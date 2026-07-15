import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from db_config import get_db_connection

def verify():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM secciones")
    secciones_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM estudiantes")
    estudiantes_count = cur.fetchone()[0]
    conn.close()
    print(f"VERIFICACIÓN EXITOSA:")
    print(f"- Secciones en MySQL: {secciones_count}")
    print(f"- Estudiantes en MySQL: {estudiantes_count}")

if __name__ == '__main__':
    verify()
