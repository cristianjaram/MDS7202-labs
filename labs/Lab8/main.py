import pandas as pd
import numpy as np
import mlflow as mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from xgboost import XGBClassifier

# Load dataset
df = pd.read_csv("water_potability.csv")

# Preprocess data
X = df.drop("Potability", axis=1)
y = df["Potability"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#pipeline de pre procesamiento para xgboost
pipeline = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='mean')),    
    ('scaler', StandardScaler()),      
    ("model", XGBClassifier(use_label_encoder=False, eval_metric='logloss'))
])

#ENTRENAMIENTO Y TRACKING
mlflow.set_experiment("XGBoost_Base")
mlflow.autolog()  # Habilitar autologging
with mlflow.start_run(run_name ="XGBoost Base Run"):
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # Evaluar el modelo
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)

    print(f"Accuracy: {accuracy}")
    print(f"F1 Score: {f1}")
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
