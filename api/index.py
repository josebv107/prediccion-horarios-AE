import os
import sys
import sqlite3
import shutil
from flask import Flask, request, jsonify

# Agregar el directorio raíz al path de Python para importar predictor.py y server.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import predictor
import server

app = Flask(__name__)

# Rutas de Base de Datos
DEPLOYED_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "upao.db")
TMP_DB = "/tmp/upao.db"

def get_db_connection():
    # En Vercel el entorno es de solo lectura. Copiamos la plantilla db/upao.db
    # a la ruta temporal /tmp para poder guardar/reiniciar las simulaciones.
    if os.environ.get("VERCEL"):
        if not os.path.exists(TMP_DB):
            os.makedirs(os.path.dirname(TMP_DB), exist_ok=True)
            shutil.copy2(DEPLOYED_DB, TMP_DB)
        return sqlite3.connect(TMP_DB)
    return sqlite3.connect(DEPLOYED_DB)

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json or {}
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombres, apellidos, carrera, ciclo_actual FROM estudiantes WHERE codigo = ? AND password = ?", (username, password))
        student = cursor.fetchone()
        conn.close()
        
        if student:
            return jsonify({
                "success": True,
                "student": {
                    "id": student[0],
                    "codigo": username,
                    "nombres": student[1],
                    "apellidos": student[2],
                    "carrera": student[3],
                    "ciclo_actual": student[4]
                }
            })
        else:
            return jsonify({"success": False, "message": "Código o contraseña incorrectos"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/student-info', methods=['GET'])
def student_info():
    codigo = request.args.get('codigo')
    if not codigo:
        return jsonify({"success": False, "message": "Código de estudiante requerido"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombres, apellidos, carrera, ciclo_actual FROM estudiantes WHERE codigo = ?", (codigo,))
        student = cursor.fetchone()
        
        if not student:
            conn.close()
            return jsonify({"success": False, "message": "Estudiante no encontrado"}), 404
            
        student_id = student[0]
        cursor.execute("""
            SELECT COUNT(*), SUM(h.nota * h.creditos_hora), SUM(h.creditos_hora)
            FROM historial h
            WHERE h.estudiante_id = ? AND h.estado = 'aprobado'
        """, (student_id,))
        stats = cursor.fetchone()
        conn.close()
        
        total_cursos = stats[0] or 0
        suma_puntos = stats[1] or 0
        total_creditos = stats[2] or 0
        promedio = round(suma_puntos / total_creditos, 2) if total_creditos > 0 else 0.0
        
        return jsonify({
            "success": True,
            "student": {
                "id": student_id,
                "codigo": codigo,
                "nombres": student[1],
                "apellidos": student[2],
                "carrera": student[3],
                "ciclo_actual": student[4],
                "stats": {
                    "creditos_aprobados": total_creditos,
                    "promedio_ponderado": promedio
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/eligible-courses', methods=['GET'])
def eligible_courses():
    codigo = request.args.get('codigo')
    if not codigo:
        return jsonify({"success": False, "message": "Código de estudiante requerido"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM estudiantes WHERE codigo = ?", (codigo,))
        student_row = cursor.fetchone()
        if not student_row:
            conn.close()
            return jsonify({"success": False, "message": "Estudiante no encontrado"}), 404
        student_id = student_row[0]
        
        # Obtener cursos elegibles hasta ciclo 5 que NO estén aprobados
        cursor.execute("""
            SELECT c.id, c.codigo, c.nombre, c.creditos, c.ciclo_malla, c.dificultad
            FROM cursos c
            WHERE c.ciclo_malla <= 5
              AND c.id NOT IN (
                  SELECT h.curso_id 
                  FROM historial h 
                  WHERE h.estudiante_id = ? AND h.estado = 'aprobado'
              )
            ORDER BY c.ciclo_malla ASC, c.codigo ASC
        """, (student_id,))
        courses_rows = cursor.fetchall()
        eligible_list = []
        
        for crow in courses_rows:
            cid, c_cod, c_nom, c_cred, c_ciclo, c_dif = crow
            
            cursor.execute("""
                SELECT estado FROM historial 
                WHERE estudiante_id = ? AND curso_id = ?
                ORDER BY id DESC LIMIT 1
            """, (student_id, cid))
            hist_status = cursor.fetchone()
            status_label = "regular"
            if hist_status and hist_status[0] == "desaprobado":
                status_label = "pendiente"
                
            cursor.execute("""
                SELECT s.id, s.liga, s.tipo, s.nrc, s.secc, s.capacidad, s.matriculados, s.cerrado, d.nombres, d.indice_exigencia
                FROM secciones s
                LEFT JOIN docentes d ON s.docente_id = d.id
                WHERE s.curso_id = ? AND s.periodo = '2026-10'
            """, (cid,))
            sec_rows = cursor.fetchall()
            sections = []
            
            for srow in sec_rows:
                sid, liga, tipo, nrc, secc, capa, matric, cerrado, doc_nombres, doc_exig = srow
                
                cursor.execute("""
                    SELECT dia, hora_ini, hora_fin, aula, pabellon
                    FROM horarios
                    WHERE seccion_id = ?
                """, (sid,))
                hor_rows = cursor.fetchall()
                horarios = []
                for hrow in hor_rows:
                    horarios.append({
                        "dia": hrow[0],
                        "hora_ini": hrow[1],
                        "hora_fin": hrow[2],
                        "aula": hrow[3],
                        "pabellon": hrow[4]
                    })
                    
                sections.append({
                    "id": sid,
                    "liga": liga,
                    "tipo": tipo,
                    "nrc": nrc,
                    "secc": secc,
                    "capacidad": capa,
                    "matriculados": matric,
                    "cerrado": cerrado,
                    "docente": doc_nombres or "Por Designar",
                    "docente_exigencia": doc_exig or 3.5,
                    "horarios": horarios
                })
                
            eligible_list.append({
                "id": cid,
                "codigo": c_cod,
                "nombre": c_nom,
                "creditos": c_cred,
                "ciclo_malla": c_ciclo,
                "dificultad": c_dif,
                "estado": status_label,
                "secciones": sections
            })
            
        cursor.execute("SELECT seccion_id FROM matricula WHERE estudiante_id = ? AND periodo = '2026-10'", (student_id,))
        enrolled_section_ids = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({
            "success": True,
            "courses": eligible_list,
            "enrolled_section_ids": enrolled_section_ids
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/enroll', methods=['POST'])
def enroll():
    try:
        data = request.json or {}
        codigo = data.get('codigo')
        seccion_ids = data.get('seccion_ids', [])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM estudiantes WHERE codigo = ?", (codigo,))
        student_row = cursor.fetchone()
        if not student_row:
            conn.close()
            return jsonify({"success": False, "message": "Estudiante no encontrado"}), 404
        student_id = student_row[0]
        
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("DELETE FROM matricula WHERE estudiante_id = ? AND periodo = '2026-10'", (student_id,))
        cursor.execute("DELETE FROM historial WHERE estudiante_id = ? AND periodo = '2026-10'", (student_id,))
        
        inserted_courses = set()
        for sec_id in seccion_ids:
            cursor.execute("INSERT INTO matricula (estudiante_id, seccion_id, periodo) VALUES (?, ?, '2026-10')", (student_id, sec_id))
            
            cursor.execute("""
                SELECT c.id, c.creditos 
                FROM secciones s
                JOIN cursos c ON s.curso_id = c.id
                WHERE s.id = ?
            """, (sec_id,))
            course_info = cursor.fetchone()
            if course_info:
                curso_id, creditos = course_info
                if curso_id not in inserted_courses:
                    inserted_courses.add(curso_id)
                    cursor.execute("""
                        INSERT INTO historial (estudiante_id, curso_id, periodo, nota, creditos_hora, estado)
                        VALUES (?, ?, '2026-10', NULL, ?, 'en_progreso')
                    """, (student_id, curso_id, creditos))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "¡Matrícula simulada exitosamente!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json or {}
        codigo = data.get('codigo')
        seccion_ids = data.get('seccion_ids', [])
        personal_context = data.get('personal_context', {})
        
        trabaja = int(personal_context.get('trabaja', 0))
        horas_trabajo_semana = int(personal_context.get('horas_trabajo_semana', 0))
        tiempo_traslado_diario = int(personal_context.get('tiempo_traslado_diario', 30))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, ciclo_actual FROM estudiantes WHERE codigo = ?", (codigo,))
        student_row = cursor.fetchone()
        if not student_row:
            conn.close()
            return jsonify({"success": False, "message": "Estudiante no encontrado"}), 404
        student_id, ciclo_actual = student_row
        
        # 1. Medidas del historial académico
        cursor.execute("""
            SELECT nota, creditos_hora, estado FROM historial 
            WHERE estudiante_id = ? AND estado IN ('aprobado', 'desaprobado')
        """, (student_id,))
        hist_rows = cursor.fetchall()
        
        total_puntos = sum(r[0] * r[1] for r in hist_rows if r[0] is not None)
        total_creditos = sum(r[1] for r in hist_rows if r[0] is not None)
        promedio_acumulado = total_puntos / total_creditos if total_creditos > 0 else 12.0
        
        creditos_aprobados = sum(r[1] for r in hist_rows if r[2] == 'aprobado')
        creditos_desaprobados = sum(r[1] for r in hist_rows if r[2] == 'desaprobado')
        numero_desaprobaciones = sum(1 for r in hist_rows if r[2] == 'desaprobado')
        
        cursor.execute("SELECT COUNT(*) FROM historial WHERE estudiante_id = ? AND estado = 'retirado'", (student_id,))
        cursos_retirados = cursor.fetchone()[0] or 0
        
        # Promedio del último ciclo
        cursor.execute("""
            SELECT DISTINCT periodo FROM historial 
            WHERE estudiante_id = ? AND periodo != '2026-10' AND estado IN ('aprobado', 'desaprobado')
            ORDER BY periodo DESC LIMIT 1
        """, (student_id,))
        latest_period_row = cursor.fetchone()
        if latest_period_row:
            latest_period = latest_period_row[0]
            cursor.execute("""
                SELECT nota, creditos_hora FROM historial 
                WHERE estudiante_id = ? AND periodo = ? AND estado IN ('aprobado', 'desaprobado')
            """, (student_id, latest_period))
            latest_rows = cursor.fetchall()
            lp_puntos = sum(r[0] * r[1] for r in latest_rows if r[0] is not None)
            lp_creditos = sum(r[1] for r in latest_rows if r[0] is not None)
            promedio_ultimo_ciclo = lp_puntos / lp_creditos if lp_creditos > 0 else 12.0
        else:
            promedio_ultimo_ciclo = promedio_acumulado
            
        # 2. Medidas de carga académica
        creditos_matriculados = 0
        cantidad_cursos = 0
        cantidad_cursos_repitencia = 0
        cantidad_cursos_dificiles = 0
        
        if seccion_ids:
            cursor.execute(f"""
                SELECT SUM(creditos), COUNT(id) FROM (
                    SELECT DISTINCT c.id, c.creditos
                    FROM secciones s
                    JOIN cursos c ON s.curso_id = c.id
                    WHERE s.id IN ({','.join('?' for _ in seccion_ids)})
                )
            """, seccion_ids)
            load_info = cursor.fetchone()
            creditos_matriculados = load_info[0] or 0
            cantidad_cursos = load_info[1] or 0
            
            # Dificultad
            cursor.execute(f"""
                SELECT COUNT(DISTINCT c.id) FROM secciones s
                JOIN cursos c ON s.curso_id = c.id
                WHERE s.id IN ({','.join('?' for _ in seccion_ids)}) AND c.dificultad >= 4
            """, seccion_ids)
            cantidad_cursos_dificiles = cursor.fetchone()[0] or 0
            
            # Repitencia
            cursor.execute(f"SELECT DISTINCT curso_id FROM secciones WHERE id IN ({','.join('?' for _ in seccion_ids)})", seccion_ids)
            selected_course_ids = [r[0] for r in cursor.fetchall()]
            for c_id in selected_course_ids:
                cursor.execute("SELECT COUNT(*) FROM historial WHERE estudiante_id = ? AND curso_id = ? AND estado = 'desaprobado'", (student_id, c_id))
                if cursor.fetchone()[0] > 0:
                    cantidad_cursos_repitencia += 1
                    
        # 3. Medidas del horario académico
        horarios_list = []
        if seccion_ids:
            cursor.execute(f"""
                SELECT s.id, h.dia, h.hora_ini, h.hora_fin
                FROM horarios h
                JOIN secciones s ON h.seccion_id = s.id
                WHERE s.id IN ({','.join('?' for _ in seccion_ids)})
            """, seccion_ids)
            horarios_list = cursor.fetchall()
            
        sched_features = server.calculate_schedule_features(horarios_list)
        
        # 4. Medidas relacionadas a docentes
        indice_exigencia_docentes = 3.5
        indice_dificultad_docente_curso = 3.5
        cantidad_docentes_exigentes = 0
        
        if seccion_ids:
            cursor.execute(f"""
                SELECT d.indice_exigencia FROM secciones s
                JOIN docentes d ON s.docente_id = d.id
                WHERE s.id IN ({','.join('?' for _ in seccion_ids)})
            """, seccion_ids)
            exigencias = [r[0] for r in cursor.fetchall() if r[0] is not None]
            if exigencias:
                indice_exigencia_docentes = sum(exigencias) / len(exigencias)
                cantidad_docentes_exigentes = sum(1 for e in exigencias if e >= 4.0)
                
            cursor.execute(f"""
                SELECT c.dificultad, d.indice_exigencia FROM secciones s
                JOIN cursos c ON s.curso_id = c.id
                JOIN docentes d ON s.docente_id = d.id
                WHERE s.id IN ({','.join('?' for _ in seccion_ids)})
            """, seccion_ids)
            pair_rows = cursor.fetchall()
            vals = [(r[0] + r[1]) / 2.0 for r in pair_rows if r[0] is not None and r[1] is not None]
            if vals:
                indice_dificultad_docente_curso = sum(vals) / len(vals)
                
        conn.close()
        
        features_dict = {
            "promedio_acumulado": round(promedio_acumulado, 2),
            "promedio_ultimo_ciclo": round(promedio_ultimo_ciclo, 2),
            "creditos_aprobados": creditos_aprobados,
            "creditos_desaprobados": creditos_desaprobados,
            "numero_desaprobaciones": numero_desaprobaciones,
            "cursos_retirados": cursos_retirados,
            "ciclo_actual": ciclo_actual,
            "creditos_matriculados": creditos_matriculados,
            "cantidad_cursos": cantidad_cursos,
            "cantidad_cursos_repitencia": cantidad_cursos_repitencia,
            "cantidad_cursos_dificiles": cantidad_cursos_dificiles,
            "hora_inicio_mas_temprana": sched_features["hora_inicio_mas_temprana"],
            "dias_7am": sched_features["dias_7am"],
            "hora_fin_mas_tardia": sched_features["hora_fin_mas_tardia"],
            "dias_nocturnos": sched_features["dias_nocturnos"],
            "dias_con_clases": sched_features["dias_con_clases"],
            "horas_consecutivas_maximas": sched_features["horas_consecutivas_maximas"],
            "horas_muertas_semana": sched_features["horas_muertas_semana"],
            "max_horas_en_campus_dia": sched_features["max_horas_en_campus_dia"],
            "indice_balance_horario": sched_features["indice_balance_horario"],
            "indice_exigencia_docentes": round(indice_exigencia_docentes, 2),
            "indice_dificultad_docente_curso": round(indice_dificultad_docente_curso, 2),
            "cantidad_docentes_exigentes": cantidad_docentes_exigentes,
            "tiempo_traslado_diario": tiempo_traslado_diario,
            "trabaja": trabaja,
            "horas_trabajo_semana": horas_trabajo_semana
        }
        
        prediction_result = predictor.predict_performance(features_dict)
        predicted_class = prediction_result["predicted_class"]
        
        # Generar recomendaciones
        recos = []
        if predicted_class == "Deficiente":
            recos.append("Tu rendimiento esperado es Deficiente. Considera reducir la carga de créditos o cambiar secciones con docentes con menor índice de exigencia.")
        elif predicted_class == "Regular":
            recos.append("Rendimiento esperado Regular. Evita cruces complejos, mantén tus horas de estudio altas y reduce horas laborables si es posible.")
        else:
            recos.append("Tu perfil actual proyecta un buen desempeño académico. ¡Sigue así y organiza tus horas de estudio de manera óptima!")
            
        if sched_features["horas_muertas_semana"] > 8:
            recos.append("Tienes más de 8 horas muertas a la semana. Considera agrupar tus secciones para reducir el tiempo perdido en el campus.")
        if sched_features["dias_7am"] >= 3:
            recos.append("Tienes 3 o más días con clases a las 7:00 AM. Asegura descansar bien para evitar la fatiga acumulada.")
        if trabaja == 1 and horas_trabajo_semana > 20:
            recos.append("Trabajas más de 20 horas semanales. Intenta balancear tu horario con menos créditos matriculados para evitar sobrecargas.")
        if cantidad_cursos_repitencia > 0:
            recos.append(f"Estás llevando {cantidad_cursos_repitencia} curso(s) en repitencia. Prioriza estas asignaturas sobre los demás cursos.")
            
        prediction_result["recommendations"] = recos
        return jsonify({
            "success": True,
            "prediction": prediction_result
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
