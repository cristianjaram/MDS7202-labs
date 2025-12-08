# 🚀 Guía de Instalación - Sistema de Predicción SodAI Drinks

## 📋 Requisitos Previos

### Software Necesario

1. **Docker Desktop** (OBLIGATORIO)
   - Descargar: https://www.docker.com/products/docker-desktop/
   - Versión: Windows 10/11 Pro, Enterprise o Education con WSL2
   - Tamaño: ~500 MB de descarga

2. **Python 3.8 o superior** (OBLIGATORIO)
   - Descargar: https://www.python.org/downloads/
   - Durante instalación: Marcar "Add Python to PATH"
   - Tamaño: ~30 MB

3. **Git** (Opcional)
   - Solo si quieres clonar desde repositorio
   - Descargar: https://git-scm.com/downloads

### Espacio en Disco
- Mínimo: 10 GB libres
- Recomendado: 15 GB libres

---

## 📂 Estructura del Proyecto

```
entrega2/
├── airflow/                    # Pipeline de ML con Apache Airflow
│   ├── dags/
│   │   └── pipeline_dag.py    # Definición del pipeline
│   ├── scripts/
│   │   ├── tasks.py           # Tareas del pipeline
│   │   ├── data_processing.py # Procesamiento de datos
│   │   ├── model.py           # Entrenamiento del modelo
│   │   ├── prediction.py      # Generación de predicciones
│   │   └── export_csv.py      # Exportación a CSV
│   ├── docker-compose.yml     # Configuración de Airflow
│   └── Dockerfile            # Imagen personalizada de Airflow
│
├── app/                        # Aplicación Web (FastAPI + Gradio)
│   ├── backend/
│   │   ├── main.py           # API REST con FastAPI
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── frontend/
│   │   ├── app.py            # Interfaz Gradio
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── docker-compose.yml
│
├── datos/                      # Datos del proyecto
│   ├── clientes.parquet
│   ├── productos.parquet
│   └── transacciones.parquet
│
├── combine_data.py            # Script para agregar nuevos datos
├── export_predictions_to_csv.py  # Script para exportar CSV
└── README_INSTALACION.md      # Este archivo
```

---

## 🔧 Instalación Paso a Paso

### Paso 1: Instalar Docker Desktop

1. Descargar Docker Desktop desde https://www.docker.com/products/docker-desktop/
2. Ejecutar el instalador
3. Reiniciar el PC si se solicita
4. Abrir Docker Desktop y esperar a que inicie completamente
5. Verificar instalación:
   ```bash
   docker --version
   docker-compose --version
   ```

### Paso 2: Instalar Python

1. Descargar Python desde https://www.python.org/downloads/
2. Durante instalación: **IMPORTANTE** - Marcar "Add Python to PATH"
3. Verificar instalación:
   ```bash
   python --version
   pip --version
   ```

### Paso 3: Instalar Dependencias de Python

```bash
pip install pandas pyarrow
```

### Paso 4: Copiar Archivos del Proyecto

Descomprimir el archivo ZIP en la ubicación deseada, por ejemplo:
```
C:\Users\[tu_usuario]\Desktop\MDS7202-labs\proyecto_lab\entrega2\
```

### Paso 5: Verificar Estructura de Archivos

Asegurarse de que existan las siguientes carpetas:
- `entrega2/airflow/`
- `entrega2/app/`
- `entrega1/` (con los datos)

---

## 🚀 Ejecución del Sistema

### Opción A: Ejecutar Todo (Airflow + App Web)

#### 1. Levantar Airflow

```bash
# Navegar a la carpeta de Airflow
cd C:\Users\[tu_usuario]\Desktop\MDS7202-labs\proyecto_lab\entrega2\airflow

# Primera vez: Inicializar base de datos de Airflow
docker-compose up airflow-init

# Levantar servicios
docker-compose up -d

# Verificar que estén corriendo
docker-compose ps
```

**Credenciales de Airflow:**
- URL: http://localhost:8080
- Usuario: `airflow`
- Contraseña: `airflow`

#### 2. Levantar App Web (Frontend + Backend)

```bash
# Navegar a la carpeta de la app
cd C:\Users\[tu_usuario]\Desktop\MDS7202-labs\proyecto_lab\entrega2\app

# Construir y levantar servicios
docker-compose up -d

# Verificar que estén corriendo
docker-compose ps
```

**URLs de la Aplicación:**
- Frontend Gradio: http://localhost:7860
- API Backend: http://localhost:8000
- Documentación API: http://localhost:8000/docs

---

## 📊 Ejecutar el Pipeline de ML

### Primera Ejecución (Entrenamiento Inicial)

1. Abrir navegador en http://localhost:8080
2. Iniciar sesión (airflow / airflow)
3. Buscar el DAG `sodai_drinks_pipeline`
4. Click en el botón Play (▶️) a la derecha
5. Click en "Trigger DAG"
6. Esperar 5-10 minutos a que termine

