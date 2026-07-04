import os
import csv
import math
import urllib.request
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Ruta del dataset local
DATASET_URL = "https://raw.githubusercontent.com/alvarol30/DATASET_AE/refs/heads/main/DATASET_PROYECTOAE.csv"
DATASET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "DATASET_PROYECTOAE.csv")

# Definición del orden de las características en el dataset
FEATURE_ORDER = [
    "promedio_acumulado",
    "promedio_ultimo_ciclo",
    "creditos_aprobados",
    "creditos_desaprobados",
    "numero_desaprobaciones",
    "cursos_retirados",
    "ciclo_actual",
    "creditos_matriculados",
    "cantidad_cursos",
    "cantidad_cursos_repitencia",
    "cantidad_cursos_dificiles",
    "hora_inicio_mas_temprana",
    "dias_7am",
    "hora_fin_mas_tardia",
    "dias_nocturnos",
    "dias_con_clases",
    "horas_consecutivas_maximas",
    "horas_muertas_semana",
    "max_horas_en_campus_dia",
    "indice_balance_horario",
    "indice_exigencia_docentes",
    "indice_dificultad_docente_curso",
    "cantidad_docentes_exigentes",
    "tiempo_traslado_diario",
    "trabaja",
    "horas_trabajo_semana"
]

# Ponderaciones de características para Weighted Naive Bayes
# Suaviza el peso de los promedios e incrementa el impacto del horario y el trabajo
FEATURE_WEIGHTS = {
    "promedio_acumulado": 0.6,
    "promedio_ultimo_ciclo": 0.6,
    "creditos_aprobados": 0.6,
    "creditos_desaprobados": 0.6,
    "numero_desaprobaciones": 0.6,
    "cursos_retirados": 0.6,
    "ciclo_actual": 0.8,
    
    # Carga académica
    "creditos_matriculados": 1.0,
    "cantidad_cursos": 1.0,
    "cantidad_cursos_repitencia": 1.2,
    "cantidad_cursos_dificiles": 1.1,
    
    # Horario
    "hora_inicio_mas_temprana": 1.0,
    "dias_7am": 1.0,
    "hora_fin_mas_tardia": 1.0,
    "dias_nocturnos": 1.0,
    "dias_con_clases": 1.0,
    "horas_consecutivas_maximas": 1.2,
    "horas_muertas_semana": 1.5,
    "max_horas_en_campus_dia": 1.2,
    "indice_balance_horario": 1.0,
    
    # Docentes
    "indice_exigencia_docentes": 1.2,
    "indice_dificultad_docente_curso": 1.2,
    "cantidad_docentes_exigentes": 1.2,
    
    # Contexto personal
    "tiempo_traslado_diario": 1.5,
    "trabaja": 1.2,
    "horas_trabajo_semana": 1.5
}

_model = None
_scaler = None
_metrics = {}

