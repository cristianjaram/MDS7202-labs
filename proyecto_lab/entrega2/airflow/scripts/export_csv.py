import pandas as pd
import glob
import os
from pathlib import Path

def export_positive_predictions_to_csv(
    predictions_dir: str = '/opt/airflow/data',
    output_path: str = '/opt/airflow/data/predicciones_positivas.csv'
):
    """
    Exporta predicciones positivas a CSV sin headers.

    Args:
        predictions_dir: Directorio donde se encuentran los archivos de predicciones
        output_path: Ruta del archivo CSV de salida

    Returns:
        str: Ruta del archivo CSV generado
    """
    # Buscar el archivo de predicciones más reciente
    pattern = os.path.join(predictions_dir, 'predicciones_*.parquet')
    prediction_files = glob.glob(pattern)

    if not prediction_files:
        raise FileNotFoundError(f"No se encontraron archivos de predicciones en {predictions_dir}")

    # Usar el archivo más reciente
    latest_file = max(prediction_files, key=os.path.getctime)
    print(f"Cargando predicciones desde: {latest_file}")

    # Cargar predicciones
    predictions = pd.read_parquet(latest_file)

    # Filtrar solo predicciones positivas (prediction = 1)
    positive_predictions = predictions[predictions['prediction'] == 1].copy()

    print(f"Total de predicciones: {len(predictions)}")
    print(f"Predicciones positivas: {len(positive_predictions)}")

    # Seleccionar solo las columnas customer_id y product_id
    # Renombrar a empresa y producto
    csv_data = positive_predictions[['customer_id', 'product_id']].copy()
    csv_data.columns = ['empresa', 'producto']

    # Asegurarse de que sean enteros
    csv_data['empresa'] = csv_data['empresa'].astype(int)
    csv_data['producto'] = csv_data['producto'].astype(int)

    # Ordenar por empresa y producto para mejor legibilidad
    csv_data = csv_data.sort_values(['empresa', 'producto'])

    # Exportar a CSV sin headers
    csv_data.to_csv(output_path, index=False, header=False)

    print(f"CSV exportado exitosamente: {output_path}")
    print(f"Total de filas en CSV: {len(csv_data)}")

    return output_path


if __name__ == "__main__":
    # Para pruebas locales
    export_positive_predictions_to_csv()
