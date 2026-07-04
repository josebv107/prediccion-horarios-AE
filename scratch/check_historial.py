import sqlite3
conn = sqlite3.connect('db/upao_new.db')
c = conn.cursor()
c.execute("SELECT h.curso_id, c.nombre FROM historial h JOIN cursos c ON h.curso_id=c.id WHERE h.estudiante_id = 6 AND h.estado = 'aprobado'")
print("Aprobados:", c.fetchall())
c.execute("SELECT h.curso_id, c.nombre FROM historial h JOIN cursos c ON h.curso_id=c.id WHERE h.estudiante_id = 6 AND h.estado = 'desaprobado'")
print("Desaprobados:", c.fetchall())
