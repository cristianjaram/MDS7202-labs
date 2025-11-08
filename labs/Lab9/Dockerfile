FROM apache/airflow:2.7.3-python3.10

# Cambiar a usuario root para instalar dependencias
USER root

# Instalar curl y otras dependencias del sistema
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Cambiar de vuelta al usuario airflow
USER airflow

# Instalar paquetes Python adicionales
RUN pip install --no-cache-dir \
    scikit-learn==1.3.2 \
    joblib==1.3.2 \
    gradio==3.50.2

# Copiar los archivos DAG
COPY --chown=airflow:root dags/ /opt/airflow/dags/

# Configurar variables de entorno
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__CORE__EXECUTOR=SequentialExecutor
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db