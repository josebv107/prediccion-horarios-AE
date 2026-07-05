import sqlite3
import os
import re

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db', 'upao_new.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

def parse_txt():
    with open('HORARIOSCOMPLETOSUPAO.txt', 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
    
    current_curso_cod = None
    current_curso_nom = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Course header example: ICSI - ( CIEN-752 ) ALGEBRA MATRIC Y GEOM ANALIT
        if ' - ( ' in line and ' ) ' in line:
            parts = line.split(' - ( ')
            if len(parts) == 2:
                sub_parts = parts[1].split(' ) ')
                if len(sub_parts) >= 1:
                    current_curso_cod = sub_parts[0].strip()
                    current_curso_nom = sub_parts[1].strip() if len(sub_parts) > 1 else ''
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
                
            print(f"Course: {current_curso_cod}, NRC: {nrc}, Secc: {secc}, Docente: {docente_nom}, Horarios: {len(horarios)}")
            i = j
            continue
            
        i += 1

parse_txt()
