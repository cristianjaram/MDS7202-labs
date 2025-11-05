from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.utils.trigger_rule import TriggerRule
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
import os

# Importar nuestras funciones
from hiring_dynamic_functions import (
    create_folders, 
    load_and_merge, 
    split_data, 
    train_model, 
    evaluate_models
)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Definir el DAG
dag = DAG(
    'hiring_dynamic_pipeline',
    default_args=default_args,
    description='Pipeline dinámico para entrenamiento de modelos de contratación',
    schedule_interval=None,  
    catchup=False,  
    tags=['hiring', 'ml', 'dynamic'],
)

# Función para decidir qué archivos descargar
def decide_download_strategy(**kwargs):
    """
    Decide qué archivos descargar basado en la fecha de ejecución
    """
    execution_date = kwargs['ds']
    execution_dt = datetime.strptime(execution_date, '%Y-%m-%d')
    
    # Si es antes del 1 de noviembre de 2024, solo descarga data_1
    if execution_dt < datetime(2024, 11, 1):
        print(f"Fecha {execution_date}: Descargando solo data_1.csv")
        return 'download_data_1'
    else:
        print(f"Fecha {execution_date}: Descargando data_1.csv y data_2.csv")
        return 'download_both_files'  # Cambiar a una sola tarea

# Funciones wrapper para entrenar modelos específicos
def train_random_forest(**kwargs):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    train_model(model, 'RandomForest', **kwargs)

def train_logistic_regression(**kwargs):
    model = LogisticRegression(random_state=42, max_iter=1000)
    train_model(model, 'LogisticRegression', **kwargs)

def train_svm(**kwargs):
    model = SVC(random_state=42, probability=True)
    train_model(model, 'SVM', **kwargs)

# Función para descargar ambos archivos cuando sea necesario
def download_both_files(**kwargs):
    """Descarga ambos archivos cuando la fecha es >= Nov 1, 2024"""
    ds = kwargs['ds']
    
    # Crear directorios si no existen
    os.makedirs(f'/tmp/{ds}/raw', exist_ok=True)
    
    # Descargar data_1.csv
    import subprocess
    result1 = subprocess.run([
        'curl', '-o', f'/tmp/{ds}/raw/data_1.csv',
        'https://gitlab.com/eduardomoyab/laboratorio-13/-/raw/main/files/data_1.csv'
    ], capture_output=True, text=True)
    
    # Descargar data_2.csv
    result2 = subprocess.run([
        'curl', '-o', f'/tmp/{ds}/raw/data_2.csv',
        'https://gitlab.com/eduardomoyab/laboratorio-13/-/raw/main/files/data_2.csv'
    ], capture_output=True, text=True)
    
    print(f"Descarga data_1: {result1.returncode}")
    print(f"Descarga data_2: {result2.returncode}")


start_task = DummyOperator(
    task_id='start_pipeline',
    dag=dag,
)


create_folders_task = PythonOperator(
    task_id='create_folders',
    python_callable=create_folders,
    dag=dag,
)


branch_download = BranchPythonOperator(
    task_id='branch_download_strategy',
    python_callable=decide_download_strategy,
    dag=dag,
)


download_data_1 = BashOperator(
    task_id='download_data_1',
    bash_command='mkdir -p /tmp/{{ ds }}/raw && curl -o /tmp/{{ ds }}/raw/data_1.csv https://gitlab.com/eduardomoyab/laboratorio-13/-/raw/main/files/data_1.csv',
    dag=dag,
)


download_both_task = PythonOperator(
    task_id='download_both_files',
    python_callable=download_both_files,
    dag=dag,
)


merge_data_task = PythonOperator(
    task_id='load_and_merge_data',
    python_callable=load_and_merge,
    trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,  # Mejor trigger rule
    dag=dag,
)

split_data_task = PythonOperator(
    task_id='split_data',
    python_callable=split_data,
    dag=dag,
)

train_rf_task = PythonOperator(
    task_id='train_random_forest',
    python_callable=train_random_forest,
    dag=dag,
)

train_lr_task = PythonOperator(
    task_id='train_logistic_regression',
    python_callable=train_logistic_regression,
    dag=dag,
)

train_svm_task = PythonOperator(
    task_id='train_svm',
    python_callable=train_svm,
    dag=dag,
)

evaluate_task = PythonOperator(
    task_id='evaluate_models',
    python_callable=evaluate_models,
    trigger_rule=TriggerRule.ALL_SUCCESS,
    dag=dag,
)

end_task = DummyOperator(
    task_id='end_pipeline',
    dag=dag,
)

start_task >> create_folders_task >> branch_download

branch_download >> download_data_1
branch_download >> download_both_task

[download_data_1, download_both_task] >> merge_data_task

merge_data_task >> split_data_task


split_data_task >> [train_rf_task, train_lr_task, train_svm_task]

[train_rf_task, train_lr_task, train_svm_task] >> evaluate_task

evaluate_task >> end_task