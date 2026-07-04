import sqlite3
import os

txt_path = os.path.join(os.path.dirname(__file__), "..", "HORARIOSCOMPLETOSUPAO.txt")
db_path = os.path.join(os.path.dirname(__file__), "..", "db", "upao_new.db")

with open(txt_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

conn = sqlite3.connect(db_path)
c = conn.cursor()

current_code = None
for i in range(len(lines)):
    line = lines[i].strip()
    if line.startswith("ICSI - (") and ")" in line:
        parts = line.split(")")
        current_code = parts[0].split("(")[1].strip()
    elif line == "CRED:" and current_code:
        try:
            cred = int(lines[i+1].strip())
            c.execute("UPDATE cursos SET creditos = ? WHERE codigo = ? AND creditos = 0", (cred, current_code))
            current_code = None  # Done for this course
        except:
            pass

conn.commit()
conn.close()
print("Creditos actualizados")
