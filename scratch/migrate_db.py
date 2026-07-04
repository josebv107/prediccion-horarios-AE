import sqlite3
import os
import re
from datetime import datetime

# Conectar a la base de datos
db_path = os.path.join(os.path.dirname(__file__), "..", "db", "upao_new.db")
txt_path = os.path.join(os.path.dirname(__file__), "..", "HORARIOSCOMPLETOSUPAO.txt")

conn = sqlite3.connect(db_path, timeout=30)
c = conn.cursor()

# 1. Limpiar matrículas y horarios de otros usuarios
# El usuario que queremos preservar es 000287948
c.execute("SELECT id FROM estudiantes WHERE codigo = '000287948'")
row = c.fetchone()
if not row:
    print("Error: Usuario 000287948 no encontrado.")
    exit(1)
user_id_to_keep = row[0]

print(f"Borrando matrículas y reportes excepto para user_id {user_id_to_keep}...")
c.execute("DELETE FROM matricula WHERE estudiante_id != ?", (user_id_to_keep,))
c.execute("DELETE FROM historial WHERE periodo = '2026-10' AND estudiante_id != ?", (user_id_to_keep,))

# Obtener los IDs de las secciones que el usuario original sí tiene matriculadas
c.execute("SELECT seccion_id FROM matricula WHERE estudiante_id = ?", (user_id_to_keep,))
kept_secciones = [r[0] for r in c.fetchall()]
kept_secciones_str = ",".join(map(str, kept_secciones)) if kept_secciones else "-1"

print(f"Borrando horarios y secciones antiguas (preservando las de 000287948: {kept_secciones_str})...")
c.execute(f"DELETE FROM horarios WHERE seccion_id NOT IN ({kept_secciones_str})")
c.execute(f"DELETE FROM secciones WHERE id NOT IN ({kept_secciones_str})")
conn.commit()

# 2. Parsear el TXT
print("Procesando HORARIOSCOMPLETOSUPAO.txt...")
with open(txt_path, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.readlines()]

current_cycle = 1
current_course_code = None
current_course_name = None

i = 0
while i < len(lines):
    line = lines[i]
    if not line:
        i += 1
        continue
    
    # Detectar ciclo
    # Ej: "1er ciclo", "2do ciclo", "3er ciclo"
    if "ciclo" in line.lower() and len(line) < 15:
        match = re.search(r'(\d+)', line)
        if match:
            current_cycle = int(match.group(1))
        i += 1
        continue
    
    # Detectar curso
    # Ej: ICSI - ( CIEN-752 ) ALGEBRA MATRIC Y GEOM ANALIT
    m_course = re.search(r'\(\s*([\w\-]+)\s*\)\s*(.*)', line)
    if m_course and ("PRESENCIAL" in lines[i+1].upper() or "VIRTUAL" in lines[i+1].upper()):
        current_course_code = m_course.group(1).strip()
        current_course_name = m_course.group(2).strip()
        i += 2
        continue

    # Detectar bloque de NRC
    if line == "NRC:" and current_course_code:
        nrc = lines[i+1].strip()
        secc = ""
        liga = ""
        cred = 0
        capa = 0
        
        j = i + 2
        while j < len(lines):
            l = lines[j]
            if l == "SECC:": secc = lines[j+1].strip()
            elif l == "LIGA:": liga = lines[j+1].strip()
            elif l == "CRED:": cred = int(lines[j+1].strip())
            elif l == "CAPA:": capa = int(lines[j+1].strip())
            elif l.startswith("PABE\tAULA\tDIA\tHORA\tID DOCENTE\tDOCENTE") or l.startswith("PABE	AULA	DIA	HORA	ID DOCENTE	DOCENTE"):
                j += 1
                break
            elif l == "NRC:" or "ciclo" in l.lower() or l.startswith("ICSI - "):
                # Salimos si encontramos el siguiente NRC sin haber encontrado el header de PABE
                break
            j += 1
            
        # Determinar tipo
        tipo = "T"
        if "P" in liga: tipo = "P"
        elif "L" in liga: tipo = "L"

        # UPSERT Curso
        c.execute("SELECT id FROM cursos WHERE codigo=?", (current_course_code,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO cursos (codigo, nombre, creditos, ciclo_malla, dificultad) VALUES (?, ?, ?, ?, 3)",
                      (current_course_code, current_course_name, cred, current_cycle))
            curso_id = c.lastrowid
        else:
            curso_id = row[0]
            # Podríamos actualizar créditos/ciclo si quisiéramos, pero por ahora lo dejamos
            c.execute("UPDATE cursos SET creditos=?, ciclo_malla=? WHERE id=?", (cred, current_cycle, curso_id))
            
        # Parsear filas de horarios para este NRC
        horarios_list = []
        docente_id_to_use = None
        
        while j < len(lines):
            l = lines[j]
            if not l: 
                j+=1; continue
            if l == "NRC:" or "ciclo" in l.lower() or l.startswith("ICSI - "): 
                break
            
            # Linea de horario: PG  G105  LUN,  02:20 PM - 04:05 PM  000029743  FERNANDEZ JAEGER LUIS RENATO
            parts = l.split('\t')
            if len(parts) >= 6:
                pabe = parts[0].strip()
                aula = parts[1].strip()
                dia = parts[2].replace(',', '').strip()
                hora_str = parts[3].strip() # 02:20 PM - 04:05 PM
                id_doc = parts[4].strip()
                doc_name = parts[5].strip()
                
                # Extraer hora ini y fin
                h_parts = hora_str.split('-')
                hora_ini = ""
                hora_fin = ""
                if len(h_parts) == 2:
                    # Convert to 24h format for DB
                    try:
                        t_ini = datetime.strptime(h_parts[0].strip(), "%I:%M %p")
                        t_fin = datetime.strptime(h_parts[1].strip(), "%I:%M %p")
                        hora_ini = t_ini.strftime("%H:%M")
                        hora_fin = t_fin.strftime("%H:%M")
                    except Exception as e:
                        print("Error parsing time:", h_parts, e)
                        hora_ini = h_parts[0].strip()
                        hora_fin = h_parts[1].strip()
                
                # UPSERT Docente
                c.execute("SELECT id FROM docentes WHERE codigo=?", (id_doc,))
                d_row = c.fetchone()
                if not d_row:
                    c.execute("INSERT INTO docentes (codigo, nombres, indice_exigencia) VALUES (?, ?, 3.5)", (id_doc, doc_name))
                    doc_id = c.lastrowid
                else:
                    doc_id = d_row[0]
                    
                docente_id_to_use = doc_id
                
                horarios_list.append({
                    "dia": dia, "hora_ini": hora_ini, "hora_fin": hora_fin, "aula": aula, "pabellon": pabe
                })
            j += 1
            
        i = j # Avanzar i
        
        # INSERTAR Seccion
        if nrc and secc:
            c.execute("""INSERT INTO secciones 
                      (curso_id, periodo, liga, tipo, nrc, secc, docente_id, capacidad, matriculados, cerrado) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)""",
                      (curso_id, '2026-10', liga, tipo, nrc, secc, docente_id_to_use, capa))
            seccion_id = c.lastrowid
            
            for h in horarios_list:
                c.execute("INSERT INTO horarios (seccion_id, dia, hora_ini, hora_fin, aula, pabellon) VALUES (?,?,?,?,?,?)",
                          (seccion_id, h["dia"], h["hora_ini"], h["hora_fin"], h["aula"], h["pabellon"]))
            
            # Commit after each section block
            conn.commit()
                          
        continue
        
    i += 1

conn.close()
print("✅ Migración completada exitosamente!")
