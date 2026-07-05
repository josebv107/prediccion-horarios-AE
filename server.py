from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
import sqlite3
import os
import urllib.parse
import math

def calculate_schedule_features(horarios_list):
    # Parse into day dictionary
    days_data = {d: [] for d in ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB']}
    
    all_starts = []
    all_ends = []
    dias_7am_set = set()
    dias_nocturnos_set = set()
    
    for row in horarios_list:
        sec_id, dia, hora_ini, hora_fin = row
        dia = dia.upper()
        
        # Convert HH:MM to float
        h_ini_h, h_ini_m = map(int, hora_ini.split(':'))
        h_fin_h, h_fin_m = map(int, hora_fin.split(':'))
        
        start_f = h_ini_h + h_ini_m / 60.0
        end_f = h_fin_h + h_fin_m / 60.0
        
        days_data[dia].append((start_f, end_f))
        all_starts.append(start_f)
        all_ends.append(end_f)
        
        if hora_ini == "07:00":
            dias_7am_set.add(dia)
        if end_f >= 19.0: # 7 PM o más tarde
            dias_nocturnos_set.add(dia)
            
    # Early/late
    hora_inicio_mas_temprana = min(all_starts) if all_starts else 8.0
    hora_fin_mas_tardia = max(all_ends) if all_ends else 12.0
    dias_7am = len(dias_7am_set)
    dias_nocturnos = len(dias_nocturnos_set)
    
    # Days with classes
    dias_con_clases_list = [d for d, blocks in days_data.items() if len(blocks) > 0]
    dias_con_clases = len(dias_con_clases_list)
    
    # Metrics per day
    horas_muertas_semana = 0.0
    horas_consecutivas_maximas = 0.0
    max_horas_en_campus_dia = 0.0
    daily_totals = []
    
    for dia in ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB']:
        blocks = days_data[dia]
        if not blocks:
            continue
            
        # Sort by start time
        blocks.sort(key=lambda x: x[0])
        
        # Total class hours
        total_hours = sum(b[1] - b[0] for b in blocks)
        daily_totals.append(total_hours)
        
        # Max hours in campus
        campus_duration = blocks[-1][1] - blocks[0][0]
        if campus_duration > max_horas_en_campus_dia:
            max_horas_en_campus_dia = campus_duration
            
        # Dead hours and consecutive hours
        day_dead = 0.0
        current_seq_duration = blocks[0][1] - blocks[0][0]
        max_seq = current_seq_duration
        
        for idx in range(1, len(blocks)):
            prev_b = blocks[idx - 1]
            curr_b = blocks[idx]
            
            gap = curr_b[0] - prev_b[1]
            if gap > 0.25: # Hueco de más de 15 minutos
                day_dead += gap
                # Rompe bloque consecutivo
                if current_seq_duration > max_seq:
                    max_seq = current_seq_duration
                current_seq_duration = curr_b[1] - curr_b[0]
            else:
                # Consecutivo (se acumula)
                current_seq_duration += (curr_b[1] - curr_b[0])
                
        if current_seq_duration > max_seq:
            max_seq = current_seq_duration
            
        horas_muertas_semana += day_dead
        if max_seq > horas_consecutivas_maximas:
            horas_consecutivas_maximas = max_seq
            
    # Indice balance (SD of class hours across active days)
    if daily_totals:
        mean_h = sum(daily_totals) / len(daily_totals)
        var_h = sum((x - mean_h)**2 for x in daily_totals) / len(daily_totals)
        indice_balance_horario = math.sqrt(var_h)
    else:
        indice_balance_horario = 0.0
        
    return {
        "hora_inicio_mas_temprana": round(hora_inicio_mas_temprana, 2),
        "dias_7am": dias_7am,
        "hora_fin_mas_tardia": round(hora_fin_mas_tardia, 2),
        "dias_nocturnos": dias_nocturnos,
        "dias_con_clases": dias_con_clases,
        "horas_consecutivas_maximas": round(horas_consecutivas_maximas, 2),
        "horas_muertas_semana": round(horas_muertas_semana, 2),
        "max_horas_en_campus_dia": round(max_horas_en_campus_dia, 2),
        "indice_balance_horario": round(indice_balance_horario, 2)
    }

class MyHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                username = data.get('username')
                password = data.get('password')
                
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "upao_new.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombres, apellidos, carrera, ciclo_actual FROM estudiantes WHERE codigo = ? AND password = ?", (username, password))
                student = cursor.fetchone()
                conn.close()
                
                if student:
                    response = {
                        "success": True,
                        "student": {
                            "id": student[0],
                            "codigo": username,
                            "nombres": student[1],
                            "apellidos": student[2],
                            "carrera": student[3],
                            "ciclo_actual": student[4]
                        }
                    }
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "Código o contraseña incorrectos"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode('utf-8'))
                
        elif self.path == '/api/enroll':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                codigo = data.get('codigo')
                seccion_ids = data.get('seccion_ids', [])
                
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "upao_new.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Obtener id del estudiante
                cursor.execute("SELECT id FROM estudiantes WHERE codigo = ?", (codigo,))
                student_row = cursor.fetchone()
                if not student_row:
                    conn.close()
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "Estudiante no encontrado"}).encode('utf-8'))
                    return
                student_id = student_row[0]
                
                # Iniciar transacción
                cursor.execute("BEGIN TRANSACTION")
                
                # 1. Decrementar matriculados de las secciones anteriores
                cursor.execute("SELECT seccion_id FROM matricula WHERE estudiante_id = ? AND periodo = '2026-10'", (student_id,))
                old_secciones = [r[0] for r in cursor.fetchall()]
                if old_secciones:
                    cursor.execute(f"UPDATE secciones SET matriculados = MAX(0, matriculados - 1) WHERE id IN ({','.join('?'*len(old_secciones))})", old_secciones)

                # Limpiar matrícula previa del periodo 2026-10 para simulación limpia
                cursor.execute("DELETE FROM matricula WHERE estudiante_id = ? AND periodo = '2026-10'", (student_id,))
                
                # Limpiar de historial de este periodo
                cursor.execute("DELETE FROM historial WHERE estudiante_id = ? AND periodo = '2026-10'", (student_id,))
                
                # 2. Incrementar matriculados de las nuevas secciones
                if seccion_ids:
                    cursor.execute(f"UPDATE secciones SET matriculados = matriculados + 1 WHERE id IN ({','.join('?'*len(seccion_ids))})", seccion_ids)

                
                inserted_courses = set()
                for sec_id in seccion_ids:
                    # Registrar en matrícula
                    cursor.execute("""
                        INSERT INTO matricula (estudiante_id, seccion_id, periodo)
                        VALUES (?, ?, '2026-10')
                    """, (student_id, sec_id))
                    
                    # Obtener curso del que forma parte esta sección
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
                            # Registrar en historial como en_progreso
                            cursor.execute("""
                                INSERT INTO historial (estudiante_id, curso_id, periodo, nota, creditos_hora, estado)
                                VALUES (?, ?, '2026-10', NULL, ?, 'en_progreso')
                            """, (student_id, curso_id, creditos))
                
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "¡Matrícula simulada exitosamente!"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode('utf-8'))
        elif self.path == '/api/predict':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                import predictor
                data = json.loads(post_data.decode('utf-8'))
                codigo = data.get('codigo')
                seccion_ids = data.get('seccion_ids', [])
                personal_context = data.get('personal_context', {})
                
                trabaja = int(personal_context.get('trabaja', 0))
                horas_trabajo_semana = int(personal_context.get('horas_trabajo_semana', 0))
                tiempo_traslado_diario = int(personal_context.get('tiempo_traslado_diario', 30))
                
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "upao_new.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Obtener id del estudiante
                cursor.execute("SELECT id, ciclo_actual FROM estudiantes WHERE codigo = ?", (codigo,))
                student_row = cursor.fetchone()
                if not student_row:
                    conn.close()
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "Estudiante no encontrado"}).encode('utf-8'))
                    return
                    
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
                    # Carga general: obtener créditos sumando cursos únicos
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
                
                sched_features = calculate_schedule_features(horarios_list)
                
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
                
                # Consolidar todas las características
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
                
                # Ejecutar predicción
                prediction_result = predictor.predict_performance(features_dict)
                predicted_class = prediction_result["predicted_class"]
                
                # Generar recomendaciones dinámicas en base a los features
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
                
                # Devolver respuesta
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "prediction": prediction_result
                }).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "message": "Endpoint no encontrado"}).encode('utf-8'))

    def do_GET(self):
        if self.path.startswith('/api/student-info'):
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            codigo = query_params.get('codigo', [None])[0]
            
            if not codigo:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Código de estudiante requerido"}).encode('utf-8'))
                return
                
            try:
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "upao_new.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Obtener info básica
                cursor.execute("SELECT id, nombres, apellidos, carrera, ciclo_actual FROM estudiantes WHERE codigo = ?", (codigo,))
                student = cursor.fetchone()
                
                if not student:
                    conn.close()
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "Estudiante no encontrado"}).encode('utf-8'))
                    return
                    
                student_id = student[0]
                
                # Calcular créditos y promedio ponderado
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
                
                response = {
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
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode('utf-8'))
                
        elif self.path.startswith('/api/eligible-courses'):
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            codigo = query_params.get('codigo', [None])[0]
            
            if not codigo:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Código de estudiante requerido"}).encode('utf-8'))
                return
                
            try:
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "upao_new.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Obtener id y ciclo del estudiante
                cursor.execute("SELECT id, ciclo_actual FROM estudiantes WHERE codigo = ?", (codigo,))
                student_row = cursor.fetchone()
                if not student_row:
                    conn.close()
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "Estudiante no encontrado"}).encode('utf-8'))
                    return
                student_id = student_row[0]
                ciclo_actual = student_row[1]
                
                # Obtener cursos elegibles hasta el ciclo actual que NO estén aprobados
                cursor.execute("""
                    SELECT c.id, c.codigo, c.nombre, c.creditos, c.ciclo_malla, c.dificultad
                    FROM cursos c
                    WHERE c.ciclo_malla <= ?
                      AND c.id NOT IN (
                          SELECT h.curso_id 
                          FROM historial h 
                          WHERE h.estudiante_id = ? AND h.estado = 'aprobado'
                      )
                    ORDER BY c.ciclo_malla ASC, c.codigo ASC
                """, (ciclo_actual, student_id))

                
                courses_rows = cursor.fetchall()
                eligible_courses = []
                
                for crow in courses_rows:
                    cid, c_cod, c_nom, c_cred, c_ciclo, c_dif = crow
                    
                    # Ver si está en historial como desaprobado para marcarlo como pendiente
                    cursor.execute("""
                        SELECT estado FROM historial 
                        WHERE estudiante_id = ? AND curso_id = ?
                        ORDER BY id DESC LIMIT 1
                    """, (student_id, cid))
                    hist_status = cursor.fetchone()
                    status_label = "regular"
                    if hist_status and hist_status[0] == "desaprobado":
                        status_label = "pendiente"
                    
                    # Obtener secciones de este curso para el periodo 2026-10
                    cursor.execute("""
                        SELECT s.id, s.liga, s.tipo, s.nrc, s.secc, s.capacidad, s.matriculados, s.cerrado, d.nombres, d.indice_exigencia
                        FROM secciones s
                        LEFT JOIN docentes d ON s.docente_id = d.id
                        WHERE s.curso_id = ? AND s.periodo = '2026-10'
                        ORDER BY 
                            CASE s.tipo
                                WHEN 'T' THEN 1
                                WHEN 'P' THEN 2
                                WHEN 'L' THEN 3
                                ELSE 4
                            END ASC,
                            s.secc ASC
                    """, (cid,))
                    sec_rows = cursor.fetchall()
                    sections = []
                    
                    for srow in sec_rows:
                        sid, liga, tipo, nrc, secc, capa, matric, cerrado, doc_nombres, doc_exig = srow
                        
                        # Obtener horarios de la sección
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
                    
                    if sections:
                        # Ordenar secciones por Liga (para agrupar T1 con P1) y luego por tipo (T, P, L)
                        def section_sort_key(sec):
                            liga_str = sec.get('liga', '')
                            # Extraer identificador de grupo (eliminar letras T, P, L)
                            group_id = liga_str.replace('T', '').replace('P', '').replace('L', '').strip()
                            tipo = sec.get('tipo', '')
                            tipo_order = {'T': 1, 'P': 2, 'L': 3}.get(tipo, 4)
                            return (group_id, tipo_order, sec.get('secc', ''))
                            
                        sections.sort(key=section_sort_key)
                        
                        eligible_courses.append({
                            "id": cid,
                            "codigo": c_cod,
                            "nombre": c_nom,
                            "creditos": c_cred,
                            "ciclo_malla": c_ciclo,
                            "dificultad": c_dif,
                            "estado": status_label,
                            "secciones": sections
                        })
                
                # Obtener secciones en las que el estudiante ya está matriculado para el periodo 2026-10
                cursor.execute("SELECT seccion_id FROM matricula WHERE estudiante_id = ? AND periodo = '2026-10'", (student_id,))
                enrolled_section_ids = [row[0] for row in cursor.fetchall()]
                
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True, 
                    "courses": eligible_courses,
                    "enrolled_section_ids": enrolled_section_ids
                }).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode('utf-8'))
        else:
            # Servir archivos estáticos normalmente
            super().do_GET()

def run(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MyHandler)
    print(f"Servidor UPAO Canvas iniciado en http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        httpd.server_close()

if __name__ == '__main__':
    run()
