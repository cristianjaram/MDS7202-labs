# Pipeline de Producción - SodAI Drinks

## Descripción General

Este proyecto implementa un pipeline automatizado end-to-end que orquesta el flujo completo de predicción de pedidos para SodAI Drinks. El sistema abarca desde la extracción inicial de datos hasta la generación de predicciones semanales, integrando componentes de MLOps como detección de data drift, reentrenamiento condicional y tracking de experimentos.

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

## Descripción de Tareas del Pipeline

### 1. Extracción de Datos (extract_data)
Esta tarea se encarga de cargar los datos fuente desde archivos en formato parquet, incluyendo información de clientes, productos y transacciones históricas. Los datos se copian al directorio de trabajo del pipeline y se genera metadata sobre la extracción realizada.

- **Entrada**: Ruta a los archivos de datos originales
- **Salida**: Archivos parquet disponibles en `data/` y metadata de extracción

### 2. Transformación de Datos (transform_data)
En esta etapa se realiza la ingeniería de features necesaria para el modelo predictivo. El proceso incluye la agregación temporal de las transacciones por semana, la generación del producto cartesiano entre clientes, productos y semanas, y la creación de variables derivadas temporales como promedios móviles y lags. Finalmente, se integran los atributos estáticos de clientes y productos.

- **Operaciones principales**:
  - Agregación semanal de transacciones
  - Generación de combinaciones cliente × producto × semana
  - Creación de features temporales: t-1, t-2, promedio de 4 semanas
  - Integración de atributos de clientes y productos
- **Salida**: Dataset transformado en `data/dataset_transformed.parquet`

### 3. Detección de Data Drift (check_drift)
Este componente implementa un sistema de monitoreo de calidad de datos que detecta cambios significativos en las distribuciones estadísticas de las features. Utiliza z-scores para comparar las estadísticas actuales (media y desviación estándar) con las históricas. Si se detectan desviaciones mayores a 2.0 en alguna variable, el sistema determina que es necesario reentrenar el modelo.

- **Método**: Comparación estadística mediante z-score
- **Umbral de decisión**: z-score > 2.0 indica data drift
- **Salida**: Decisión de flujo: `retrain_model` o `skip_retrain`

### 4. Reentrenamiento del Modelo (retrain_model)
Cuando se detecta data drift, esta tarea ejecuta el reentrenamiento completo del modelo utilizando optimización bayesiana de hiperparámetros. El proceso incluye balanceo de clases mediante SMOTE y registra todos los experimentos en MLflow para asegurar reproducibilidad y trazabilidad.

- **Componentes del proceso**:
  - Optimización de hiperparámetros con Optuna (búsqueda bayesiana)
  - Balanceo de clases con SMOTE
  - Registro de experimentos en MLflow (métricas, parámetros, artefactos)
  - Generación de gráficos SHAP para interpretabilidad del modelo
- **Salida**: Modelo entrenado guardado en `models/modelo_final.pkl`

### 5. Generación de Predicciones (generate_predictions)
La tarea final del pipeline genera predicciones para todas las combinaciones cliente-producto de la siguiente semana. Utiliza el modelo más reciente (recién entrenado o existente según el resultado del drift detection) y guarda las predicciones con sus probabilidades asociadas.

- **Entrada**: Dataset transformado y modelo entrenado
- **Salida**: Predicciones almacenadas en `data/predicciones_YYYY_MM_DD.parquet`

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

## Lógica de Reentrenamiento Condicional

El pipeline implementa una estrategia de reentrenamiento inteligente basada en la detección de data drift, lo que permite optimizar el uso de recursos computacionales mientras se mantiene la calidad del modelo:

1. **Primera ejecución**: En la ejecución inicial, el sistema siempre entrena un modelo nuevo debido a la ausencia de datos históricos de referencia.

2. **Ejecuciones posteriores**:
   - El sistema calcula las estadísticas descriptivas (media y desviación estándar) de todas las features numéricas
   - Estas estadísticas se comparan con las históricas almacenadas utilizando z-scores
   - Si alguna feature presenta un z-score > 2.0, se considera que hay drift significativo y se activa el reentrenamiento
   - Si no se detecta drift, se utiliza el modelo existente para las predicciones, ahorrando recursos

Esta aproximación permite que el modelo se mantenga actualizado solo cuando es realmente necesario, reduciendo costos computacionales sin sacrificar precisión.

## Supuestos y Consideraciones del Pipeline

Para el correcto funcionamiento del sistema, se asumen las siguientes condiciones:

1. **Estructura de datos**: Los nuevos datos de transacciones mantienen el mismo esquema que el archivo original `transacciones.parquet`
2. **Disponibilidad de datos**: Los archivos de datos están disponibles en el directorio configurado al momento de ejecución
3. **Frecuencia de ejecución**: El pipeline está diseñado para ejecutarse semanalmente, generando predicciones para la semana siguiente
4. **Horizonte de predicción**: Las predicciones generadas corresponden a la semana inmediatamente posterior a la última fecha presente en los datos

## Monitoreo y Observabilidad

El sistema cuenta con múltiples mecanismos de monitoreo y registro:

- **Logs de Airflow**: Cada tarea del pipeline genera logs detallados accesibles desde la interfaz web de Airflow, permitiendo diagnóstico de problemas y auditoría de ejecuciones
- **Archivos de métricas**: Los resultados y estadísticas se persisten en archivos JSON en el directorio `data/`:
  - `latest_prediction_summary.json`: Contiene el resumen de la última ejecución de predicciones (total de predicciones, positivas, negativas, probabilidad promedio)
  - `historical_stats.json`: Almacena las estadísticas históricas de las features para la comparación en el drift detection

Estos registros facilitan tanto la depuración como el análisis retrospectivo del comportamiento del sistema.

## Oportunidades de Mejora

Como trabajo futuro, se han identificado las siguientes mejoras potenciales:

- **Sistema de alertas**: Implementar notificaciones automáticas por email o Slack cuando se detecte drift o fallas en el pipeline
- **A/B Testing**: Desarrollar capacidad para comparar modelos en producción con versiones candidatas
- **Métricas operacionales**: Incorporar monitoreo de latencia, uso de memoria y CPU, y tiempo de ejecución de cada tarea
- **Dashboard de monitoreo**: Integrar con herramientas como Grafana para visualización en tiempo real del estado del pipeline y métricas del modelo
