import os
import pymysql
import pymysql.cursors

def get_db_connection():
    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = int(os.environ.get('MYSQL_PORT', 3306))
    user = os.environ.get('MYSQL_USER', 'root')
    default_pass = '180302' if host in ('localhost', '127.0.0.1') else ''
    password = os.environ.get('MYSQL_PASSWORD', default_pass)
    database = os.environ.get('MYSQL_DB', 'upao_horarios')
    
    # Manejo de SSL si está configurado en las variables de entorno
    ssl_dict = None
    if os.environ.get('MYSQL_SSL', 'false').lower() == 'true':
        ssl_dict = {'ssl': {}}

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        autocommit=True,
        ssl=ssl_dict,
        cursorclass=pymysql.cursors.Cursor
    )
    return conn
