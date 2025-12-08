"""
Script para combinar datos históricos con nuevos datos de enero.
"""
import pandas as pd
import os
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Rutas
OLD_DATA_PATH = '../entrega1/transacciones.parquet'
NEW_DATA_PATH = '../entrega3/batch_t3.parquet'
BACKUP_PATH = '../entrega1/transacciones_backup.parquet'
OUTPUT_PATH = '../entrega1/transacciones.parquet'

def main():
    print("=" * 60)
    print("COMBINANDO DATOS HISTÓRICOS + NUEVOS DATOS DE ENERO")
    print("=" * 60)

    # 1. Hacer backup de los datos originales
    if os.path.exists(OLD_DATA_PATH):
        print(f"\n1. Haciendo backup de datos originales...")
        old_data = pd.read_parquet(OLD_DATA_PATH)
        old_data.to_parquet(BACKUP_PATH, index=False)
        print(f"   ✅ Backup guardado en: {BACKUP_PATH}")
        print(f"   - Transacciones originales: {len(old_data):,}")
        print(f"   - Rango: {old_data['purchase_date'].min()} a {old_data['purchase_date'].max()}")
    else:
        print(f"\n❌ ERROR: No se encontró {OLD_DATA_PATH}")
        return

    # 2. Cargar nuevos datos
    if os.path.exists(NEW_DATA_PATH):
        print(f"\n2. Cargando nuevos datos de enero...")
        new_data = pd.read_parquet(NEW_DATA_PATH)
        print(f"   ✅ Nuevos datos cargados")
        print(f"   - Transacciones nuevas: {len(new_data):,}")
        print(f"   - Rango: {new_data['purchase_date'].min()} a {new_data['purchase_date'].max()}")
    else:
        print(f"\n❌ ERROR: No se encontró {NEW_DATA_PATH}")
        return

    # 3. Verificar que no haya solapamiento de fechas
    old_max_date = old_data['purchase_date'].max()
    new_min_date = new_data['purchase_date'].min()

    print(f"\n3. Verificando continuidad temporal...")
    print(f"   - Última fecha datos antiguos: {old_max_date}")
    print(f"   - Primera fecha datos nuevos: {new_min_date}")

    if new_min_date <= old_max_date:
        print(f"   ⚠️  ADVERTENCIA: Hay solapamiento de fechas")
        print(f"   - Se mantendrán todos los datos, pero puede haber duplicados")
    else:
        print(f"   ✅ Datos son consecutivos (sin solapamiento)")

    # 4. Combinar datos
    print(f"\n4. Combinando datos...")
    combined = pd.concat([old_data, new_data], ignore_index=True)

    # Eliminar posibles duplicados (mismo customer, product, order_id, fecha)
    before_dedup = len(combined)
    combined = combined.drop_duplicates(
        subset=['customer_id', 'product_id', 'order_id', 'purchase_date'],
        keep='first'
    )
    after_dedup = len(combined)

    if before_dedup != after_dedup:
        print(f"   ⚠️  Se eliminaron {before_dedup - after_dedup:,} duplicados")

    # Ordenar por fecha
    combined = combined.sort_values('purchase_date').reset_index(drop=True)

    print(f"   ✅ Datos combinados exitosamente")
    print(f"   - Total transacciones: {len(combined):,}")
    print(f"   - Rango completo: {combined['purchase_date'].min()} a {combined['purchase_date'].max()}")

    # 5. Guardar datos combinados
    print(f"\n5. Guardando datos combinados...")
    combined.to_parquet(OUTPUT_PATH, index=False)
    print(f"   ✅ Datos guardados en: {OUTPUT_PATH}")

    # 6. Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Transacciones originales: {len(old_data):,}")
    print(f"Transacciones nuevas:     {len(new_data):,}")
    print(f"Total combinado:          {len(combined):,}")
    print(f"\nRango temporal final:")
    print(f"  Desde: {combined['purchase_date'].min()}")
    print(f"  Hasta: {combined['purchase_date'].max()}")
    print(f"\nClientes únicos:  {combined['customer_id'].nunique():,}")
    print(f"Productos únicos: {combined['product_id'].nunique():,}")
    print("\n✅ DATOS LISTOS PARA AIRFLOW!")
    print("=" * 60)

if __name__ == "__main__":
    main()
