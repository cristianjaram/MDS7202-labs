"""
Script simple para exportar predicciones positivas a CSV.
Uso: python export_predictions_to_csv.py
"""
import pandas as pd
import glob
import os

# Configuración de rutas
PREDICTIONS_DIR = 'airflow/data'
OUTPUT_FILE = 'predicciones_positivas.csv'

def main():
    # Buscar el archivo de predicciones más reciente
    pattern = os.path.join(PREDICTIONS_DIR, 'predicciones_*.parquet')
    prediction_files = glob.glob(pattern)

    if not prediction_files:
        print(f"❌ ERROR: No se encontraron archivos de predicciones en {PREDICTIONS_DIR}")
        return

    # Usar el archivo más reciente
    latest_file = max(prediction_files, key=os.path.getctime)
    print(f"📂 Cargando predicciones desde: {latest_file}")

    # Cargar predicciones
    predictions = pd.read_parquet(latest_file)

    print(f"\n📊 Estadísticas:")
    print(f"   Total de predicciones: {len(predictions):,}")
    print(f"   Predicciones positivas: {predictions['prediction'].sum():,}")
    print(f"   Predicciones negativas: {(predictions['prediction'] == 0).sum():,}")
    print(f"   Fecha de predicción: {predictions['purchase_date'].iloc[0]}")

    # Filtrar solo predicciones positivas (prediction = 1)
    positive_predictions = predictions[predictions['prediction'] == 1].copy()

    # Seleccionar solo customer_id y product_id
    csv_data = positive_predictions[['customer_id', 'product_id']].copy()

    # Asegurarse de que sean enteros
    csv_data['customer_id'] = csv_data['customer_id'].astype(int)
    csv_data['product_id'] = csv_data['product_id'].astype(int)

    # Ordenar por customer_id y product_id
    csv_data = csv_data.sort_values(['customer_id', 'product_id'])

    # Exportar a CSV sin headers
    csv_data.to_csv(OUTPUT_FILE, index=False, header=False)

    print(f"\n✅ CSV exportado exitosamente: {OUTPUT_FILE}")
    print(f"   Total de filas en CSV: {len(csv_data):,}")
    print(f"   Clientes únicos: {csv_data['customer_id'].nunique():,}")
    print(f"   Productos únicos: {csv_data['product_id'].nunique():,}")

    # Mostrar algunas filas de ejemplo
    print(f"\n📄 Primeras 10 filas del CSV:")
    print(csv_data.head(10).to_string(index=False, header=False))

if __name__ == "__main__":
    main()
