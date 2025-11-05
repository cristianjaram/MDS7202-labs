import os
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
import joblib
import gradio as gr


def create_folders(**kwargs):
    exec_date = kwargs.get('ds')  # fecha de ejecución del DAG
    base_path = os.path.join(os.getcwd(), 'data', exec_date)

    subfolders = ['raw', 'splits', 'models']
    for folder in subfolders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)

    print(f"Carpetas creadas en: {base_path}")
    return base_path



def split_data(base_path, random_state=42):
    raw_path = os.path.join(base_path, 'raw', 'data_1.csv')
    df = pd.read_csv(raw_path)

    X = df.drop('HiringDecision', axis=1)
    y = df['HiringDecision']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=random_state
    )

    train = pd.concat([X_train, y_train], axis=1)
    test = pd.concat([X_test, y_test], axis=1)

    splits_path = os.path.join(base_path, 'splits')
    train.to_csv(os.path.join(splits_path, 'train.csv'), index=False)
    test.to_csv(os.path.join(splits_path, 'test.csv'), index=False)

    print("Datos divididos y guardados exitosamente.")



def preprocess_and_train(base_path):
    """Entrena un pipeline con RandomForest y guarda el modelo."""
    splits_path = os.path.join(base_path, 'splits')
    train = pd.read_csv(os.path.join(splits_path, 'train.csv'))
    test = pd.read_csv(os.path.join(splits_path, 'test.csv'))

    X_train = train.drop('HiringDecision', axis=1)
    y_train = train['HiringDecision']
    X_test = test.drop('HiringDecision', axis=1)
    y_test = test['HiringDecision']

    # Identificar tipos de variables
    num_features = [
        'Age', 'ExperienceYears', 'PreviousCompanies',
        'DistanceFromCompany', 'InterviewScore',
        'SkillScore', 'PersonalityScore'
    ]
    cat_features = ['Gender', 'EducationLevel', 'RecruitmentStrategy']

    # Preprocesamiento
    numeric_transformer = Pipeline(steps=[
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, num_features),
            ('cat', categorical_transformer, cat_features)
        ]
    )

    # Modelo
    model = RandomForestClassifier(n_estimators=100, random_state=42)

    # Pipeline completo
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', model)
    ])

    # Entrenamiento
    pipeline.fit(X_train, y_train)

    # Evaluación
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, pos_label=1)

    print(f"Accuracy: {acc:.4f}")
    print(f"F1-score (Contratado): {f1:.4f}")

    # Guardar modelo
    models_path = os.path.join(base_path, 'models')
    model_path = os.path.join(models_path, 'hiring_model.joblib')
    joblib.dump(pipeline, model_path)

    print(f"Modelo guardado en: {model_path}")

    return model_path



def predict(file, model_path):
    """Predice si un candidato será contratado o no."""
    pipeline = joblib.load(model_path)
    input_data = pd.read_json(file)
    predictions = pipeline.predict(input_data)
    labels = ["No contratado" if pred == 0 else "Contratado" for pred in predictions]
    return {'Predicción': labels[0]}


def gradio_interface(model_path):
    """Lanza la interfaz de Gradio."""
    interface = gr.Interface(
        fn=lambda file: predict(file, model_path),
        inputs=gr.File(label="Sube un archivo JSON"),
        outputs="json",
        title="Hiring Decision Prediction",
        description="Sube un archivo JSON con las características de entrada para predecir si Vale será contratada o no."
    )
    interface.launch(share=True)