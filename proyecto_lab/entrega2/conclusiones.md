# Conclusiones - Entrega 2: MLOps Pipeline

## 1. Resumen del Proyecto

Se implementó un pipeline MLOps completo para el sistema de predicción de pedidos de SodAI Drinks, incluyendo:

- **Pipeline de datos automatizado** con Apache Airflow
- **Tracking de experimentos** con MLflow
- **Detección de data drift** para reentrenamiento condicional
- **API REST** con FastAPI
- **Interfaz de usuario** con Gradio
- **Containerización** completa con Docker

## 2. Modelo de Machine Learning

### Algoritmo
- **LightGBM** con balanceo de clases mediante SMOTE
- Optimización de hiperparámetros con **Optuna** (25 trials)

### Métricas obtenidas
- **F1-Score**: 0.8646
- **ROC-AUC**: 0.9695
- **PR-AUC**: 0.9222
- **Precision**: 0.8315
- **Recall**: 0.9003

### Hiperparámetros óptimos
- learning_rate: 0.0178
- n_estimators: 238
- num_leaves: 203
- max_depth: 11
- min_child_samples: 7
- feature_fraction: 0.6496

## 3. Pipeline de Airflow

### Tareas implementadas
1. **extract_data**: Carga los datos desde archivos parquet
2. **transform_data**: Ingeniería de features (lags, promedios, agregaciones)
3. **check_drift**: Detecta data drift comparando distribuciones con z-score
4. **retrain_model**: Reentrena el modelo si se detecta drift (Branch)
5. **generate_predictions**: Genera predicciones para la siguiente semana

### Flujo condicional
El DAG utiliza `BranchPythonOperator` para decidir si reentrenar basándose en la detección de drift, optimizando recursos cuando los datos son estables.

## 4. Integración con MLflow

### Elementos registrados
- **Parámetros**: Hiperparámetros del modelo, umbrales, configuración
- **Métricas**: F1, Precision, Recall, ROC-AUC, PR-AUC, Accuracy
- **Artefactos**: Modelo pkl, SHAP plots, matriz de confusión

### Beneficios
- Trazabilidad completa de experimentos
- Comparación histórica de modelos
- Reproducibilidad de resultados

## 5. Aplicación Web

### Backend (FastAPI)
- Endpoint `/predict`: Predicción individual
- Endpoint `/predict/batch`: Predicciones en lote
- Endpoint `/health`: Estado del servicio
- Endpoint `/model/info`: Información del modelo

### Frontend (Gradio)
- Interfaz intuitiva para ingresar datos
- Visualización clara de resultados con probabilidades
- Verificación de conexión con el backend

## 6. Dockerización

### Componentes containerizados
- **Airflow**: Scheduler, Webserver, Workers
- **PostgreSQL**: Base de datos de Airflow
- **Backend**: FastAPI con modelo cargado
- **Frontend**: Gradio

### Volúmenes compartidos
- Modelos entrenados accesibles entre Airflow y la aplicación
- DAGs y scripts montados para desarrollo

## 7. Lecciones Aprendidas

### Desafíos técnicos
1. **Compatibilidad de dependencias**: NumPy/Pandas requieren versiones específicas
2. **Librerías de sistema**: LightGBM necesita libgomp1
3. **Rutas en Docker**: Mapeo correcto de volúmenes entre host y containers

### Buenas prácticas aplicadas
- Código modular y reutilizable
- Configuración mediante variables de entorno
- Health checks para monitoreo
- Logging estructurado

## 8. Próximos Pasos

### Mejoras potenciales
1. **Monitoreo en producción**: Prometheus + Grafana
2. **CI/CD**: GitHub Actions para despliegue automático
3. **Feature Store**: Centralizar gestión de features
4. **A/B Testing**: Comparar modelos en producción
5. **Alertas**: Notificaciones automáticas de drift o errores

### Escalabilidad
- Kubernetes para orquestación de containers
- Celery Executor para tareas distribuidas
- Cache de predicciones frecuentes

## 9. Conclusión Final

Se logró implementar un sistema MLOps end-to-end que automatiza todo el ciclo de vida del modelo de machine learning, desde la ingesta de datos hasta el serving de predicciones. El pipeline permite:

- **Automatización**: Reentrenamiento periódico sin intervención manual
- **Reproducibilidad**: Tracking completo de experimentos con MLflow
- **Mantenibilidad**: Código modular y containerizado
- **Escalabilidad**: Arquitectura preparada para crecimiento

El modelo alcanza un F1-Score de 0.8646, demostrando buen balance entre precisión y recall para predecir qué clientes comprarán productos la próxima semana.
