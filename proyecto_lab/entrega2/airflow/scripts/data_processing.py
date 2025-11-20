import pandas as pd
import numpy as np
from typing import Tuple, Dict

def load_data(data_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carga los archivos parquet de clientes, productos y transacciones."""
    clientes = pd.read_parquet(f"{data_path}/clientes.parquet")
    productos = pd.read_parquet(f"{data_path}/productos.parquet")
    transacciones = pd.read_parquet(f"{data_path}/transacciones.parquet")
    return clientes, productos, transacciones

def create_weekly_aggregations(transacciones: pd.DataFrame) -> pd.DataFrame:
    """Crea agregaciones semanales de compras por cliente-producto."""
    compras_semanales = transacciones.groupby([
        'customer_id',
        pd.Grouper(key='purchase_date', freq='W-SUN'),
        'product_id'
    ])['items'].mean().reset_index(name='promedio_items')
    return compras_semanales

def create_cartesian_product(compras_semanales: pd.DataFrame) -> pd.DataFrame:
    """Crea producto cartesiano cliente x producto x semana."""
    semanas = compras_semanales['purchase_date'].sort_values().unique()
    df_list = []

    for cust_id, group in compras_semanales.groupby('customer_id'):
        productos_cliente = group['product_id'].unique()
        cartesian = pd.MultiIndex.from_product(
            [[cust_id], semanas, productos_cliente],
            names=['customer_id', 'purchase_date', 'product_id']
        ).to_frame(index=False)
        df_list.append(cartesian)

    df_merged = pd.concat(df_list, ignore_index=True)
    df_merged = df_merged.merge(
        compras_semanales,
        on=['customer_id', 'purchase_date', 'product_id'],
        how='left'
    )

    df_merged['target'] = (df_merged['promedio_items'] > 0).astype(int)
    df_merged['promedio_items'] = df_merged['promedio_items'].fillna(0)

    return df_merged

def create_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Crea features de lag temporal."""
    df = df.sort_values(['customer_id', 'product_id', 'purchase_date']).copy()

    df['promedio_items_t-1'] = df.groupby(['customer_id', 'product_id'])['promedio_items'].shift(1)
    df['promedio_items_t-2'] = df.groupby(['customer_id', 'product_id'])['promedio_items'].shift(2)
    df['compra_ultima_sem'] = (df['promedio_items_t-1'] > 0).astype(int)

    df['promedio_4s'] = (
        df.groupby(['customer_id', 'product_id'])['promedio_items']
        .transform(lambda x: x.shift(1).rolling(4).mean())
    )

    df[['promedio_items_t-1', 'promedio_items_t-2', 'promedio_4s']] = \
        df[['promedio_items_t-1', 'promedio_items_t-2', 'promedio_4s']].fillna(0)

    df.drop(columns=['promedio_items'], inplace=True)

    return df

def merge_attributes(df: pd.DataFrame, clientes: pd.DataFrame, productos: pd.DataFrame) -> pd.DataFrame:
    """Une atributos de clientes y productos al dataset."""
    df = (
        df
        .merge(clientes[['customer_id', 'customer_type', 'X', 'Y', 'num_deliver_per_week']],
               on='customer_id', how='inner')
        .merge(productos[['product_id', 'brand', 'sub_category', 'segment', 'package', 'size']],
               on='product_id', how='inner')
    )
    return df

def calculate_iqr_limits(df: pd.DataFrame, cols: list, factor: float = 1.5) -> Dict:
    """Calcula límites IQR para detección de outliers."""
    limits = {}
    for col in cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR
        limits[col] = (lower, upper)
    return limits

def remove_outliers(df: pd.DataFrame, limits: Dict) -> pd.DataFrame:
    """Elimina outliers usando límites predefinidos."""
    df_clean = df.copy()
    for col, (lower, upper) in limits.items():
        df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]
    return df_clean

def temporal_split(df: pd.DataFrame, train_end: str, valid_end: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Divide datos temporalmente en train, validation y test."""
    df = df.sort_values('purchase_date')

    train_end_dt = pd.to_datetime(train_end)
    valid_end_dt = pd.to_datetime(valid_end)

    train = df[df['purchase_date'] <= train_end_dt].copy()
    valid = df[(df['purchase_date'] > train_end_dt) & (df['purchase_date'] <= valid_end_dt)].copy()
    test = df[df['purchase_date'] > valid_end_dt].copy()

    return train, valid, test

def prepare_features(df: pd.DataFrame, drop_ids: bool = True) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepara features y target, opcionalmente eliminando IDs."""
    if drop_ids:
        cols_to_drop = ['customer_id', 'product_id', 'purchase_date', 'target']
        cols_to_drop = [c for c in cols_to_drop if c in df.columns]
        X = df.drop(columns=cols_to_drop)
        y = df['target'] if 'target' in df.columns else None
    else:
        X = df.drop(columns=['target']) if 'target' in df.columns else df
        y = df['target'] if 'target' in df.columns else None

    return X, y

def build_dataset(data_path: str) -> pd.DataFrame:
    """Pipeline completo para construir el dataset desde archivos raw."""
    clientes, productos, transacciones = load_data(data_path)

    compras_semanales = create_weekly_aggregations(transacciones)
    df = create_cartesian_product(compras_semanales)
    df = create_lag_features(df)
    df = merge_attributes(df, clientes, productos)

    return df

def get_feature_columns():
    """Retorna las columnas numéricas y categóricas."""
    numeric_features = [
        'promedio_items_t-1', 'promedio_items_t-2', 'compra_ultima_sem',
        'promedio_4s', 'X', 'Y', 'num_deliver_per_week', 'size'
    ]
    categorical_features = ['customer_type', 'brand', 'sub_category', 'segment', 'package']

    return numeric_features, categorical_features
