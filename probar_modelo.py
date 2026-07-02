import sqlite3
import os
import sys

# Ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "upao.db")

def seed_database():
    print("[BASE DE DATOS] Inicializando estudiantes de prueba...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Crear estudiante de bajo rendimiento (000999999)
    try:
        cursor.execute("SELECT id FROM estudiantes WHERE codigo = '000999999'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute("""
                INSERT INTO estudiantes (codigo, nombres, apellidos, password, carrera, ciclo_actual, trabaja, horas_trabajo_semana, tiempo_traslado_diario)
                VALUES ('000999999', 'JUAN ALBERTO', 'PEREZ GOMEZ', 'prueba1234', 'INGENIERÍA DE SISTEMAS E INTELIGENCIA ARTIFICIAL', 4, 1, 30, 120)
            """)
            student_id = cursor.lastrowid
            
            # Cargar historial con notas bajas y repitencias
            historial = [
                (1, '2024-10', 11.5, 4, 'aprobado'),
                (2, '2024-10', 14.0, 2, 'aprobado'),
                (3, '2024-10', 10.5, 4, 'aprobado'),
                (4, '2024-10', 12.0, 2, 'aprobado'),
                (5, '2024-10', 8.0, 4, 'desaprobado'),
                (6, '2024-10', 7.0, 4, 'desaprobado'),
                (5, '2024-20', 11.0, 4, 'aprobado'),
                (6, '2024-20', 9.5, 4, 'desaprobado'),
                (7, '2024-20', 10.5, 4, 'aprobado'),
                (8, '2024-20', 11.5, 3, 'aprobado'),
                (9, '2024-20', 12.0, 2, 'aprobado'),
                (10, '2024-20', 8.0, 4, 'desaprobado'),
                (6, '2025-10', 11.5, 4, 'aprobado'),
                (10, '2025-10', 10.5, 4, 'aprobado'),
                (11, '2025-10', 7.5, 4, 'desaprobado'),
                (12, '2025-10', 6.0, 4, 'desaprobado'),
                (13, '2025-10', 10.5, 4, 'aprobado'),
                (11, '2025-20', 11.0, 4, 'aprobado'),
                (12, '2025-20', 9.0, 4, 'desaprobado'),
                (14, '2025-20', 10.5, 4, 'aprobado'),
                (15, '2025-20', 12.0, 2, 'aprobado'),
                (16, '2025-20', 7.5, 4, 'desaprobado')
            ]
            for curso_id, periodo, nota, creditos, estado in historial:
                cursor.execute("""
                    INSERT INTO historial (estudiante_id, curso_id, periodo, nota, creditos_hora, estado)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (student_id, curso_id, periodo, nota, creditos, estado))
            print("  -> Estudiante 000999999 registrado correctamente.")
        else:
            print("  -> Estudiante 000999999 ya existía.")
    except Exception as e:
        print("  -> Error al registrar 000999999:", e)

    # 2. Crear estudiante de alto rendimiento (000888888)
    try:
        cursor.execute("SELECT id FROM estudiantes WHERE codigo = '000888888'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute("""
                INSERT INTO estudiantes (codigo, nombres, apellidos, password, carrera, ciclo_actual, trabaja, horas_trabajo_semana, tiempo_traslado_diario)
                VALUES ('000888888', 'MARTA', 'GUTIERREZ LOPEZ', 'buena123', 'INGENIERÍA DE SISTEMAS E INTELIGENCIA ARTIFICIAL', 7, 0, 0, 30)
            """)
            student_id = cursor.lastrowid
            
            # Cargar historial de puras notas altas y 0 repitencias
            historial = [
                (1, '2023-10', 17.5, 4, 'aprobado'),
                (2, '2023-10', 18.0, 2, 'aprobado'),
                (3, '2023-10', 16.5, 4, 'aprobado'),
                (4, '2023-10', 17.0, 2, 'aprobado'),
                (5, '2023-10', 17.5, 4, 'aprobado'),
                (6, '2023-10', 16.0, 4, 'aprobado'),
                (1, '2024-20', 18.0, 4, 'aprobado'),
                (2, '2024-20', 17.5, 2, 'aprobado'),
                (3, '2024-20', 16.5, 4, 'aprobado'),
                (4, '2024-20', 17.0, 2, 'aprobado'),
                (5, '2024-20', 18.0, 4, 'aprobado'),
                (6, '2024-20', 16.5, 4, 'aprobado'),
            ]
            for curso_id, periodo, nota, creditos, estado in historial:
                cursor.execute("""
                    INSERT INTO historial (estudiante_id, curso_id, periodo, nota, creditos_hora, estado)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (student_id, curso_id, periodo, nota, creditos, estado))
            print("  -> Estudiante 000888888 registrado correctamente.")
        else:
            print("  -> Estudiante 000888888 ya existía.")
    except Exception as e:
        print("  -> Error al registrar 000888888:", e)

    conn.commit()
    conn.close()

def run_predictions():
    print("\n[PREDICTOR] Cargando modelo Naive Bayes y ejecutando pruebas de predicción...")
    import predictor
    
    # Lista de estudiantes para evaluar
    students = ["000999999", "000888888", "000287948"]
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    for codigo in students:
        cur.execute("SELECT id, ciclo_actual, trabaja, horas_trabajo_semana, tiempo_traslado_diario, nombres FROM estudiantes WHERE codigo = ?", (codigo,))
        row = cur.fetchone()
        if not row:
            continue
        student_id, ciclo_actual, trabaja, horas_trabajo, tiempo_traslado, nombres = row
        
        # Obtener promedio acumulado
        cur.execute("""
            SELECT AVG(nota) FROM historial
            WHERE estudiante_id = ? AND nota IS NOT NULL AND estado = 'aprobado'
        """, (student_id,))
        promedio = cur.fetchone()[0] or 12.0
        
        # Obtener créditos aprobados
        cur.execute("SELECT SUM(creditos_hora) FROM historial WHERE estudiante_id = ? AND estado = 'aprobado'", (student_id,))
        cred_aprob = cur.fetchone()[0] or 0.0
        
        # Obtener créditos desaprobados
        cur.execute("SELECT SUM(creditos_hora) FROM historial WHERE estudiante_id = ? AND estado = 'desaprobado'", (student_id,))
        cred_desap = cur.fetchone()[0] or 0.0
        
        # Número de desaprobaciones
        cur.execute("SELECT COUNT(*) FROM historial WHERE estudiante_id = ? AND estado = 'desaprobado'", (student_id,))
        num_desap = cur.fetchone()[0]
        
        # Cursos retirados
        cur.execute("SELECT COUNT(*) FROM historial WHERE estudiante_id = ? AND estado = 'retirado'", (student_id,))
        retirados = cur.fetchone()[0]
        
        # Simulamos que el estudiante tiene seleccionadas las secciones 1 a 10
        # Esto le da un horario muy cargado
        seccion_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        features = {
            "promedio_acumulado": promedio,
            "promedio_ultimo_ciclo": promedio,
            "creditos_aprobados": cred_aprob,
            "creditos_desaprobados": cred_desap,
            "numero_desaprobaciones": float(num_desap),
            "cursos_retirados": float(retirados),
            "ciclo_actual": float(ciclo_actual),
            "creditos_matriculados": 20.0,
            "cantidad_cursos": 5.0,
            "cantidad_cursos_repitencia": 0.0,
            "cantidad_cursos_dificiles": 1.0,
            "hora_inicio_mas_temprana": 7.0, # 7:00 am
            "dias_7am": 2.0,
            "hora_fin_mas_tardia": 22.0,     # Clases de noche
            "dias_nocturnos": 3.0,
            "dias_con_clases": 5.0,
            "horas_consecutivas_maximas": 4.0,
            "horas_muertas_semana": 2.0,
            "max_horas_en_campus_dia": 7.0,
            "indice_balance_horario": 3.5,
            "indice_exigencia_docentes": 3.8,
            "indice_dificultad_docente_curso": 3.8,
            "cantidad_docentes_exigentes": 2.0,
            "tiempo_traslado_diario": float(tiempo_traslado),
            "trabaja": float(trabaja),
            "horas_trabajo_semana": float(horas_trabajo)
        }
        
        res = predictor.predict_performance(features)
        print(f"\nEstudiante: {nombres} (Código: {codigo})")
        print(f"  * Promedio Acumulado: {promedio:.2f}")
        print(f"  * Horas de Trabajo: {horas_trabajo} hrs | Traslado: {tiempo_traslado} min")
        print(f"  * Resultado Predicho: {res['predicted_class']}")
        print("  * Probabilidades:")
        for c, prob in res["probabilities"].items():
            print(f"    - {c}: {prob*100:.2f}%")
            
    conn.close()

if __name__ == "__main__":
    seed_database()
    run_predictions()
