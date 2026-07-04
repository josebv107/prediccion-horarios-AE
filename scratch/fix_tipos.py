import sqlite3
import os

txt_path = os.path.join(os.path.dirname(__file__), "..", "HORARIOSCOMPLETOSUPAO.txt")
db_path = os.path.join(os.path.dirname(__file__), "..", "db", "upao_new.db")

with open(txt_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

conn = sqlite3.connect(db_path)
c = conn.cursor()

current_nrc = None
for i in range(len(lines)):
    line = lines[i].strip()
    if line == "NRC:":
        current_nrc = lines[i+1].strip()
    elif line == "ID LIGA:" and current_nrc:
        id_liga = lines[i+1].strip()
        
        tipo = "T"
        if "P" in id_liga: tipo = "P"
        elif "L" in id_liga: tipo = "L"
        elif "Q" in id_liga: tipo = "P" # A veces usan otras letras para practica
        
        c.execute("UPDATE secciones SET liga = ?, tipo = ? WHERE nrc = ?", (id_liga, tipo, current_nrc))
        current_nrc = None

conn.commit()
conn.close()
print("Tipos de seccion arreglados.")