def load_and_train_model():
    global _model, _scaler, _metrics
    
    db_dir = os.path.dirname(DATASET_PATH)
    os.makedirs(db_dir, exist_ok=True)
    if not os.path.exists(DATASET_PATH):
        try:
            print("[PREDICTOR] Descargando dataset del proyecto...")
            urllib.request.urlretrieve(DATASET_URL, DATASET_PATH)
        except Exception as e:
            print(f"[PREDICTOR] Error descargando dataset: {e}")
            return False
            
    try:
        # Cargar datos con pandas
        df = pd.read_csv(DATASET_PATH)
        df["trabaja"] = df["trabaja"].map({
            "No": 0,
            "Si": 1,
            "sí": 1,
            "yes": 1
        }).fillna(0)
        
        # Aplicar Capping (Acotado) en el entrenamiento
        df["tiempo_traslado_diario"] = df["tiempo_traslado_diario"].clip(13.0, 180.0)
        df["horas_trabajo_semana"] = df["horas_trabajo_semana"].clip(0.0, 48.0)
        
        X = df[FEATURE_ORDER]
        y = df["resultado_ciclo"]
        
        # Escalador
        _scaler = MinMaxScaler()
        X_scaled = _scaler.fit_transform(X)
        
        # División 70-20-10 (Como en proyectoae (2).py)
        X_train, X_temp, y_train, y_temp = train_test_split(
            X_scaled, y, test_size=0.30, random_state=42, stratify=y
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=1/3, random_state=42, stratify=y_temp
        )
        
        # Entrenar Naive Bayes de scikit-learn
        _model = GaussianNB()
        _model.fit(X_train, y_train)
        
        # Evaluación usando nuestra predict_proba ponderada para coherencia de métricas
        y_pred = []
        for row in X_test:
            probs = predict_proba_weighted(row)
            best_class = max(probs, key=probs.get)
            y_pred.append(best_class)
            
        acc = accuracy_score(y_test, y_pred)
        
        classes_ordered = ['Excelente', 'Bueno', 'Regular', 'Deficiente']
        confusion = {r: {p: 0 for p in classes_ordered} for r in classes_ordered}
        for i, r in enumerate(y_test):
            p = y_pred[i]
            if r in confusion and p in confusion[r]:
                confusion[r][p] += 1
                
        # Construir reporte
        report = {}
        for c in classes_ordered:
            tp = confusion[c][c]
            fp = sum(confusion[r][c] for r in classes_ordered if r != c)
            fn = sum(confusion[c][p] for p in classes_ordered if p != c)
            
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            
            report[c] = {
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4)
            }
            
        _metrics = {
            "accuracy": round(acc, 4),
            "confusion_matrix": confusion,
            "classification_report": report
        }
        
        print(f"[PREDICTOR] Modelo scikit-learn NB + pesos entrenado. Accuracy: {acc:.4f}")
        return True
    except Exception as e:
        print(f"[PREDICTOR] Error entrenando modelo: {e}")
        return False

def predict_proba_weighted(scaled_features):
    global _model
    log_posteriors = {}
    
    # Calcular probabilidades usando la fórmula Gaussiana con las medias/varianzas entrenadas de sklearn
    for idx, c in enumerate(_model.classes_):
        log_prior = math.log(_model.class_prior_[idx])
        log_likelihood = 0.0
        
        means = _model.theta_[idx]
        variances = _model.var_[idx]
        
        for j in range(len(scaled_features)):
            mean = means[j]
            var = variances[j]
            
            # PDF normal
            exponent = math.exp(-((scaled_features[j] - mean) ** 2) / (2 * var))
            likelihood = (1.0 / math.sqrt(2 * math.pi * var)) * exponent
            
            # Weighted Naive Bayes
            feat_name = FEATURE_ORDER[j]
            weight = FEATURE_WEIGHTS.get(feat_name, 1.0)
            
            log_val = math.log(likelihood if likelihood > 0 else 1e-15)
            log_likelihood += weight * log_val
            
        log_posteriors[c] = log_prior + log_likelihood
        
    # Softmax
    max_log = max(log_posteriors.values())
    exp_posteriors = {c: math.exp(val - max_log) for c, val in log_posteriors.items()}
    sum_exp = sum(exp_posteriors.values())
    
    return {c: exp_posteriors[c] / sum_exp for c in _model.classes_}

def predict_performance(features_dict):
    global _model, _scaler, _metrics
    
    if _model is None or _scaler is None:
        success = load_and_train_model()
        if not success:
            raise Exception("No se pudo cargar ni entrenar el modelo.")
            
    ordered_features = []
    for col in FEATURE_ORDER:
        val = features_dict.get(col, 0.0)
        if isinstance(val, bool):
            val = 1.0 if val else 0.0
        elif isinstance(val, str):
            if val.lower() in ["si", "sí", "yes", "1", "trabaja"]:
                val = 1.0
            else:
                val = 0.0
                
        # Capping
        if col == "tiempo_traslado_diario":
            val = min(180.0, max(13.0, float(val)))
        elif col == "horas_trabajo_semana":
            val = min(48.0, max(0.0, float(val)))
            
        ordered_features.append(float(val))
        
    # Escalar
    df_features = pd.DataFrame([ordered_features], columns=FEATURE_ORDER)
    scaled_features = _scaler.transform(df_features)[0]
    
    # Predecir usando Weighted Gaussian NB
    probs = predict_proba_weighted(scaled_features)
    predicted_class = max(probs, key=probs.get)
    
    return {
        "predicted_class": predicted_class,
        "probabilities": probs,
        "metrics": _metrics,
        "features": features_dict
    }

# Cargar al importar
load_and_train_model()
