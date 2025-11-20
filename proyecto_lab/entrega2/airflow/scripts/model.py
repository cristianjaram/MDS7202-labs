import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any
import optuna
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix
)
from lightgbm import LGBMClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
import joblib
import warnings

warnings.filterwarnings('ignore', category=UserWarning)

def create_preprocessor(numeric_features: list, categorical_features: list,
                       scaler_type: str = 'minmax') -> ColumnTransformer:
    """Crea el preprocesador con escalador y encoder."""
    if scaler_type == 'standard':
        scaler = StandardScaler()
    elif scaler_type == 'minmax':
        scaler = MinMaxScaler()
    else:
        scaler = 'passthrough'

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', scaler, numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ]
    )
    return preprocessor

def create_model_pipeline(numeric_features: list, categorical_features: list,
                         model_params: Dict, use_smote: bool = True,
                         scaler_type: str = 'minmax') -> Pipeline:
    """Crea pipeline completo con preprocesamiento, SMOTE y modelo."""
    preprocessor = create_preprocessor(numeric_features, categorical_features, scaler_type)

    if use_smote:
        pipeline = ImbPipeline([
            ('preprocessor', preprocessor),
            ('smote', SMOTE(random_state=42, k_neighbors=5)),
            ('classifier', LGBMClassifier(**model_params, verbose=-1))
        ])
    else:
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', LGBMClassifier(**model_params, verbose=-1))
        ])

    return pipeline

def cross_validate_model(pipeline, X: pd.DataFrame, y: pd.Series,
                        n_splits: int = 5) -> Tuple[float, float]:
    """Realiza cross-validation estratificada."""
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    scores = cross_val_score(
        pipeline, X, y,
        cv=cv,
        scoring='f1_weighted',
        n_jobs=-1
    )

    return scores.mean(), scores.std()

def optimize_hyperparameters(X_train: pd.DataFrame, y_train: pd.Series,
                            X_valid: pd.DataFrame, y_valid: pd.Series,
                            numeric_features: list, categorical_features: list,
                            n_trials: int = 50, use_smote: bool = True) -> Tuple[Dict, float]:
    """Optimiza hiperparámetros con Optuna."""

    def objective(trial):
        scaler_name = trial.suggest_categorical("scaler", ["standard", "minmax"])

        params = {
            "num_leaves": trial.suggest_int("num_leaves", 20, 200),
            "max_depth": trial.suggest_int("max_depth", 3, 15),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 100, 800),
            "min_child_samples": trial.suggest_int("min_child_samples", 10, 100),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 2.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 2.0),
            "random_state": 42,
            "class_weight": "balanced"
        }

        pipeline = create_model_pipeline(
            numeric_features, categorical_features,
            params, use_smote=use_smote, scaler_type=scaler_name
        )

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_valid)
        score = f1_score(y_valid, y_pred, average="weighted")

        return score

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    return study.best_params, study.best_value

def train_final_model(X_train: pd.DataFrame, y_train: pd.Series,
                     numeric_features: list, categorical_features: list,
                     best_params: Dict, use_smote: bool = True) -> Pipeline:
    """Entrena el modelo final con los mejores hiperparámetros."""
    scaler_type = best_params.pop('scaler', 'minmax')

    model_params = {
        "num_leaves": best_params.get("num_leaves", 126),
        "max_depth": best_params.get("max_depth", 12),
        "learning_rate": best_params.get("learning_rate", 0.207),
        "n_estimators": best_params.get("n_estimators", 519),
        "min_child_samples": best_params.get("min_child_samples", 82),
        "subsample": best_params.get("subsample", 0.82),
        "colsample_bytree": best_params.get("colsample_bytree", 0.94),
        "reg_alpha": best_params.get("reg_alpha", 0.45),
        "reg_lambda": best_params.get("reg_lambda", 0.75),
        "random_state": 42,
        "class_weight": "balanced"
    }

    pipeline = create_model_pipeline(
        numeric_features, categorical_features,
        model_params, use_smote=use_smote, scaler_type=scaler_type
    )

    pipeline.fit(X_train, y_train)

    return pipeline

def evaluate_model(model, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """Evalúa el modelo con múltiples métricas."""
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]

    metrics = {
        'f1_weighted': f1_score(y, y_pred, average='weighted'),
        'f1_class1': f1_score(y, y_pred, pos_label=1),
        'roc_auc': roc_auc_score(y, y_proba),
        'pr_auc': average_precision_score(y, y_proba),
        'confusion_matrix': confusion_matrix(y, y_pred).tolist(),
        'classification_report': classification_report(y, y_pred, output_dict=True)
    }

    return metrics

def find_optimal_threshold(model, X: pd.DataFrame, y: pd.Series) -> Tuple[float, float]:
    """Encuentra el threshold óptimo para maximizar F1."""
    y_proba = model.predict_proba(X)[:, 1]

    best_threshold = 0.5
    best_f1 = 0

    for threshold in np.arange(0.1, 0.9, 0.01):
        y_pred = (y_proba >= threshold).astype(int)
        f1 = f1_score(y, y_pred)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    return best_threshold, best_f1

def save_model(model, path: str):
    """Guarda el modelo en disco."""
    joblib.dump(model, path)

def load_model(path: str):
    """Carga el modelo desde disco."""
    return joblib.load(path)

def get_default_params() -> Dict:
    """Retorna parámetros por defecto basados en optimización previa."""
    return {
        'scaler': 'minmax',
        'num_leaves': 126,
        'max_depth': 12,
        'learning_rate': 0.207,
        'n_estimators': 519,
        'min_child_samples': 82,
        'subsample': 0.82,
        'colsample_bytree': 0.94,
        'reg_alpha': 0.45,
        'reg_lambda': 0.75,
        'random_state': 42,
        'class_weight': 'balanced'
    }
