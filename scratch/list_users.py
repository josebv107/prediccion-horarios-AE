import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "db", "upao.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT codigo, password, nombres, apellidos, ciclo_actual FROM estudiantes ORDER BY codigo")
users = cursor.fetchall()

for u in users:
    print(f"Código: {u[0]} | Password: {u[1]} | Nombre: {u[2]} {u[3]} | Ciclo: {u[4]}")
conn.close()
