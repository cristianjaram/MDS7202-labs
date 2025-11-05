import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score
import glob

def create_folders(**kwargs):
    """
    Crea una carpeta con la fecha de ejecución y las subcarpetas necesarias.
    """
    # Obtener la fecha de ejecución
    ds = kwargs['ds']  # formato: YYYY-MM-DD
    
    # Crear directorio principal con la fecha
    base_path = f"/tmp/{ds}"
    os.makedirs(base_path, exist_ok=True)
    
    # Crear subcarpetas
    subdirs = ['raw', 'preprocessed', 'splits', 'models']
    for subdir in subdirs:
        os.makedirs(os.path.join(base_path, subdir), exist_ok=True)
    
    print(f"Carpetas creadas en: {base_path}")
    return base_path

def load_and_merge(**kwargs):
    """
    Lee los archivos data_1.csv y data_2.csv (si está disponible) desde la carpeta raw,
    los concatena y guarda el resultado en la carpeta preprocessed.
    """
    ds = kwargs['ds']
    base_path = f"/tmp/{ds}"
    raw_path = os.path.join(base_path, 'raw')
    preprocessed_path = os.path.join(base_path, 'preprocessed')
    
    dataframes = []
    
    # Intentar leer data_1.csv
    data1_path = os.path.join(raw_path, 'data_1.csv')
    if os.path.exists(data1_path):
        df1 = pd.read_csv(data1_path)
        dataframes.append(df1)
        print(f"Cargado data_1.csv: {len(df1)} filas")
    
    # Intentar leer data_2.csv
    data2_path = os.path.join(raw_path, 'data_2.csv')
    if os.path.exists(data2_path):
        df2 = pd.read_csv(data2_path)
        dataframes.append(df2)
        print(f"Cargado data_2.csv: {len(df2)} filas")
    
    # Concatenar los dataframes disponibles
    if dataframes:
        merged_df = pd.concat(dataframes, ignore_index=True)
        
        output_path = os.path.join(preprocessed_path, 'merged_data.csv')
        merged_df.to_csv(output_path, index=False)
        
        print(f"Dataset concatenado guardado: {len(merged_df)} filas en {output_path}")
    else:
        raise FileNotFoundError("No se encontraron archivos de datos en la carpeta raw")

def split_data(**kwargs):
    """
    Lee la data guardada en preprocessed y realiza un hold out.
    Crea conjuntos de entrenamiento y prueba (80-20).
    """
    ds = kwargs['ds']
    base_path = f"/tmp/{ds}"
    preprocessed_path = os.path.join(base_path, 'preprocessed')
    splits_path = os.path.join(base_path, 'splits')
    
    # Leer el dataset concatenado
    data_path = os.path.join(preprocessed_path, 'merged_data.csv')
    df = pd.read_csv(data_path)
    
    # Separar características y variable objetivo
    X = df.drop('HiringDecision', axis=1)
    y = df['HiringDecision']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=0.2, 
        random_state=42, 
        stratify=y
    )
    
    # Guardar los conjuntos de datos
    train_df = pd.concat([X_train, y_train], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)
    
    train_path = os.path.join(splits_path, 'train.csv')
    test_path = os.path.join(splits_path, 'test.csv')
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"Conjuntos guardados - Train: {len(train_df)} filas, Test: {len(test_df)} filas")

def train_model(model, model_name, **kwargs):
    """
    Entrena un modelo específico con preprocesamiento incluido.
    
    Args:
        model: Modelo de clasificación a entrenar
        model_name: Nombre identificativo del modelo
    """
    ds = kwargs['ds']
    base_path = f"/tmp/{ds}"
    splits_path = os.path.join(base_path, 'splits')
    models_path = os.path.join(base_path, 'models')
    
    train_path = os.path.join(splits_path, 'train.csv')
    train_df = pd.read_csv(train_path)
    
    X_train = train_df.drop('HiringDecision', axis=1)
    y_train = train_df['HiringDecision']
    
    numeric_features = X_train.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = X_train.select_dtypes(include=['object']).columns.tolist()
    
    # Crear preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', 'passthrough', categorical_features)  # Las categóricas ya están codificadas
        ],
        remainder='passthrough'
    )
    
    # Crear pipeline completo
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])
    
    pipeline.fit(X_train, y_train)
    
    # Guardar el modelo entrenado
    model_filename = f"{model_name}_pipeline.joblib"
    model_path = os.path.join(models_path, model_filename)
    joblib.dump(pipeline, model_path)
    
    print(f"Modelo {model_name} entrenado y guardado en: {model_path}")

def evaluate_models(**kwargs):
    """
    Evalúa todos los modelos entrenados, selecciona el mejor y lo guarda.
    """
    ds = kwargs['ds']
    base_path = f"/tmp/{ds}"
    splits_path = os.path.join(base_path, 'splits')
    models_path = os.path.join(base_path, 'models')
    
    # Leer conjunto de prueba
    test_path = os.path.join(splits_path, 'test.csv')
    test_df = pd.read_csv(test_path)
    
    X_test = test_df.drop('HiringDecision', axis=1)
    y_test = test_df['HiringDecision']
    
    # Encontrar todos los modelos entrenados
    model_files = glob.glob(os.path.join(models_path, '*_pipeline.joblib'))
    
    best_model = None
    best_accuracy = 0
    best_model_name = ""
    model_results = {}
    
    # Evaluar cada modelo
    for model_file in model_files:
        # Extraer nombre del modelo
        model_name = os.path.basename(model_file).replace('_pipeline.joblib', '')
        
        # Cargar modelo
        pipeline = joblib.load(model_file)
        
        # Hacer predicciones
        y_pred = pipeline.predict(X_test)
        
        # Calcular accuracy
        accuracy = accuracy_score(y_test, y_pred)
        model_results[model_name] = accuracy
        
        print(f"Modelo {model_name}: Accuracy = {accuracy:.4f}")
        
        # Actualizar mejor modelo si es necesario
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model = pipeline
            best_model_name = model_name
    
    if best_model is not None:
        best_model_path = os.path.join(models_path, 'best_model.joblib')
        joblib.dump(best_model, best_model_path)
        
        print(f"\n=== RESULTADOS FINALES ===")
        print(f"Mejor modelo: {best_model_name}")
        print(f"Mejor accuracy: {best_accuracy:.4f}")
        print(f"Modelo guardado en: {best_model_path}")
        
        # Mostrar comparación de todos los modelos
        print(f"\nComparación de modelos:")
        for model_name, accuracy in model_results.items():
            print(f"  {model_name}: {accuracy:.4f}")
    else:
        raise ValueError("No se encontraron modelos para evaluar")