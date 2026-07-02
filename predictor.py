import csv
import math
import urllib.request
import os
import random

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

class CustomMinMaxScaler:
    def __init__(self):
        self.mins = []
        self.maxs = []
        
    def fit(self, X):
        n_features = len(X[0])
        self.mins = [min(row[j] for row in X) for j in range(n_features)]
        self.maxs = [max(row[j] for row in X) for j in range(n_features)]
        
    def transform(self, X):
        X_scaled = []
        for row in X:
            scaled_row = []
            for j in range(len(row)):
                denom = self.maxs[j] - self.mins[j]
                val = (row[j] - self.mins[j]) / denom if denom > 0 else 0.0
                scaled_row.append(val)
            X_scaled.append(scaled_row)
        return X_scaled

    def transform_single(self, row):
        scaled_row = []
        for j in range(len(row)):
            denom = self.maxs[j] - self.mins[j]
            val = (row[j] - self.mins[j]) / denom if denom > 0 else 0.0
            scaled_row.append(val)
        return scaled_row

class CustomGaussianNB:
    def __init__(self):
        self.classes = []
        self.priors = {}
        self.means = {}
        self.vars = {}
        
    def fit(self, X, y):
        self.classes = list(set(y))
        n_samples = len(X)
        n_features = len(X[0])
        
        # Agrupar muestras por clase
        samples_by_class = {c: [] for c in self.classes}
        for features, label in zip(X, y):
            samples_by_class[label].append(features)
            
        # Calcular medias y varianzas
        for c in self.classes:
            class_samples = samples_by_class[c]
            n_class_samples = len(class_samples)
            self.priors[c] = n_class_samples / n_samples
            
            self.means[c] = []
            self.vars[c] = []
            
            # Para cada feature
            for j in range(n_features):
                mean_j = sum(row[j] for row in class_samples) / n_class_samples
                var_j = sum((row[j] - mean_j) ** 2 for row in class_samples) / n_class_samples
                
                self.means[c].append(mean_j)
                # Añadir var_smoothing para evitar varianza cero
                self.vars[c].append(var_j + 1e-9)

    def _calculate_likelihood(self, x, mean, var):
        # PDF normal
        exponent = math.exp(-((x - mean) ** 2) / (2 * var))
        return (1.0 / math.sqrt(2 * math.pi * var)) * exponent

    def predict_proba(self, x):
        log_posteriors = {}
        for c in self.classes:
            log_prior = math.log(self.priors[c])
            log_likelihood = 0.0
            for j in range(len(x)):
                mean = self.means[c][j]
                var = self.vars[c][j]
                likelihood = self._calculate_likelihood(x[j], mean, var)
                
                # Weighted Naive Bayes
                feat_name = FEATURE_ORDER[j]
                weight = FEATURE_WEIGHTS.get(feat_name, 1.0)
                
                # Impedir log de cero y multiplicar por el peso
                log_val = math.log(likelihood if likelihood > 0 else 1e-15)
                log_likelihood += weight * log_val
            log_posteriors[c] = log_prior + log_likelihood
            
        # Softmax
        max_log = max(log_posteriors.values())
        exp_posteriors = {c: math.exp(val - max_log) for c, val in log_posteriors.items()}
        sum_exp = sum(exp_posteriors.values())
        
        probs = {c: exp_posteriors[c] / sum_exp for c in self.classes}
        return probs

    def predict(self, X):
        preds = []
        for row in X:
            probs = self.predict_proba(row)
            best_class = max(probs, key=probs.get)
            preds.append(best_class)
        return preds

# Variables globales para guardar el modelo entrenado
_model = None
_scaler = None
_metrics = {}


