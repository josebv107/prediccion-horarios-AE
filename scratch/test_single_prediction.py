import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import predictor
from predictor import FEATURE_ORDER

# Datos del estudiante 000555555 base
features_base = {
    'promedio_acumulado': 12.0,
    'promedio_ultimo_ciclo': 11.5,
    'creditos_aprobados': 120,
    'creditos_desaprobados': 25,
    'numero_desaprobaciones': 6,
    'cursos_retirados': 2,
    'ciclo_actual': 8,
    'creditos_matriculados': 22,
    'cantidad_cursos': 6,
    'cantidad_cursos_repitencia': 2,
    'cantidad_cursos_dificiles': 3,
    'hora_inicio_mas_temprana': 7,
    'dias_7am': 3,
    'hora_fin_mas_tardia': 22,
    'dias_nocturnos': 2,
    'dias_con_clases': 5,
    'horas_consecutivas_maximas': 6,
    'horas_muertas_semana': 8,
    'max_horas_en_campus_dia': 10,
    'indice_balance_horario': 0.4,
    'indice_exigencia_docentes': 0.8,
    'indice_dificultad_docente_curso': 0.7,
    'cantidad_docentes_exigentes': 3,
    'tiempo_traslado_diario': 60,
    'trabaja': "No",
    'horas_trabajo_semana': 0
}

print("\n--- TEST: NO TRABAJA (0 horas) ---")
res1 = predictor.predict_performance(features_base)
for k, v in res1["probabilities"].items():
    print(f"{k}: {v*100:.2f}%")

print("\n--- TEST: TRABAJA (30 horas) ---")
features_trab = features_base.copy()
features_trab["trabaja"] = "Si"
features_trab["horas_trabajo_semana"] = 30
res2 = predictor.predict_performance(features_trab)
for k, v in res2["probabilities"].items():
    print(f"{k}: {v*100:.2f}%")

print("\n--- TEST: TRABAJA (48 horas) ---")
features_trab48 = features_base.copy()
features_trab48["trabaja"] = "Si"
features_trab48["horas_trabajo_semana"] = 48
res3 = predictor.predict_performance(features_trab48)
for k, v in res3["probabilities"].items():
    print(f"{k}: {v*100:.2f}%")
