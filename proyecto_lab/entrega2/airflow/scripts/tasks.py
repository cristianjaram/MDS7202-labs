import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import mlflow
import mlflow.sklearn
import shap
import matplotlib.pyplot as plt
from scipy import stats

from .data_processing import (
    load_data, build_dataset, temporal_split, prepare_features,
    calculate_iqr_limits, remove_outliers, get_feature_columns
)
from .model import (
    optimize_hyperparameters, train_final_model, evaluate_model,
    find_optimal_threshold, save_model, load_model, get_default_params
)
from .prediction import (
    prepare_prediction_data, generate_predictions, summarize_predictions,
    save_predictions, get_next_week_date
)
from .export_csv import export_positive_predictions_to_csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

mlflow.set_tracking_uri(f"file://{os.path.join(BASE_DIR, 'mlruns')}")
mlflow.set_experiment("sodai_drinks_prediction")


def extract_data(data_path: str, **kwargs):
    """Extrae y carga los datos desde los archivos parquet."""
    ti = kwargs['ti']

    clientes, productos, transacciones = load_data(data_path)

    clientes.to_parquet(os.path.join(DATA_DIR, 'clientes.parquet'))
    productos.to_parquet(os.path.join(DATA_DIR, 'productos.parquet'))
    transacciones.to_parquet(os.path.join(DATA_DIR, 'transacciones.parquet'))

    metadata = {
        'n_clientes': len(clientes),
        'n_productos': len(productos),
        'n_transacciones': len(transacciones),
        'extraction_date': datetime.now().isoformat()
    }

    ti.xcom_push(key='extraction_metadata', value=metadata)
    return metadata


def transform_data(**kwargs):
    """Transforma los datos y crea features."""
    ti = kwargs['ti']

    clientes = pd.read_parquet(os.path.join(DATA_DIR, 'clientes.parquet'))
    productos = pd.read_parquet(os.path.join(DATA_DIR, 'productos.parquet'))
    transacciones = pd.read_parquet(os.path.join(DATA_DIR, 'transacciones.parquet'))

    from .data_processing import (
        create_weekly_aggregations, create_cartesian_product,
        create_lag_features, merge_attributes
    )

    compras_semanales = create_weekly_aggregations(transacciones)
    df = create_cartesian_product(compras_semanales)
    df = create_lag_features(df)
    df = merge_attributes(df, clientes, productos)

    df.to_parquet(os.path.join(DATA_DIR, 'dataset_transformed.parquet'))

    metadata = {
        'n_rows': len(df),
        'n_features': len(df.columns),
        'date_range': f"{df['purchase_date'].min()} - {df['purchase_date'].max()}",
        'target_distribution': df['target'].value_counts(normalize=True).to_dict()
    }

    ti.xcom_push(key='transform_metadata', value=metadata)
    return metadata


def detect_drift(**kwargs):
    """Detecta drift en los datos comparando con datos históricos."""
    ti = kwargs['ti']

    df = pd.read_parquet(os.path.join(DATA_DIR, 'dataset_transformed.parquet'))

    historical_stats_path = os.path.join(DATA_DIR, 'historical_stats.json')

    numeric_features, _ = get_feature_columns()
    current_stats = {}

    for col in numeric_features:
        if col in df.columns:
            current_stats[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'median': float(df[col].median())
            }

    drift_detected = False
    drift_report = {'features_with_drift': [], 'drift_scores': {}}

    if os.path.exists(historical_stats_path):
        with open(historical_stats_path, 'r') as f:
            historical_stats = json.load(f)

        for col in numeric_features:
            if col in current_stats and col in historical_stats:
                hist_mean = historical_stats[col]['mean']
                hist_std = historical_stats[col]['std']
                curr_mean = current_stats[col]['mean']

                if hist_std > 0:
                    z_score = abs(curr_mean - hist_mean) / hist_std
                    drift_report['drift_scores'][col] = float(z_score)

                    if z_score > 2.0:
                        drift_detected = True
                        drift_report['features_with_drift'].append(col)
    else:
        drift_detected = True
        drift_report['reason'] = 'No historical data available - initial training required'

    with open(historical_stats_path, 'w') as f:
        json.dump(current_stats, f)

    ti.xcom_push(key='drift_detected', value=drift_detected)
    ti.xcom_push(key='drift_report', value=drift_report)

    if drift_detected:
        return 'retrain_model'
    else:
        return 'skip_retrain'


