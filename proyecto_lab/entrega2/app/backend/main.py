from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
import joblib
import os
import json

app = FastAPI(
    title="SodAI Drinks Prediction API",
    description="API para predecir si un cliente realizará un pedido de un producto",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/modelo_final.pkl")
MODEL_INFO_PATH = os.getenv("MODEL_INFO_PATH", "/app/models/model_info.json")
DATA_PATH = os.getenv("DATA_PATH", "/app/data")

model = None
model_info = None
optimal_threshold = 0.5
predictions_df = None
clientes_df = None
productos_df = None
transacciones_df = None

class PredictionInput(BaseModel):
    promedio_items_t1: float
    promedio_items_t2: float
    compra_ultima_sem: int
    promedio_4s: float
    X: float
    Y: float
    num_deliver_per_week: float
    size: float
    customer_type: str
    brand: str
    sub_category: str
    segment: str
    package: str

class PredictionOutput(BaseModel):
    prediction: int
    probability: float
    will_purchase: str

class BatchPredictionInput(BaseModel):
    data: List[PredictionInput]

class BatchPredictionOutput(BaseModel):
    predictions: List[PredictionOutput]
    total: int
    positive_count: int

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str

@app.on_event("startup")
async def load_model():
    global model, model_info, optimal_threshold, predictions_df, clientes_df, productos_df, transacciones_df

    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            print(f"Modelo cargado desde {MODEL_PATH}")
        else:
            print(f"Modelo no encontrado en {MODEL_PATH}")

        if os.path.exists(MODEL_INFO_PATH):
            with open(MODEL_INFO_PATH, 'r') as f:
                model_info = json.load(f)
                optimal_threshold = model_info.get('optimal_threshold', 0.5)
                print(f"Threshold óptimo: {optimal_threshold}")

        if os.path.exists(DATA_PATH):
            prediction_files = [f for f in os.listdir(DATA_PATH) if f.startswith('predicciones_') and f.endswith('.parquet')]
            if prediction_files:
                latest_prediction = sorted(prediction_files)[-1]
                predictions_df = pd.read_parquet(os.path.join(DATA_PATH, latest_prediction))
                print(f"Predicciones cargadas: {latest_prediction} ({len(predictions_df)} registros)")

            clientes_path = os.path.join(DATA_PATH, 'clientes.parquet')
            if os.path.exists(clientes_path):
                clientes_df = pd.read_parquet(clientes_path)
                print(f"Clientes cargados: {len(clientes_df)} registros")

            productos_path = os.path.join(DATA_PATH, 'productos.parquet')
            if os.path.exists(productos_path):
                productos_df = pd.read_parquet(productos_path)
                print(f"Productos cargados: {len(productos_df)} registros")

            transacciones_path = os.path.join(DATA_PATH, 'transacciones.parquet')
            if os.path.exists(transacciones_path):
                transacciones_df = pd.read_parquet(transacciones_path)
                print(f"Transacciones cargadas: {len(transacciones_df)} registros")
    except Exception as e:
        print(f"Error cargando datos: {e}")

@app.get("/", response_model=dict)
async def root():
    return {
        "message": "SodAI Drinks Prediction API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        model_path=MODEL_PATH
    )

@app.post("/predict", response_model=PredictionOutput)
async def predict(input_data: PredictionInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no cargado")

    try:
        df = pd.DataFrame([{
            'promedio_items_t-1': input_data.promedio_items_t1,
            'promedio_items_t-2': input_data.promedio_items_t2,
            'compra_ultima_sem': input_data.compra_ultima_sem,
            'promedio_4s': input_data.promedio_4s,
            'X': input_data.X,
            'Y': input_data.Y,
            'num_deliver_per_week': input_data.num_deliver_per_week,
            'size': input_data.size,
            'customer_type': input_data.customer_type,
            'brand': input_data.brand,
            'sub_category': input_data.sub_category,
            'segment': input_data.segment,
            'package': input_data.package
        }])

        probability = model.predict_proba(df)[0, 1]
        prediction = int(probability >= optimal_threshold)

        return PredictionOutput(
            prediction=prediction,
            probability=round(float(probability), 4),
            will_purchase="Sí comprará" if prediction == 1 else "No comprará"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch", response_model=BatchPredictionOutput)
async def predict_batch(input_data: BatchPredictionInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no cargado")

    try:
        records = []
        for item in input_data.data:
            records.append({
                'promedio_items_t-1': item.promedio_items_t1,
                'promedio_items_t-2': item.promedio_items_t2,
                'compra_ultima_sem': item.compra_ultima_sem,
                'promedio_4s': item.promedio_4s,
                'X': item.X,
                'Y': item.Y,
                'num_deliver_per_week': item.num_deliver_per_week,
                'size': item.size,
                'customer_type': item.customer_type,
                'brand': item.brand,
                'sub_category': item.sub_category,
                'segment': item.segment,
                'package': item.package
            })

        df = pd.DataFrame(records)
        probabilities = model.predict_proba(df)[:, 1]
        predictions = (probabilities >= optimal_threshold).astype(int)

        results = []
        for pred, prob in zip(predictions, probabilities):
            results.append(PredictionOutput(
                prediction=int(pred),
                probability=round(float(prob), 4),
                will_purchase="Sí comprará" if pred == 1 else "No comprará"
            ))

        return BatchPredictionOutput(
            predictions=results,
            total=len(results),
            positive_count=int(predictions.sum())
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model/info")
async def get_model_info():
    if model_info is None:
        raise HTTPException(status_code=404, detail="Información del modelo no disponible")
    return model_info

@app.get("/customers")
async def get_customers():
    """Obtiene la lista de clientes disponibles con transacciones."""
    if clientes_df is None or transacciones_df is None:
        raise HTTPException(status_code=503, detail="Datos de clientes no disponibles")

    customers_with_transactions = transacciones_df['customer_id'].unique()
    filtered_customers = clientes_df[clientes_df['customer_id'].isin(customers_with_transactions)]
    customers = filtered_customers[['customer_id', 'customer_type']].to_dict('records')
    return {"customers": customers, "total": len(customers)}

@app.get("/customers/{customer_id}/products")
async def get_customer_products(customer_id: str):
    """Obtiene los productos que un cliente ha comprado históricamente."""
    if transacciones_df is None or productos_df is None:
        raise HTTPException(status_code=503, detail="Datos no disponibles")

    try:
        customer_id_int = int(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"ID de cliente inválido: {customer_id}")

    customer_transactions = transacciones_df[transacciones_df['customer_id'] == customer_id_int]
    if customer_transactions.empty:
        raise HTTPException(status_code=404, detail=f"Cliente {customer_id} no encontrado")

    product_ids = customer_transactions['product_id'].unique().tolist()
    products = productos_df[productos_df['product_id'].isin(product_ids)][
        ['product_id', 'brand', 'sub_category', 'segment', 'package', 'size']
    ].to_dict('records')

    return {"customer_id": customer_id, "products": products, "total": len(products)}

@app.get("/predict/customer/{customer_id}/product/{product_id}")
async def predict_customer_product(customer_id: str, product_id: str):
    """Obtiene la predicción para una tupla cliente-producto específica."""
    if predictions_df is None:
        raise HTTPException(status_code=503, detail="Predicciones no disponibles")

    try:
        customer_id_int = int(customer_id)
        product_id_int = int(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="IDs inválidos")

    result = predictions_df[
        (predictions_df['customer_id'] == customer_id_int) &
        (predictions_df['product_id'] == product_id_int)
    ]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No hay predicción para cliente {customer_id} y producto {product_id}"
        )

    prediction_row = result.iloc[0]
    return {
        "customer_id": customer_id,
        "product_id": product_id,
        "prediction": int(prediction_row['prediction']),
        "probability": round(float(prediction_row['probability']), 4),
        "will_purchase": "Sí comprará" if prediction_row['prediction'] == 1 else "No comprará",
        "prediction_date": str(prediction_row['purchase_date'])
    }

@app.get("/predictions/top/{n}")
async def get_top_predictions(n: int = 100):
    """Obtiene las top N predicciones con mayor probabilidad."""
    if predictions_df is None:
        raise HTTPException(status_code=503, detail="Predicciones no disponibles")

    top_predictions = predictions_df.nlargest(n, 'probability')
    results = top_predictions.to_dict('records')

    for r in results:
        r['purchase_date'] = str(r['purchase_date'])

    return {"top_predictions": results, "total": len(results)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
