# base de Python
FROM python:3.12-slim

# directorio de trabajo dentro del contenedor
WORKDIR /app

# copiar archivos necesarios al contenedor
COPY requirements.txt .

# dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar resto de proyecto
COPY . .

# puerto donde corre la API
EXPOSE 8000

# Comando por defecto para levantar el servidor FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
