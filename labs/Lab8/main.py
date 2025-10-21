# import pandas as pd
# import numpy as np
# import mlflow as mlflow
# import mlflow.sklearn
# from sklearn.model_selection import train_test_split
# from sklearn.linear_model import LinearRegression
# from sklearn.pipeline import Pipeline
# from sklearn.preprocessing import StandardScaler
# from sklearn.impute import SimpleImputer
# from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
# from xgboost import XGBClassifier

# # Load dataset
# df = pd.read_csv("water_potability.csv")

# # Preprocess data
# X = df.drop("Potability", axis=1)
# y = df["Potability"]

# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# #pipeline de pre procesamiento para xgboost
# pipeline = Pipeline(steps=[
#     ('imputer', SimpleImputer(strategy='mean')),    
#     ('scaler', StandardScaler()),      
#     ("model", XGBClassifier(use_label_encoder=False, eval_metric='logloss'))
# ])

# #ENTRENAMIENTO Y TRACKING
# mlflow.set_experiment("XGBoost_Base")
# mlflow.autolog()  # Habilitar autologging
# with mlflow.start_run(run_name ="XGBoost Base Run"):
#     pipeline.fit(X_train, y_train)
#     y_pred = pipeline.predict(X_test)

#     # Evaluar el modelo
#     accuracy = accuracy_score(y_test, y_pred)
#     f1 = f1_score(y_test, y_pred)
#     precision = precision_score(y_test, y_pred)
#     recall = recall_score(y_test, y_pred)

#     print(f"Accuracy: {accuracy}")
#     print(f"F1 Score: {f1}")
#     print(f"Precision: {precision}")
#     print(f"Recall: {recall}")


from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import numpy as np

# ==============================
# CARGA DEL MODELO ENTRENADO
# ==============================
with open("models/best_xgboost_model.pkl", "rb") as f:
    model = pickle.load(f)

# ==============================
# DEFINICIÓN DE LA APLICACIÓN
# ==============================
app = FastAPI(
    title="API de Potabilidad del Agua",
    description="Modelo de Machine Learning basado en XGBoost que predice si el agua es potable o no, a partir de mediciones químicas obtenidas por sensores (features del modelo)",
    version="1.0"
)

# ==============================
# ESQUEMA DE ENTRADA (Pydantic)
# ==============================
class WaterSample(BaseModel):
    ph: float
    Hardness: float
    Solids: float
    Chloramines: float
    Sulfate: float
    Conductivity: float
    Organic_carbon: float
    Trihalomethanes: float
    Turbidity: float

# ==============================
# RUTAS
# ==============================
@app.get("/")
def home():
    return {
        "mensaje": "Modelo de predicción de potabilidad del agua.",
        "descripcion": "Predice si el agua es potable (1) o no potable (0) en base a 9 variables químicas.",
        "entrada": ["ph", "Hardness", "Solids", "Chloramines", "Sulfate", "Conductivity", "Organic_carbon", "Trihalomethanes", "Turbidity"],
        "salida": {"potabilidad": "0 = no potable, 1 = potable"}
    }

@app.post("/potabilidad/")
def predict_potability(sample: WaterSample):
    features = np.array([[sample.ph, sample.Hardness, sample.Solids, sample.Chloramines,
                          sample.Sulfate, sample.Conductivity, sample.Organic_carbon,
                          sample.Trihalomethanes, sample.Turbidity]])
    pred = model.predict(features)[0]
    return {"potabilidad": int(pred)}

# ==============================
# EJECUCIÓN LOCAL
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
