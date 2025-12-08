"""
Script para ejecutar el pipeline de Airflow y extraer el CSV.
"""
import subprocess
import time
import os

def run_command(cmd, description):
    """Ejecuta un comando y muestra su salida."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0

def main():
    print("\n" + "="*60)
    print("EJECUTANDO PIPELINE DE AIRFLOW")
    print("="*60)

    # Verificar que Airflow está corriendo
    print("\n1. Verificando que Airflow está corriendo...")
    os.chdir("airflow")
    success = run_command(
        "docker-compose ps",
        "Estado de contenedores de Airflow"
    )

    if not success:
        print("\nERROR: Airflow no está corriendo.")
        print("Ejecuta: cd airflow && docker-compose up -d")
        return

    print("\n" + "="*60)
    print("INSTRUCCIONES PARA EJECUTAR EL PIPELINE")
    print("="*60)
    print("\nAbre tu navegador y ve a: http://localhost:8080")
    print("\nCredenciales:")
    print("  Usuario: airflow")
    print("  Password: airflow")
    print("\nPasos en la interfaz de Airflow:")
    print("  1. Busca el DAG 'sodai_drinks_pipeline'")
    print("  2. Click en el botón Play (▶️) a la derecha")
    print("  3. Click en 'Trigger DAG'")
    print("  4. Espera a que todas las tareas estén en verde (5-10 min)")
    print("\nEl pipeline ejecutará estas tareas:")
    print("  ✓ extract_data - Carga los datos combinados")
    print("  ✓ transform_data - Crea features")
    print("  ✓ check_drift - Detecta drift (detectará cambios con datos nuevos)")
    print("  ✓ retrain_model - Reentrenará el modelo si hay drift")
    print("  ✓ generate_predictions - Predice para 2025-01-06 a 2025-01-12")
    print("  ✓ export_csv - Genera CSV con predicciones positivas")

    print("\n" + "="*60)
    print("\nPresiona ENTER cuando el pipeline haya terminado...")
    input()

    # Extraer el CSV
    print("\n" + "="*60)
    print("EXTRAYENDO CSV DE PREDICCIONES")
    print("="*60)

    csv_dest = "c:/Users/crist/Desktop/predicciones_positivas.csv"

    success = run_command(
        f'docker cp airflow-airflow-webserver-1:/opt/airflow/data/predicciones_positivas.csv "{csv_dest}"',
        "Copiando CSV desde Airflow al escritorio"
    )

    if success:
        print(f"\n✅ CSV extraído exitosamente!")
        print(f"Ubicación: {csv_dest}")

        # Mostrar primeras líneas
        run_command(
            f'powershell -Command "Get-Content \'{csv_dest}\' | Select-Object -First 20"',
            "Primeras 20 líneas del CSV"
        )

        # Contar líneas
        run_command(
            f'powershell -Command "(Get-Content \'{csv_dest}\').Count"',
            "Total de predicciones positivas"
        )
    else:
        print("\n❌ Error al extraer el CSV")
        print("Verifica que el pipeline haya terminado correctamente")

    print("\n" + "="*60)
    print("PROCESO COMPLETADO")
    print("="*60)

if __name__ == "__main__":
    main()