def load_and_train_model():
    global _model, _scaler, _metrics
    
    # Asegurar descarga del dataset
    db_dir = os.path.dirname(DATASET_PATH)
    os.makedirs(db_dir, exist_ok=True)
    if not os.path.exists(DATASET_PATH):
        try:
            print("[PREDICTOR] Descargando dataset del proyecto desde GitHub...")
            urllib.request.urlretrieve(DATASET_URL, DATASET_PATH)
            print("[PREDICTOR] Dataset guardado localmente.")
        except Exception as e:
            print(f"[PREDICTOR] Error descargando dataset: {e}")
            return False
            
    # Cargar datos
    X = []
    y = []
    
    try:
        with open(DATASET_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            for row in reader:
                if not row or len(row) < 27:
                    continue
                # trabaja (Si/No) -> 1/0
                trabaja_str = row[24].strip().lower()
                trabaja_val = 1 if trabaja_str in ["si", "sí", "yes", "1"] else 0
                
                features = []
                for i in range(26):
                    if i == 24:
                        features.append(float(trabaja_val))
                    elif i == 23:  # tiempo_traslado_diario: acotar outliers
                        features.append(min(180.0, max(13.0, float(row[i]))))
                    elif i == 25:  # horas_trabajo_semana: acotar outliers
                        features.append(min(48.0, max(0.0, float(row[i]))))
                    else:
                        features.append(float(row[i]))
                        
                X.append(features)
                y.append(row[26].strip())
    except Exception as e:
        print(f"[PREDICTOR] Error leyendo dataset: {e}")
        return False

    # División estratificada 70-20-10
    class_indices = {}
    for idx, label in enumerate(y):
        if label not in class_indices:
            class_indices[label] = []
        class_indices[label].append(idx)
        
    train_indices = []
    val_indices = []
    test_indices = []
    
    random.seed(42)
    for label, indices in class_indices.items():
        shuffled = list(indices)
        random.shuffle(shuffled)
        
        n = len(shuffled)
        n_train = int(n * 0.70)
        n_val = int(n * 0.20)
        
        train_indices.extend(shuffled[:n_train])
        val_indices.extend(shuffled[n_train:n_train + n_val])
        test_indices.extend(shuffled[n_train + n_val:])
        
    X_train = [X[i] for i in train_indices]
    y_train = [y[i] for i in train_indices]
    
    X_test = [X[i] for i in test_indices]
    y_test = [y[i] for i in test_indices]

    # Ajustar scaler y transformar
    _scaler = CustomMinMaxScaler()
    _scaler.fit(X_train)
    
    X_train_scaled = _scaler.transform(X_train)
    X_test_scaled = _scaler.transform(X_test)
    
    # Entrenar Naive Bayes
    _model = CustomGaussianNB()
    _model.fit(X_train_scaled, y_train)
    
    # Evaluar métricas
    y_pred = _model.predict(X_test_scaled)
    
    correct = sum(1 for p, r in zip(y_pred, y_test) if p == r)
    accuracy = correct / len(y_test) if len(y_test) > 0 else 0.0
    
    classes_ordered = ['Excelente', 'Bueno', 'Regular', 'Deficiente']
    confusion = {r: {p: 0 for p in classes_ordered} for r in classes_ordered}
    for p, r in zip(y_pred, y_test):
        if r in confusion and p in confusion[r]:
            confusion[r][p] += 1
            
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
        "accuracy": round(accuracy, 4),
        "confusion_matrix": confusion,
        "classification_report": report
    }
    
    print(f"[PREDICTOR] Naive Bayes entrenado con éxito. Accuracy: {accuracy:.4f}")
    return True

def predict_performance(features_dict):
    global _model, _scaler, _metrics
    
    if _model is None or _scaler is None:
        success = load_and_train_model()
        if not success:
            raise Exception("No se pudo cargar ni entrenar el modelo.")
            
    # Ordenar las características
    ordered_features = []
    for col in FEATURE_ORDER:
        val = features_dict.get(col, 0.0)
        # Sanitizar booleanos o strings
        if isinstance(val, bool):
            val = 1.0 if val else 0.0
        elif isinstance(val, str):
            if val.lower() in ["si", "sí", "yes", "1", "trabaja"]:
                val = 1.0
            else:
                val = 0.0
        
        # Aplicar Capping (Acotado) de variables contextuales
        if col == "tiempo_traslado_diario":
            val = min(180.0, max(13.0, float(val)))
        elif col == "horas_trabajo_semana":
            val = min(48.0, max(0.0, float(val)))
            
        ordered_features.append(float(val))
        
    # Escalar
    scaled_features = _scaler.transform_single(ordered_features)
    
    # Predecir
    probs = _model.predict_proba(scaled_features)
    predicted_class = max(probs, key=probs.get)
    
    return {
        "predicted_class": predicted_class,
        "probabilities": probs,
        "metrics": _metrics,
        "features": features_dict
    }

# Entrenar de inmediato al importar
load_and_train_model()
