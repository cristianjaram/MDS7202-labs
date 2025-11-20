# Pipeline Productivo - SodAI Drinks

## Descripción General

Este pipeline automatizado orquesta el flujo completo de predicción de pedidos para SodAI Drinks, desde la extracción de datos hasta la generación de predicciones semanales.

## Arquitectura del Pipeline

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  START  │ ──► │   EXTRACT   │ ──► │  TRANSFORM  │ ──► │  CHECK_DRIFT │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬───────┘
                                                               │
                                          ┌────────────────────┼────────────────────┐
                                          │                    │                    │
                                          ▼                    │                    ▼
                                   ┌─────────────┐             │           ┌──────────────┐
                                   │   RETRAIN   │             │           │ SKIP_RETRAIN │
                                   └──────┬──────┘             │           └──────┬───────┘
                                          │                    │                  │
                                          └────────────────────┼──────────────────┘
                                                               │
                                                               ▼
                                                        ┌─────────────┐
                                                        │    JOIN     │
                                                        └──────┬──────┘
                                                               │
                                                               ▼
                                                     ┌──────────────────┐
                                                     │    PREDICTIONS   │
                                                     └────────┬─────────┘
                                                              │
                                                              ▼
                                                        ┌─────────┐
                                                        │   END   │
                                                        └─────────┘
```

## Descripción de Tareas

### 1. extract_data
- **Función**: Carga los datos desde archivos parquet (clientes, productos, transacciones)
- **Input**: Ruta a los archivos de datos
- **Output**: Archivos parquet copiados a `data/` y metadata de extracción

### 2. transform_data
- **Función**: Procesa los datos y crea features
- **Operaciones**:
  - Agregación semanal de transacciones
  - Creación de producto cartesiano (cliente x producto x semana)
  - Features de lag temporal (t-1, t-2, promedio 4 semanas)
  - Merge con atributos de clientes y productos
- **Output**: Dataset transformado en `data/dataset_transformed.parquet`

### 3. check_drift (Detección de Drift)
- **Función**: Detecta cambios significativos en las distribuciones de datos
- **Método**: Comparación de estadísticas (media, std) con datos históricos usando z-score
- **Umbral**: z-score > 2.0 indica drift
- **Output**: Decide si reentrenar (`retrain_model`) o saltar (`skip_retrain`)

### 4. retrain_model
- **Función**: Reentrena el modelo con optimización de hiperparámetros
- **Componentes**:
  - Optimización con Optuna
  - SMOTE para balanceo de clases
  - Tracking con MLflow (métricas, parámetros, artefactos)
  - Gráficos SHAP para interpretabilidad
- **Output**: Modelo guardado en `models/modelo_final.pkl`

### 5. generate_predictions
- **Función**: Genera predicciones para la próxima semana
- **Input**: Datos transformados y modelo entrenado
- **Output**: Predicciones en `data/predicciones_YYYY_MM_DD.parquet`

## Estructura de Archivos

```
airflow/
├── dags/
│   └── pipeline_dag.py          # Definición del DAG
├── scripts/
│   ├── __init__.py
│   ├── config.py                # Configuración global
│   ├── data_processing.py       # Funciones de procesamiento
│   ├── model.py                 # Funciones del modelo
│   ├── prediction.py            # Funciones de predicción
│   └── tasks.py                 # Tareas de Airflow
├── data/                        # Datos procesados y predicciones
├── models/                      # Modelos entrenados
├── logs/                        # Logs de Airflow
├── mlruns/                      # Tracking de MLflow
├── docker-compose.yaml          # Configuración de Docker
├── requirements.txt             # Dependencias
├── .env                         # Variables de entorno
└── README.md                    # Esta documentación
```

## Ejecución del Pipeline

### Requisitos Previos
- Docker y Docker Compose instalados
- Datos en `../entrega1/` (clientes.parquet, productos.parquet, transacciones.parquet)

### Iniciar Airflow

```bash
cd airflow

# Crear carpetas necesarias
mkdir -p logs plugins data models

# Iniciar servicios
docker-compose up -d

# Esperar inicialización (primera vez toma ~2-3 minutos)
docker-compose logs -f airflow-init
```

### Acceder a la Interfaz Web

- **URL**: http://localhost:8080
- **Usuario**: airflow
- **Contraseña**: airflow

### Ejecutar el Pipeline

1. Acceder a la interfaz web de Airflow
2. Buscar el DAG `sodai_drinks_pipeline`
3. Activar el DAG (toggle ON)
4. Ejecutar manualmente con el botón "Trigger DAG"

### Detener Airflow

```bash
docker-compose down
```

## Integración con MLflow

El pipeline utiliza MLflow para tracking de experimentos:

- **Métricas registradas**: F1-weighted, F1-clase1, ROC-AUC, PR-AUC
- **Parámetros**: Todos los hiperparámetros del modelo
- **Artefactos**: Modelo serializado, gráficos SHAP

Para visualizar los experimentos:

```bash
# Dentro del contenedor o con MLflow instalado localmente
mlflow ui --backend-store-uri file://./mlruns
```

## Lógica de Reentrenamiento

El pipeline implementa reentrenamiento condicional basado en detección de drift:

1. **Primera ejecución**: Siempre reentrena (no hay datos históricos)
2. **Ejecuciones posteriores**:
   - Calcula estadísticas de las features numéricas
   - Compara con estadísticas históricas usando z-score
   - Si z-score > 2.0 en alguna feature → Reentrenar
   - Si no hay drift → Usar modelo existente

## Supuestos del Pipeline

1. Los nuevos datos mantienen la misma estructura que `transacciones.parquet`
2. Los archivos de datos aparecen en el directorio configurado
3. El modelo se reentrena semanalmente si hay drift o periódicamente
4. Las predicciones son para la semana siguiente a la última fecha en los datos

## Monitoreo y Logs

- Los logs de cada tarea están disponibles en la interfaz de Airflow
- Los resultados se guardan en archivos JSON en `data/`:
  - `latest_prediction_summary.json`: Resumen de última predicción
  - `historical_stats.json`: Estadísticas históricas para detección de drift

## Mejoras Futuras

- Agregar alertas por email cuando se detecte drift
- Implementar A/B testing de modelos
- Añadir más métricas de monitoreo (latencia, uso de recursos)
- Crear dashboard de monitoreo con Grafana
