import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
RAW_DATA_PATH = os.path.join(os.path.dirname(BASE_DIR), '..', 'entrega1')

NUMERIC_FEATURES = [
    'promedio_items_t-1', 'promedio_items_t-2', 'compra_ultima_sem',
    'promedio_4s', 'X', 'Y', 'num_deliver_per_week', 'size'
]

CATEGORICAL_FEATURES = [
    'customer_type', 'brand', 'sub_category', 'segment', 'package'
]

OUTLIER_COLUMNS = ['X', 'Y', 'size']

TRAIN_END = "2024-09-30"
VALID_END = "2024-11-30"

DEFAULT_MODEL_PARAMS = {
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

N_TRIALS = 50
CV_FOLDS = 5
SEED = 42
