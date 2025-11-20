import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta

def get_next_week_date(df: pd.DataFrame) -> pd.Timestamp:
    """Obtiene la fecha de la próxima semana basada en los datos."""
    max_date = df['purchase_date'].max()
    next_week = max_date + timedelta(days=7)
    return next_week

def prepare_prediction_data(df: pd.DataFrame, clientes: pd.DataFrame,
                           productos: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara datos para predicción de la próxima semana.
    Genera todas las combinaciones cliente-producto posibles.
    """
    last_week = df['purchase_date'].max()
    next_week = last_week + timedelta(days=7)

    unique_customers = df['customer_id'].unique()
    unique_products = df['product_id'].unique()

    prediction_data = pd.MultiIndex.from_product(
        [unique_customers, [next_week], unique_products],
        names=['customer_id', 'purchase_date', 'product_id']
    ).to_frame(index=False)

    df_history = df[['customer_id', 'product_id', 'purchase_date',
                     'promedio_items_t-1', 'promedio_items_t-2',
                     'compra_ultima_sem', 'promedio_4s']].copy()

    last_week_data = df_history[df_history['purchase_date'] == last_week].copy()

    last_week_data = last_week_data.rename(columns={
        'promedio_items_t-1': 'prev_t1',
        'promedio_items_t-2': 'prev_t2',
        'compra_ultima_sem': 'prev_compra',
        'promedio_4s': 'prev_4s'
    })

    prediction_data = prediction_data.merge(
        last_week_data[['customer_id', 'product_id', 'prev_t1', 'prev_t2', 'prev_compra', 'prev_4s']],
        on=['customer_id', 'product_id'],
        how='left'
    )

    prediction_data['promedio_items_t-1'] = prediction_data['prev_t1'].fillna(0)
    prediction_data['promedio_items_t-2'] = prediction_data['prev_t2'].fillna(0)
    prediction_data['compra_ultima_sem'] = prediction_data['prev_compra'].fillna(0)
    prediction_data['promedio_4s'] = prediction_data['prev_4s'].fillna(0)

    prediction_data = prediction_data.drop(columns=['prev_t1', 'prev_t2', 'prev_compra', 'prev_4s'])

    prediction_data = (
        prediction_data
        .merge(clientes[['customer_id', 'customer_type', 'X', 'Y', 'num_deliver_per_week']],
               on='customer_id', how='left')
        .merge(productos[['product_id', 'brand', 'sub_category', 'segment', 'package', 'size']],
               on='product_id', how='left')
    )

    prediction_data = prediction_data.dropna()

    return prediction_data

def generate_predictions(model, prediction_data: pd.DataFrame,
                        threshold: float = 0.5) -> pd.DataFrame:
    """Genera predicciones para los datos de entrada."""
    id_cols = ['customer_id', 'product_id', 'purchase_date']
    feature_cols = [c for c in prediction_data.columns if c not in id_cols]

    X = prediction_data[feature_cols]
    y_proba = model.predict_proba(X)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)

    results = prediction_data[id_cols].copy()
    results['prediction'] = y_pred
    results['probability'] = y_proba

    return results

def get_top_predictions(predictions: pd.DataFrame, top_n: int = 1000) -> pd.DataFrame:
    """Obtiene las top N predicciones por probabilidad."""
    return predictions.nlargest(top_n, 'probability')

def summarize_predictions(predictions: pd.DataFrame) -> dict:
    """Resume las predicciones generadas."""
    summary = {
        'total_predictions': len(predictions),
        'positive_predictions': predictions['prediction'].sum(),
        'negative_predictions': (predictions['prediction'] == 0).sum(),
        'avg_probability': predictions['probability'].mean(),
        'prediction_date': predictions['purchase_date'].iloc[0].strftime('%Y-%m-%d'),
        'unique_customers': predictions['customer_id'].nunique(),
        'unique_products': predictions['product_id'].nunique()
    }
    return summary

def save_predictions(predictions: pd.DataFrame, path: str):
    """Guarda predicciones en archivo parquet."""
    predictions.to_parquet(path, index=False)

def load_predictions(path: str) -> pd.DataFrame:
    """Carga predicciones desde archivo parquet."""
    return pd.read_parquet(path)
