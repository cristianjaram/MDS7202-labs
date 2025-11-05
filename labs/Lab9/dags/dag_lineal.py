# dags/dag_lineal.py
from datetime import datetime
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator  

from hiring_functions import create_folders, split_data, preprocess_and_train, gradio_interface


DEFAULT_ARGS = {
    'owner': 'estudiante',
}

with DAG(
    dag_id='hiring_lineal',
    default_args=DEFAULT_ARGS,
    start_date=datetime(2024, 10, 1),
    schedule_interval=None,  
    catchup=False,            
    max_active_runs=1,
    tags=['laboratorio', 'airflow', 'hiring'],
) as dag:

    start = EmptyOperator(task_id='start')

   
    t_create_folders = PythonOperator(
        task_id='create_folders',
        python_callable=create_folders,
        provide_context=True,  
    )

   
    
    from airflow.operators.bash import BashOperator
    
    # Tarea para descargar data_1.csv
    download_data = BashOperator(
    task_id='download_data',
    bash_command="""
    mkdir -p /opt/airflow/data/{{ ds }}/raw/ && 
    curl -L -o /opt/airflow/data/{{ ds }}/raw/data_1.csv https://gitlab.com/eduardomoyab/laboratorio-13/-/raw/main/files/data_1.csv &&
    ls -la /opt/airflow/data/{{ ds }}/raw/
    """,
    dag=dag
)



   
    t_split = PythonOperator(
        task_id='split_data',
        python_callable=split_data,
        op_kwargs={
            # Template: extrae el base_path devuelto por create_folders
            'base_path': "{{ ti.xcom_pull(task_ids='create_folders') }}",
            'random_state': 42
        },
    )

    t_train = PythonOperator(
        task_id='preprocess_and_train',
        python_callable=preprocess_and_train,
        op_kwargs={
            'base_path': "{{ ti.xcom_pull(task_ids='create_folders') }}"
        }
    )

    t_gradio = PythonOperator(
        task_id='launch_gradio',
        python_callable=lambda **kwargs: gradio_interface(
            model_path=kwargs['ti'].xcom_pull(task_ids='preprocess_and_train')
        ),
        provide_context=True,
    )

    start >> t_create_folders >> download_data >> t_split >> t_train >> t_gradio