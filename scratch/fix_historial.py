import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "db", "upao_new.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Mapeo de (ID de curso viejo -> ID de curso nuevo)
# Basado en la base de datos
remapping = {
    5: 31,  # CIEN-597 -> CIEN-752
    6: 32,  # CIEN-397 -> CIEN-753
    3: 33,  # HUMA-899 -> HUMA-1179
    4: 34,  # ICSI-507 -> ISIA-100
    12: 35, # CIEN-599 -> CIEN-754
    9: 36,  # HUMA-901 -> HUMA-1180
}

for old_id, new_id in remapping.items():
    c.execute("UPDATE historial SET curso_id = ? WHERE curso_id = ?", (new_id, old_id))

conn.commit()
conn.close()
print("Historial remapeado exitosamente con los nuevos IDs de los cursos.")