def retrain_model(n_trials: int = 25, **kwargs):
    """Reentrena el modelo con optimización de hiperparámetros."""
    ti = kwargs['ti']

    df = pd.read_parquet(os.path.join(DATA_DIR, 'dataset_transformed.parquet'))
    clientes = pd.read_parquet(os.path.join(DATA_DIR, 'clientes.parquet'))
    productos = pd.read_parquet(os.path.join(DATA_DIR, 'productos.parquet'))

    train, valid, test = temporal_split(df, train_end="2024-09-30", valid_end="2024-11-30")

    num_cols_outliers = ['X', 'Y', 'size']
    iqr_limits = calculate_iqr_limits(train, num_cols_outliers)

    train_clean = remove_outliers(train, iqr_limits)
    valid_clean = remove_outliers(valid, iqr_limits)

    X_train, y_train = prepare_features(train_clean)
    X_valid, y_valid = prepare_features(valid_clean)

    numeric_features, categorical_features = get_feature_columns()

    with mlflow.start_run(run_name=f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        best_params, best_score = optimize_hyperparameters(
            X_train, y_train, X_valid, y_valid,
            numeric_features, categorical_features,
            n_trials=n_trials, use_smote=True
        )

        final_model = train_final_model(
            X_train, y_train,
            numeric_features, categorical_features,
            best_params.copy(), use_smote=True
        )

        metrics = evaluate_model(final_model, X_valid, y_valid)
        optimal_threshold, _ = find_optimal_threshold(final_model, X_valid, y_valid)

        mlflow.log_params(best_params)
        mlflow.log_metric('f1_weighted', metrics['f1_weighted'])
        mlflow.log_metric('f1_class1', metrics['f1_class1'])
        mlflow.log_metric('roc_auc', metrics['roc_auc'])
        mlflow.log_metric('pr_auc', metrics['pr_auc'])
        mlflow.log_metric('optimal_threshold', optimal_threshold)

        try:
            classifier = final_model.named_steps['classifier']
            preprocessor = final_model.named_steps['preprocessor']
            X_valid_transformed = preprocessor.transform(X_valid)

            explainer = shap.TreeExplainer(classifier)
            shap_values = explainer.shap_values(X_valid_transformed[:100])

            plt.figure(figsize=(10, 8))
            if isinstance(shap_values, list):
                shap.summary_plot(shap_values[1], X_valid_transformed[:100], show=False)
            else:
                shap.summary_plot(shap_values, X_valid_transformed[:100], show=False)

            shap_path = os.path.join(DATA_DIR, 'shap_summary.png')
            plt.savefig(shap_path, bbox_inches='tight', dpi=150)
            plt.close()
            mlflow.log_artifact(shap_path)
        except Exception as e:
            print(f"SHAP plot failed: {e}")

        model_path = os.path.join(MODELS_DIR, 'modelo_final.pkl')
        save_model(final_model, model_path)
        mlflow.sklearn.log_model(final_model, "model")

        model_info = {
            'model_path': model_path,
            'optimal_threshold': optimal_threshold,
            'metrics': {k: v for k, v in metrics.items() if k != 'confusion_matrix' and k != 'classification_report'},
            'best_params': best_params,
            'training_date': datetime.now().isoformat()
        }

        with open(os.path.join(MODELS_DIR, 'model_info.json'), 'w') as f:
            json.dump(model_info, f, indent=2)

        ti.xcom_push(key='model_info', value=model_info)

    return model_info


def generate_predictions_task(**kwargs):
    """Genera predicciones para la próxima semana."""
    ti = kwargs['ti']

    df = pd.read_parquet(os.path.join(DATA_DIR, 'dataset_transformed.parquet'))
    clientes = pd.read_parquet(os.path.join(DATA_DIR, 'clientes.parquet'))
    productos = pd.read_parquet(os.path.join(DATA_DIR, 'productos.parquet'))

    model_path = os.path.join(MODELS_DIR, 'modelo_final.pkl')
    model_info_path = os.path.join(MODELS_DIR, 'model_info.json')

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")

    model = load_model(model_path)

    threshold = 0.5
    if os.path.exists(model_info_path):
        with open(model_info_path, 'r') as f:
            model_info = json.load(f)
            threshold = model_info.get('optimal_threshold', 0.5)

    prediction_data = prepare_prediction_data(df, clientes, productos)
    predictions = generate_predictions(model, prediction_data, threshold=threshold)

    next_week = get_next_week_date(df)
    prediction_filename = f"predicciones_{next_week.strftime('%Y_%m_%d')}.parquet"
    prediction_path = os.path.join(DATA_DIR, prediction_filename)

    save_predictions(predictions, prediction_path)

    summary = summarize_predictions(predictions)
    summary['prediction_file'] = prediction_filename
    summary['threshold_used'] = threshold

    with open(os.path.join(DATA_DIR, 'latest_prediction_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    ti.xcom_push(key='prediction_summary', value=summary)

    return summary


def export_predictions_csv(**kwargs):
    """Exporta predicciones positivas a CSV sin headers."""
    ti = kwargs['ti']

    csv_path = export_positive_predictions_to_csv(
        predictions_dir=DATA_DIR,
        output_path=os.path.join(DATA_DIR, 'predicciones_positivas.csv')
    )

    # Verificar el archivo generado
    import pandas as pd
    csv_data = pd.read_csv(csv_path, header=None, names=['empresa', 'producto'])

    export_info = {
        'csv_path': csv_path,
        'total_rows': len(csv_data),
        'unique_customers': csv_data['empresa'].nunique(),
        'unique_products': csv_data['producto'].nunique(),
        'export_date': datetime.now().isoformat()
    }

    ti.xcom_push(key='export_info', value=export_info)

    print(f"CSV exportado exitosamente: {csv_path}")
    print(f"Total de predicciones positivas: {export_info['total_rows']}")

    return export_info
