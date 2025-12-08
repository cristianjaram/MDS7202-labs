"""
Script para crear un paquete ZIP con todos los archivos necesarios del proyecto.
"""
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 60)
    print("CREANDO PAQUETE DE DISTRIBUCIÓN")
    print("=" * 60)

    # Configuración
    project_root = Path(__file__).parent
    output_name = f"sodai_drinks_mlops_{datetime.now().strftime('%Y%m%d')}"
    output_dir = project_root / output_name
    zip_path = project_root.parent.parent.parent / f"{output_name}.zip"

    print(f"\n📦 Creando paquete: {output_name}")
    print(f"📍 Ubicación ZIP: {zip_path}")

    # Crear directorio temporal
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n1️⃣  Copiando archivos de Airflow...")
    airflow_src = project_root / "airflow"
    airflow_dst = output_dir / "airflow"

    # Copiar Airflow (excluyendo logs, cache, etc.)
    shutil.copytree(
        airflow_src,
        airflow_dst,
        ignore=shutil.ignore_patterns(
            '__pycache__', '*.pyc', '*.pyo',
            'logs', 'mlruns', 'data',
            '.pytest_cache', '.env'
        )
    )

    # Crear carpetas vacías necesarias
    (airflow_dst / "logs").mkdir(exist_ok=True)
    (airflow_dst / "data").mkdir(exist_ok=True)
    (airflow_dst / "models").mkdir(exist_ok=True)
    (airflow_dst / "mlruns").mkdir(exist_ok=True)

    print(f"   ✅ Airflow copiado")

    print("\n2️⃣  Copiando aplicación web...")
    app_src = project_root / "app"
    app_dst = output_dir / "app"

    shutil.copytree(
        app_src,
        app_dst,
        ignore=shutil.ignore_patterns(
            '__pycache__', '*.pyc', '*.pyo',
            '.pytest_cache', '.env'
        )
    )
    print(f"   ✅ App copiada")

    print("\n3️⃣  Copiando datos...")
    datos_src = project_root.parent / "entrega1"
    datos_dst = output_dir / "datos"
    datos_dst.mkdir()

    # Copiar solo los parquets necesarios
    archivos_datos = ['clientes.parquet', 'productos.parquet', 'transacciones.parquet']
    for archivo in archivos_datos:
        src_file = datos_src / archivo
        if src_file.exists():
            shutil.copy2(src_file, datos_dst / archivo)
            size_mb = src_file.stat().st_size / (1024 * 1024)
            print(f"   ✅ {archivo} ({size_mb:.1f} MB)")
        else:
            print(f"   ⚠️  {archivo} no encontrado")

    print("\n4️⃣  Copiando scripts auxiliares...")
    scripts = [
        'combine_data.py',
        'export_predictions_to_csv.py',
        'README_INSTALACION.md'
    ]
    for script in scripts:
        src = project_root / script
        if src.exists():
            shutil.copy2(src, output_dir / script)
            print(f"   ✅ {script}")

    print("\n5️⃣  Creando archivos de configuración...")

    # Crear .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*.so
.Python
env/
venv/
*.egg-info/

# Airflow
airflow/logs/
airflow/mlruns/
airflow/data/*.parquet
airflow/data/*.csv
airflow/data/*.json
airflow/models/*.pkl
airflow/models/*.json

# Docker
.env

# OS
.DS_Store
Thumbs.db
"""
    with open(output_dir / ".gitignore", "w") as f:
        f.write(gitignore_content)
    print(f"   ✅ .gitignore")

    # Crear archivo de requisitos
    requirements_content = """# Requisitos para scripts auxiliares
pandas>=1.5.0
pyarrow>=10.0.0
"""
    with open(output_dir / "requirements.txt", "w") as f:
        f.write(requirements_content)
    print(f"   ✅ requirements.txt")

    # Crear script de inicio rápido
    quickstart_content = """@echo off
echo ====================================
echo SODAI DRINKS - INICIO RAPIDO
echo ====================================
echo.

echo Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker no esta instalado
    echo Por favor instala Docker Desktop primero
    pause
    exit /b 1
)

echo Docker OK!
echo.

echo [1/2] Iniciando Airflow...
cd airflow
docker-compose up -d
cd ..

echo [2/2] Iniciando App...
cd app
docker-compose up -d
cd ..

echo.
echo ====================================
echo SISTEMA INICIADO!
echo ====================================
echo.
echo URLs disponibles:
echo - Airflow: http://localhost:8080 (airflow / airflow)
echo - Gradio:  http://localhost:7860
echo - API:     http://localhost:8000/docs
echo.

pause
"""
    with open(output_dir / "INICIO_RAPIDO.bat", "w") as f:
        f.write(quickstart_content)
    print(f"   ✅ INICIO_RAPIDO.bat")

    print("\n6️⃣  Creando archivo ZIP...")

    # Crear ZIP
    shutil.make_archive(
        str(zip_path.with_suffix('')),
        'zip',
        output_dir.parent,
        output_dir.name
    )

    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"   ✅ ZIP creado: {zip_size_mb:.1f} MB")

    print("\n7️⃣  Limpiando archivos temporales...")
    shutil.rmtree(output_dir)
    print(f"   ✅ Carpeta temporal eliminada")

    print("\n" + "=" * 60)
    print("✅ PAQUETE CREADO EXITOSAMENTE")
    print("=" * 60)
    print(f"\n📦 Archivo: {zip_path}")
    print(f"📊 Tamaño: {zip_size_mb:.1f} MB")
    print(f"\n📋 Contenido del paquete:")
    print(f"   - Airflow (pipeline completo)")
    print(f"   - App (frontend + backend)")
    print(f"   - Datos (clientes, productos, transacciones)")
    print(f"   - Scripts auxiliares")
    print(f"   - README de instalación")
    print(f"   - Script de inicio rápido")
    print(f"\n💡 Para usar:")
    print(f"   1. Descomprimir el ZIP")
    print(f"   2. Leer README_INSTALACION.md")
    print(f"   3. Ejecutar INICIO_RAPIDO.bat (Windows)")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
