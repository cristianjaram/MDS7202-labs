# Entrega 2 - Pipeline MLOps para SodAI Drinks

Sistema completo de predicción de pedidos con pipeline automatizado, detección de drift, y aplicación web interactiva.

## 📋 Estructura del Proyecto

```
entrega2/
├── airflow/                    # Pipeline de datos y entrenamiento
│   ├── dags/                   # Definición del DAG de Airflow
│   ├── scripts/                # Módulos Python del pipeline
│   ├── data/                   # Datos procesados y predicciones
│   ├── models/                 # Modelos entrenados
│   ├── docker-compose.yaml     # Configuración de Airflow
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md               # Documentación del pipeline
│
├── app/                        # Aplicación web de predicciones
│   ├── backend/                # API REST con FastAPI
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── frontend/               # Interfaz Gradio
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── docker-compose.yml      # Configuración de la app
│
├── entrega2.ipynb              # Notebook principal con análisis
├── conclusiones.md             # Conclusiones y reflexiones
└── README.md                   # Este archivo
```

## 🚀 Requisitos Previos

- **Docker Desktop** instalado y corriendo
- **Docker Compose** (incluido en Docker Desktop)
- Al menos **8GB de RAM** disponible
- **20GB de espacio en disco**
- **Datos originales** de la Entrega 1:
  - `clientes.parquet`
  - `productos.parquet`
  - `transacciones.parquet`

## 📦 Archivos Necesarios para Reproducibilidad

### Archivos Esenciales (DEBEN incluirse)

```
entrega2/
├── airflow/
│   ├── dags/pipeline_dag.py                    # Definición del DAG
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── config.py                           # Configuración
│   │   ├── data_processing.py                  # Procesamiento de datos
│   │   ├── model.py                            # Funciones del modelo
│   │   ├── prediction.py                       # Generación de predicciones
│   │   └── tasks.py                            # Tareas de Airflow
│   ├── docker-compose.yaml
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── app/
│   ├── backend/
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── frontend/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── docker-compose.yml
│
├── entrega2.ipynb
├── conclusiones.md
└── README.md
```

### Archivos Opcionales (Útiles pero regenerables)

Estos archivos se generan automáticamente al ejecutar el pipeline:

```
├── airflow/
│   ├── data/                                   # Se regenera al ejecutar
│   │   ├── clientes.parquet
│   │   ├── productos.parquet
│   │   ├── transacciones.parquet
│   │   ├── dataset_transformed.parquet
│   │   ├── predicciones_*.parquet
│   │   ├── historical_stats.json
│   │   └── latest_prediction_summary.json
│   └── models/                                 # Se regenera al entrenar
│       ├── modelo_final.pkl
│       └── model_info.json
```

### Archivos que NO deben compartirse

```
├── airflow/
│   ├── logs/                                   # Logs de ejecución local
│   └── mlruns/                                 # Experimentos de MLflow local
├── .env                                        # Variables de entorno locales
└── **/__pycache__/                             # Cache de Python
```

## 🔧 Instrucciones de Instalación

### Paso 1: Preparar el entorno

1. Clonar o descargar todos los archivos esenciales manteniendo la estructura de carpetas
2. Colocar los datos originales (`clientes.parquet`, `productos.parquet`, `transacciones.parquet`) en una carpeta temporal (ej: `../entrega1/`)

### Paso 2: Configurar Airflow

```bash
cd airflow

# Crear carpetas necesarias
mkdir -p logs plugins data models mlruns

# Iniciar servicios de Airflow
docker-compose up -d

# Esperar ~2-3 minutos para la inicialización
# Verificar que todos los contenedores estén corriendo
docker-compose ps
```

### Paso 3: Ejecutar el Pipeline

1. Acceder a la interfaz de Airflow: http://localhost:8080
   - Usuario: `airflow`
   - Contraseña: `airflow`

2. Buscar el DAG `sodai_drinks_pipeline`
3. Activar el DAG (toggle ON)
4. Ejecutar manualmente con "Trigger DAG"
5. Monitorear la ejecución (toma ~10-15 minutos la primera vez)

El pipeline:
- Extrae los datos originales
- Transforma y crea features
- Detecta drift (en primera ejecución siempre entrena)
- Entrena el modelo con optimización Optuna
- Genera predicciones para la próxima semana

### Paso 4: Lanzar la Aplicación Web

```bash
cd ../app

# Iniciar backend y frontend
docker-compose up -d

# Verificar que los contenedores estén corriendo
docker-compose ps
```

Acceder a:
- **Frontend (Gradio)**: http://localhost:7860
- **API Backend (FastAPI)**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 📊 Uso de la Aplicación

### Frontend Gradio

1. Seleccionar un cliente del dropdown
2. Automáticamente se cargan los productos que ha comprado
3. Seleccionar un producto
4. Click en "Predecir" para ver la probabilidad de compra

### API REST

Ejemplos de uso:

```bash
# Health check
curl http://localhost:8000/health

# Obtener clientes disponibles
curl http://localhost:8000/customers

# Obtener productos de un cliente
curl http://localhost:8000/customers/61353/products

# Obtener predicción
curl http://localhost:8000/predict/customer/61353/product/56714

# Top predicciones
curl http://localhost:8000/predictions/top/100
```

## 🔄 Actualizaciones de Datos

Para ejecutar el pipeline con nuevos datos:

1. Colocar los nuevos archivos parquet en la carpeta de datos
2. En Airflow, ejecutar nuevamente el DAG
3. El sistema detectará automáticamente si hay drift
4. Si hay drift, reentrenará el modelo
5. Generará nuevas predicciones
6. El backend las cargará automáticamente

## 🐛 Troubleshooting

### Problema: Contenedores no inician

```bash
# Verificar logs
docker-compose logs

# Reiniciar servicios
docker-compose down
docker-compose up -d
```

### Problema: Modelo no se carga en el backend

```bash
# Verificar que el modelo existe
ls airflow/models/

# Verificar logs del backend
docker logs sodai-backend

# Reconstruir contenedor
cd app
docker-compose up --build -d backend
```

### Problema: Frontend no carga clientes

```bash
# Verificar conectividad backend
curl http://localhost:8000/health

# Verificar datos disponibles
curl http://localhost:8000/customers

# Reiniciar frontend
docker restart sodai-frontend
```

## 📝 Notas Importantes

1. **Primera ejecución**: El pipeline toma ~10-15 minutos en la primera corrida debido al entrenamiento con Optuna
2. **Memoria**: Asegurarse de tener suficiente RAM disponible (mínimo 8GB)
3. **Puertos**: Los puertos 8080, 8000 y 7860 deben estar libres
4. **Datos**: Los datos originales NO se incluyen en el repositorio por tamaño, deben proporcionarse por separado

## 🔗 Componentes Tecnológicos

- **Orquestación**: Apache Airflow
- **Modelo**: LightGBM con SMOTE
- **Optimización**: Optuna (búsqueda bayesiana)
- **Tracking**: MLflow
- **Backend**: FastAPI
- **Frontend**: Gradio
- **Containerización**: Docker & Docker Compose

## 📚 Documentación Adicional

- Ver `airflow/README.md` para detalles del pipeline
- Ver `conclusiones.md` para análisis y reflexiones
- Ver `entrega2.ipynb` para desarrollo y experimentación

## 👥 Créditos

Proyecto desarrollado como parte del curso MDS7202 - MLOps
