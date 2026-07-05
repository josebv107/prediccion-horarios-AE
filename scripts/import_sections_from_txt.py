import sqlite3
import os
import re

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db', 'upao_new.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

def insert_data():
    with open('scratch/HORARIOS_FALTANTES.txt', 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
    
    current_curso_cod = None
    
    i = 0
    added_sections = 0
    while i < len(lines):
        line = lines[i]
        
        # Course header example: ICSI - ( CIEN-752 ) ALGEBRA MATRIC Y GEOM ANALIT
        if ' - ( ' in line and ' ) ' in line:
            parts = line.split(' - ( ')
            if len(parts) >= 2:
                sub_parts = parts[1].split(' ) ')
                if len(sub_parts) >= 1:
                    current_curso_cod = sub_parts[0].strip()
                    i += 1
                    continue
                    
        # Check if NRC block starts
        if line == 'NRC:':
            if not current_curso_cod:
                i += 1
                continue
                
            nrc = lines[i+1].strip()
            
            # Find SECC
            j = i + 2
            secc = ''
            while j < len(lines) and lines[j] != 'SECC:': j += 1
            if j < len(lines): secc = lines[j+1].strip()
            
            # Find ID LIGA
            while j < len(lines) and lines[j] != 'ID LIGA:': j += 1
            if j < len(lines): id_liga = lines[j+1].strip()
            
            # Find LIGA
            while j < len(lines) and lines[j] != 'LIGA:': j += 1
            if j < len(lines): liga = lines[j+1].strip()
            
            # Extract tipo from ID LIGA (e.g. 6T -> T, P1 -> P)
            tipo_match = re.search(r'[TPL]', id_liga)
            tipo = tipo_match.group(0) if tipo_match else 'T'
            
            # Find CAPA
            while j < len(lines) and lines[j] != 'CAPA:': j += 1
            if j < len(lines): capa = lines[j+1].strip()
            
            # Find REGI
            while j < len(lines) and lines[j] != 'REGI:': j += 1
            if j < len(lines): regi = lines[j+1].strip()
            
            # Check cerrado
            cerrado = 1 if j+2 < len(lines) and lines[j+2] == 'CERRADO' else 0
            
            # Find DOCENTE header
            while j < len(lines) and not 'ID DOCENTE' in lines[j]: j += 1
            j += 1
            
            # Parse schedules
            horarios = []
            docente_cod = None
            docente_nom = None
            while j < len(lines) and lines[j] != 'NRC:' and ' - ( ' not in lines[j] and 'ciclo' not in lines[j].lower():
                parts = lines[j].split('\t')
                if len(parts) >= 6:
                    pabellon = parts[0].strip()
                    aula = parts[1].strip()
                    dia = parts[2].strip().replace(',', '')
                    hora = parts[3].strip()
                    docente_cod = parts[4].strip()
                    docente_nom = parts[5].strip()
                    
                    if ' - ' in hora:
                        h_ini, h_fin = hora.split(' - ')
                        horarios.append((dia, h_ini.strip(), h_fin.strip(), aula, pabellon))
                j += 1
            
            # Get course ID
            c.execute("SELECT id FROM cursos WHERE codigo=?", (current_curso_cod,))
            curso_row = c.fetchone()
            if curso_row:
                curso_id = curso_row[0]
                
                # Ensure Docente exists
                did = None
                if docente_nom:
                    c.execute("SELECT id FROM docentes WHERE nombres=?", (docente_nom,))
                    doc_row = c.fetchone()
                    if doc_row:
                        did = doc_row[0]
                    else:
                        c.execute("INSERT INTO docentes (nombres, indice_exigencia) VALUES (?, ?)", (docente_nom, 3.5))
                        did = c.lastrowid
                
                # Check if section already exists
                c.execute("SELECT id FROM secciones WHERE nrc=? AND curso_id=?", (nrc, curso_id))
                sec_row = c.fetchone()
                
                if True:
                    # Insert seccion with hardcoded periodo for simulation
                    c.execute("""
                        INSERT INTO secciones (curso_id, periodo, liga, tipo, nrc, secc, docente_id, capacidad, matriculados, cerrado)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (curso_id, '2026-10', id_liga, tipo, nrc, secc, did, int(capa) if capa.isdigit() else 60, int(regi) if regi.isdigit() else 0, cerrado))
                    sid = c.lastrowid
                    added_sections += 1
                    
                    # Insert horarios
                    for (dia, h_ini, h_fin, aula, pabellon) in horarios:
                        c.execute("""
                            INSERT INTO horarios (seccion_id, dia, hora_ini, hora_fin, aula, pabellon)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (sid, dia, h_ini, h_fin, aula, pabellon))
            
            i = j
            continue
            
        i += 1
        
    conn.commit()
    print(f"Added {added_sections} new sections.")

insert_data()
conn.close()
