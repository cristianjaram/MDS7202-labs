from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
import sys
import os

dag_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, dag_folder)

from scripts.tasks import (
    extract_data,
    transform_data,
    detect_drift,
    retrain_model,
    generate_predictions_task,
    export_predictions_csv
)

default_args = {
    'owner': 'deep_drinkers',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'sodai_drinks_pipeline',
    default_args=default_args,
    description='Pipeline de predicción de pedidos para SodAI Drinks',
    schedule_interval=timedelta(weeks=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mlops', 'prediction', 'sodai'],
) as dag:

    start = EmptyOperator(task_id='start')

    extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
        op_kwargs={'data_path': '/opt/airflow/entrega1'},
    )

    transform = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
    )

    check_drift = BranchPythonOperator(
        task_id='check_drift',
        python_callable=detect_drift,
    )

    retrain = PythonOperator(
        task_id='retrain_model',
        python_callable=retrain_model,
        op_kwargs={'n_trials': 25},
    )

    skip_retrain = EmptyOperator(task_id='skip_retrain')

    join = EmptyOperator(
        task_id='join',
        trigger_rule='none_failed_min_one_success'
    )

    predict = PythonOperator(
        task_id='generate_predictions',
        python_callable=generate_predictions_task,
    )

    export_csv = PythonOperator(
        task_id='export_csv',
        python_callable=export_predictions_csv,
    )

    end = EmptyOperator(task_id='end')

    start >> extract >> transform >> check_drift
    check_drift >> [retrain, skip_retrain]
    [retrain, skip_retrain] >> join >> predict >> export_csv >> end