El pipeline ejecutará:
- ✅ `extract_data` - Carga datos
- ✅ `transform_data` - Crea features
- ✅ `check_drift` - Detecta drift
- ✅ `retrain_model` - Entrena el modelo
- ✅ `generate_predictions` - Genera predicciones
- ✅ `export_csv` - Crea CSV con predicciones positivas

### Agregar Nuevos Datos

Si recibes un nuevo archivo parquet con datos adicionales:

```bash
cd C:\Users\[tu_usuario]\Desktop\MDS7202-labs\proyecto_lab\entrega2

# Editar combine_data.py y actualizar la ruta NEW_DATA_PATH
# Ejemplo: NEW_DATA_PATH = '../entrega3/batch_t2.parquet'

# Ejecutar script de combinación
python combine_data.py

# Luego ejecutar el pipeline desde la web de Airflow
```

---

## 📥 Extraer Predicciones

### Obtener el CSV de Predicciones

Después de ejecutar el pipeline:

```bash
# Copiar CSV desde el contenedor de Airflow
docker cp airflow-airflow-webserver-1:/opt/airflow/data/predicciones_positivas.csv C:\Users\[tu_usuario]\Desktop\predicciones_positivas.csv

# Ver primeras líneas
powershell -Command "Get-Content 'C:\Users\[tu_usuario]\Desktop\predicciones_positivas.csv' | Select-Object -First 20"

# Contar predicciones positivas
powershell -Command "(Get-Content 'C:\Users\[tu_usuario]\Desktop\predicciones_positivas.csv').Count"
```

**Formato del CSV:**
```
25734,56714
25734,72891
61353,11262
...
```
- Sin headers
- Columna 1: ID del cliente (empresa)
- Columna 2: ID del producto
- Solo predicciones positivas (prediction = 1)

---

## 🔍 Comandos Útiles

### Verificar Estado de Contenedores

```bash
# Airflow
cd airflow
docker-compose ps

# App
cd app
docker-compose ps
```

### Ver Logs

```bash
# Logs de Airflow scheduler
docker logs airflow-airflow-scheduler-1 -f

# Logs del backend
docker logs sodai-backend -f

# Logs del frontend
docker logs sodai-frontend -f
```

### Reiniciar Servicios

```bash
# Reiniciar Airflow
cd airflow
docker-compose restart

# Reiniciar App
cd app
docker-compose restart
```

### Detener Servicios

```bash
# Detener Airflow
cd airflow
docker-compose down

# Detener App
cd app
docker-compose down
```

### Reconstruir Contenedores (si hay cambios en código)

```bash
# Airflow
cd airflow
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# App
cd app
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## ⚠️ Solución de Problemas

### Docker Desktop no inicia
- Verificar que la virtualización esté habilitada en BIOS
- Verificar que WSL2 esté instalado: `wsl --install`
- Reiniciar Windows

### Airflow no inicia
```bash
cd airflow
docker-compose down
docker volume prune  # CUIDADO: Borra volúmenes
docker-compose up airflow-init
docker-compose up -d
```

### Error "port already allocated"
- Verificar que los puertos 8080, 8000, 7860 no estén en uso
- Cerrar otras aplicaciones que puedan usar esos puertos

### Modelo no se carga en el Backend
```bash
# Verificar que existe el modelo
docker exec airflow-airflow-webserver-1 ls -la /opt/airflow/models/

# Si no existe, ejecutar el pipeline en Airflow primero
```

### CSV no se genera
```bash
# Verificar que el pipeline terminó correctamente en Airflow
# Verificar logs de la tarea export_csv
docker logs airflow-airflow-scheduler-1 2>&1 | findstr "export_csv"
```

---

## 📞 Contacto y Soporte

Para problemas o dudas:
1. Verificar logs de Docker: `docker-compose logs`
2. Revisar la interfaz de Airflow para errores en tareas
3. Consultar documentación oficial de Docker y Airflow

---

## 📝 Notas Adicionales

### Archivos Generados Automáticamente (NO copiar)
- `airflow/logs/`
- `airflow/mlruns/`
- `airflow/data/` (excepto los parquets base)
- `airflow/models/`
- `__pycache__/`

### Recursos del Sistema
- RAM recomendada: 8 GB mínimo
- CPU: 4 cores recomendados
- Tiempo de ejecución del pipeline: 5-10 minutos

### Persistencia de Datos
- Los datos se mantienen en volúmenes de Docker
- Al ejecutar `docker-compose down` los datos NO se pierden
- Para borrar todo: `docker-compose down -v` (⚠️ borra volúmenes)

---

## ✅ Checklist de Instalación Exitosa

- [ ] Docker Desktop instalado y corriendo
- [ ] Python 3.8+ instalado
- [ ] Pandas instalado (`pip install pandas pyarrow`)
- [ ] Archivos del proyecto descomprimidos
- [ ] Airflow corriendo (http://localhost:8080 accesible)
- [ ] App corriendo (http://localhost:7860 accesible)
- [ ] Pipeline ejecutado exitosamente
- [ ] CSV de predicciones extraído

**¡Sistema listo para usar!** 🎉
