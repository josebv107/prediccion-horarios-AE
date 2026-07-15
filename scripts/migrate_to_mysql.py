import os
import sqlite3
import pymysql

def migrate():
    sqlite_db = os.path.join(os.path.dirname(__file__), "..", "db", "upao_new.db")
    if not os.path.exists(sqlite_db):
        print(f"Error: No se encontró la BD SQLite en {sqlite_db}")
        return

    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = int(os.environ.get('MYSQL_PORT', 3306))
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD', '')
    database = os.environ.get('MYSQL_DB', 'upao_horarios')

    ssl_dict = None
    if os.environ.get('MYSQL_SSL', 'false').lower() == 'true':
        ssl_dict = {'ssl': {}}

    print(f"Conectando a MySQL en {host}:{port} como '{user}'...")
    
    # Conexión inicial sin especificar base de datos para asegurarnos que exista
    conn_root = pymysql.connect(host=host, port=port, user=user, password=password, ssl=ssl_dict, charset='utf8mb4', autocommit=True)
    with conn_root.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn_root.close()

    conn_mysql = pymysql.connect(host=host, port=port, user=user, password=password, database=database, ssl=ssl_dict, charset='utf8mb4', autocommit=True)
    cur_mysql = conn_mysql.cursor()

    # Desactivar verificación de llaves foráneas para recrear tablas limpiamente
    cur_mysql.execute("SET FOREIGN_KEY_CHECKS = 0;")

    tables = ["predicciones", "matricula", "horarios", "historial", "secciones", "prerequisitos", "docentes", "cursos", "estudiantes"]
    for t in tables:
        cur_mysql.execute(f"DROP TABLE IF EXISTS `{t}`;")

    print("Creando tablas en MySQL...")
    
    cur_mysql.execute("""
    CREATE TABLE estudiantes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo VARCHAR(50) UNIQUE NOT NULL,
        nombres VARCHAR(150) NOT NULL,
        apellidos VARCHAR(150) NOT NULL,
        password VARCHAR(255) NOT NULL,
        carrera VARCHAR(150) NOT NULL,
        ciclo_actual INT NOT NULL,
        trabaja INT DEFAULT 0,
        horas_trabajo_semana INT DEFAULT 0,
        tiempo_traslado_diario INT DEFAULT 30
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur_mysql.execute("""
    CREATE TABLE cursos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo VARCHAR(50) UNIQUE NOT NULL,
        nombre VARCHAR(255) NOT NULL,
        creditos INT NOT NULL,
        ciclo_malla INT NOT NULL,
        dificultad INT DEFAULT 3
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur_mysql.execute("""
    CREATE TABLE prerequisitos (
        curso_id INT NOT NULL,
        prereq_id INT NOT NULL,
        PRIMARY KEY (curso_id, prereq_id),
        FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
        FOREIGN KEY (prereq_id) REFERENCES cursos(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur_mysql.execute("""
    CREATE TABLE docentes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo VARCHAR(50) UNIQUE NOT NULL,
        nombres VARCHAR(150) NOT NULL,
        indice_exigencia DOUBLE DEFAULT 3.5
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur_mysql.execute("""
    CREATE TABLE secciones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        curso_id INT NOT NULL,
        periodo VARCHAR(20) NOT NULL,
        liga VARCHAR(20) NOT NULL,
        tipo VARCHAR(20) NOT NULL,
        nrc VARCHAR(20) NOT NULL,
        secc VARCHAR(20) NOT NULL,
        docente_id INT,
        capacidad INT,
        matriculados INT DEFAULT 0,
        cerrado INT DEFAULT 0,
        FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
        FOREIGN KEY (docente_id) REFERENCES docentes(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur_mysql.execute("""
    CREATE TABLE horarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        seccion_id INT NOT NULL,
        dia VARCHAR(10) NOT NULL,
        hora_ini VARCHAR(10) NOT NULL,
        hora_fin VARCHAR(10) NOT NULL,
        aula VARCHAR(50),
        pabellon VARCHAR(50),
        FOREIGN KEY (seccion_id) REFERENCES secciones(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur_mysql.execute("""
    CREATE TABLE historial (
        id INT AUTO_INCREMENT PRIMARY KEY,
        estudiante_id INT NOT NULL,
        curso_id INT NOT NULL,
        periodo VARCHAR(20) NOT NULL,
        nota DOUBLE,
        creditos_hora INT NOT NULL,
        estado VARCHAR(50) NOT NULL,
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
        FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur_mysql.execute("""
    CREATE TABLE matricula (
        id INT AUTO_INCREMENT PRIMARY KEY,
        estudiante_id INT NOT NULL,
        seccion_id INT NOT NULL,
        periodo VARCHAR(20) NOT NULL,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY student_sec_period (estudiante_id, seccion_id, periodo),
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
        FOREIGN KEY (seccion_id) REFERENCES secciones(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur_mysql.execute("""
    CREATE TABLE predicciones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        estudiante_id INT NOT NULL,
        periodo VARCHAR(20) NOT NULL,
        resultado VARCHAR(50) NOT NULL,
        probabilidad DOUBLE,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        promedio_acumulado DOUBLE,
        promedio_ultimo_ciclo DOUBLE,
        creditos_matriculados INT,
        hora_inicio_mas_temprana DOUBLE,
        indice_balance_horario DOUBLE,
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    print("Migrando datos desde SQLite...")
    conn_sqlite = sqlite3.connect(sqlite_db)
    cur_sqlite = conn_sqlite.cursor()

    order = ["estudiantes", "cursos", "prerequisitos", "docentes", "secciones", "horarios", "historial", "matricula", "predicciones"]
    
    for table in order:
        cur_sqlite.execute(f"SELECT * FROM `{table}`")
        rows = cur_sqlite.fetchall()
        if not rows:
            continue
        
        cur_sqlite.execute(f"PRAGMA table_info(`{table}`)")
        cols = [info[1] for info in cur_sqlite.fetchall()]
        
        cols_str = ", ".join([f"`{c}`" for c in cols])
        placeholders = ", ".join(["%s"] * len(cols))
        sql = f"INSERT INTO `{table}` ({cols_str}) VALUES ({placeholders})"
        
        cur_mysql.executemany(sql, rows)
        print(f"  -> Migrados {len(rows)} registros a la tabla '{table}'")

    cur_mysql.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn_sqlite.close()
    conn_mysql.close()
    print("¡Migración a MySQL completada con éxito!")

if __name__ == '__main__':
    migrate()
