import pandas as pd
import numpy as np
import optuna
import mlflow
import mlflow.sklearn
import pickle
import os
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score
from xgboost import XGBClassifier


MODELS_DIR = "models"
PLOTS_DIR = "plots"

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

df = pd.read_csv("water_potability.csv")
X = df.drop("Potability", axis=1)
y = df["Potability"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

def optimize_model(trials: int = 25):
    experiment_name = f"XGBoost_Optuna_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    mlflow.set_experiment(experiment_name)

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 500),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "gamma": trial.suggest_float("gamma", 0, 5),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "eval_metric": "logloss",
            "use_label_encoder": False,
            "random_state": 42,
        }

        mlflow.start_run(run_name=f"XGBoost con lr {params['learning_rate']:.3f}")
        mlflow.log_params(params)

        pipeline = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="mean")),
            ("scaler", StandardScaler()),
            ("model", XGBClassifier(**params))
        ])

        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)
        f1 = f1_score(y_test, preds)

        mlflow.log_metric("valid_f1", f1)
        mlflow.end_run()

        return f1

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=trials)


    best_params = study.best_params
    print("Best params:", best_params)

    mlflow.set_experiment("XGBoost_Best_Model")
    with mlflow.start_run(run_name="Mejor XGBoost Optuna"):
        final_pipeline = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="mean")),
            ("scaler", StandardScaler()),
            ("model", XGBClassifier(**best_params))
        ])

        final_pipeline.fit(X_train, y_train)
        preds = final_pipeline.predict(X_test)
        best_f1 = f1_score(y_test, preds)
        mlflow.log_metric("valid_f1", best_f1)

        # Guardar modelo
        model_path = os.path.join(MODELS_DIR, "best_xgboost_model.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(final_pipeline, f)
        mlflow.log_artifact(model_path, artifact_path="models")

        # Guardar gráfico de importancia de variables
        importances = final_pipeline.named_steps["model"].feature_importances_
        plt.bar(X.columns, importances)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plot_path = os.path.join(PLOTS_DIR, "feature_importance.png")
        plt.savefig(plot_path)
        mlflow.log_artifact(plot_path, artifact_path="plots")

    print(f"\n✅ Optimización completada. Mejor modelo guardado en {model_path}")


def get_best_model(experiment_id):
    runs = mlflow.search_runs(experiment_id)
    best_model_id = runs.sort_values("metrics.valid_f1", ascending=False)["run_id"].iloc[0]
    best_model = mlflow.sklearn.load_model("runs:/" + best_model_id + "/model")
    return best_model

if __name__ == "__main__":
    optimize_model(trials=25)
