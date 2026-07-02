import sqlite3
import os

# Set db path relative to the current script location
db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db")
db_path = os.path.join(db_dir, "upao.db")

os.makedirs(db_dir, exist_ok=True)

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# ══════════════════════════════════════════════
# SCHEMA
# ══════════════════════════════════════════════
c.executescript("""
PRAGMA foreign_keys = ON;

-- Estudiantes
CREATE TABLE estudiantes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo      TEXT UNIQUE NOT NULL,
    nombres     TEXT NOT NULL,
    apellidos   TEXT NOT NULL,
    password    TEXT NOT NULL,  -- en prod iría hash; aquí plaintext para demo
    carrera     TEXT NOT NULL,
    ciclo_actual INTEGER NOT NULL,
    trabaja     INTEGER DEFAULT 0,  -- 0=No, 1=Sí
    horas_trabajo_semana INTEGER DEFAULT 0,
    tiempo_traslado_diario INTEGER DEFAULT 30  -- minutos
);

-- Cursos (malla completa)
CREATE TABLE cursos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo      TEXT UNIQUE NOT NULL,  -- ej: ISIA-104
    nombre      TEXT NOT NULL,
    creditos    INTEGER NOT NULL,
    ciclo_malla INTEGER NOT NULL,      -- ciclo recomendado en la malla
    dificultad  INTEGER DEFAULT 3      -- 1-5 subjetivo
);

-- Prerequisitos
CREATE TABLE prerequisitos (
    curso_id    INTEGER REFERENCES cursos(id),
    prereq_id   INTEGER REFERENCES cursos(id),
    PRIMARY KEY (curso_id, prereq_id)
);

-- Historial académico del estudiante
CREATE TABLE historial (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id   INTEGER REFERENCES estudiantes(id),
    curso_id        INTEGER REFERENCES cursos(id),
    periodo         TEXT NOT NULL,   -- ej: 2024-10
    nota            REAL,            -- NULL si en progreso
    creditos_hora   INTEGER NOT NULL,
    estado          TEXT NOT NULL    -- 'aprobado','desaprobado','en_progreso','retirado'
);

-- Docentes
CREATE TABLE docentes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo          TEXT UNIQUE NOT NULL,
    nombres         TEXT NOT NULL,
    indice_exigencia REAL DEFAULT 3.5  -- 2.0-5.0
);

-- Secciones (grupos/ligas)
CREATE TABLE secciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    curso_id        INTEGER REFERENCES cursos(id),
    periodo         TEXT NOT NULL,
    liga            TEXT NOT NULL,   -- T1, T2, etc.
    tipo            TEXT NOT NULL,   -- T=Teoria, P=Practica, L=Laboratorio
    nrc             TEXT NOT NULL,
    secc            TEXT NOT NULL,
    docente_id      INTEGER REFERENCES docentes(id),
    capacidad       INTEGER,
    matriculados    INTEGER DEFAULT 0,
    cerrado         INTEGER DEFAULT 0  -- 0=abierto, 1=cerrado
);

-- Horarios de cada sección (puede tener múltiples bloques)
CREATE TABLE horarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    seccion_id  INTEGER REFERENCES secciones(id),
    dia         TEXT NOT NULL,   -- LUN,MAR,MIE,JUE,VIE,SAB
    hora_ini    TEXT NOT NULL,   -- HH:MM
    hora_fin    TEXT NOT NULL,
    aula        TEXT,
    pabellon    TEXT
);

-- Matrícula del estudiante (secciones seleccionadas)
CREATE TABLE matricula (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id   INTEGER REFERENCES estudiantes(id),
    seccion_id      INTEGER REFERENCES secciones(id),
    periodo         TEXT NOT NULL,
    fecha_registro  TEXT DEFAULT (datetime('now')),
    UNIQUE(estudiante_id, seccion_id, periodo)
);

-- Predicciones generadas
CREATE TABLE predicciones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    estudiante_id   INTEGER REFERENCES estudiantes(id),
    periodo         TEXT NOT NULL,
    resultado       TEXT NOT NULL,   -- Excelente/Bueno/Regular/Deficiente
    probabilidad    REAL,
    fecha           TEXT DEFAULT (datetime('now')),
    -- features usados
    promedio_acumulado REAL,
    promedio_ultimo_ciclo REAL,
    creditos_matriculados INTEGER,
    hora_inicio_mas_temprana REAL,
    indice_balance_horario REAL
);
""")

print("✅ Tablas creadas")

# ══════════════════════════════════════════════
# DATOS — DOCENTES
# ══════════════════════════════════════════════
docentes = [
    ("000046447", "SANTA CRUZ DAMIAN ELIAS ENRIQUE",       3.8),
    ("000005119", "ABANTO CABRERA HEBER GERSON",            3.5),
    ("000029331", "CUBA CASTILLO CAROLA LIZETH",            3.2),
    ("000006276", "CASTILLO ROBLES EDWARD FERNANDO",        4.0),
    ("000000355", "CALDERON SEDANO JOSE ANTONIO",           4.2),
    ("000000580", "MIRANDA VELASQUEZ EDDY MODESTO",         4.0),
    ("000149608", "LETURIA RODRIGUEZ WALTER IVAN",          3.6),
    ("000000591", "SAGASTEGUI CHIGNE TEOBALDO HERNAN",      3.9),
    ("000246264", "COSAVALENTE CULQUICHICON PAUL",          4.1),
    ("000251948", "MURGA TORRES EMZON ENRIQUE",             3.7),
    ("000270585", "ALFARO HERRERA LUIS ALBERTO",            3.4),
    ("000091965", "LIMAY ARENAS NOLBERTO JOSE",             3.3),
    ("000000217", "GAVIDIA IVERICO JESUS ROBERTO",          3.5),
    ("000115077", "BOCANEGRA OTINIANO ANGEL FRANCISCO",     3.0),
    ("000127846", "CASAS DE LI NANCY CARIDAD",              3.1),
    ("000102226", "BECERRA ROMERO JESUS SAMUEL",            2.9),
    ("000032392", "RODRIGUEZ ALZA MIGUEL ANGEL",            3.2),
    ("000121730", "CRIBILLEROS SHIGIHARA OLGA AMELIA",      3.0),
    ("000000811", "SORIANO COLCHADO JOSE LUIS",             3.5),
    ("000000489", "RODRIGUEZ ZEVALLOS ANTONIO RICARDO",     3.6),
    ("000074856", "SALINAS GAMBOA DIANA JACQUELINE",        3.3),
    ("000072092", "SOLIS RAMIREZ EDUARDO ALEJANDRO",        3.4),
    ("000079976", "CONCEPCION URTEAGA GILMER RAMIRO",       3.1),
    ("000009695", "CAMPAÑA BOYER MIRKO VLADIMIR",           3.5),
    ("000000591", "SAGASTEGUI CHIGNE TEOBALDO HERNAN",      3.9),
    ("000051007", "URRACA VERGARA ELENA MATILDE",           3.3),
]
# deduplicate by codigo
seen = set()
docentes_uniq = []
for d in docentes:
    if d[0] not in seen:
        seen.add(d[0])
        docentes_uniq.append(d)

c.executemany("INSERT INTO docentes(codigo,nombres,indice_exigencia) VALUES(?,?,?)", docentes_uniq)
print(f"✅ {len(docentes_uniq)} docentes insertados")

# Helper
def doc_id(codigo):
    row = c.execute("SELECT id FROM docentes WHERE codigo=?", (codigo,)).fetchone()
    return row[0] if row else None

def curso_id(codigo):
    row = c.execute("SELECT id FROM cursos WHERE codigo=?", (codigo,)).fetchone()
    return row[0] if row else None

# ══════════════════════════════════════════════
# DATOS — CURSOS (malla completa ciclos 1-5)
# ══════════════════════════════════════════════
cursos_data = [
    # (codigo, nombre, creditos, ciclo_malla, dificultad)
    ("ICSI-506","ALGORITMIA Y PROGRAMACIÓN",4,1,4),
    ("HUMA-900","METODOLOGIA DEL APRENDIZAJE UNIVERSITARIO",2,1,2),
    ("HUMA-899","COMUNICACIÓN I",4,1,2),
    ("ICSI-507","INTRODUCCIÓN A LA ING. DE SISTEMAS E IA",2,1,2),
    ("CIEN-597","ALGEBRA MATRICIAL Y GEOMETRÍA ANALÍTICA",4,1,4),
    ("CIEN-397","CÁLCULO I",4,1,4),
    ("ICSI-509","PROGRAMACIÓN ORIENTADO A OBJETOS",4,2,4),
    ("HUMA-1181","FILOSOFIA Y PENSAMIENTO CRÍTICO",3,2,2),
    ("HUMA-901","COMUNICACIÓN II",2,2,2),
    ("ADMI-779","ORGANIZACIÓN Y GESTIÓN DE EMPRESAS",4,2,3),
    ("CIEN-768","FÍSICA I",4,2,5),
    ("CIEN-599","CÁLCULO II",4,2,5),
    ("ISIA-101","ESTADÍSTICA PARA INGENIEROS",4,3,4),
    ("ICSI-671","ESTRUCTURA DE DATOS Y ALGORITMOS",4,3,5),
    ("HUMA-1182","REALIDAD NACIONAL Y GLOBAL",2,3,2),
    ("ICSI-672","GESTIÓN DE PROCESOS DE NEGOCIOS",4,3,3),
    ("CIEN-648","FÍSICA II",4,3,5),
    ("CIEN-755","CÁLCULO III",4,3,5),
    ("ISIA-102","REDES Y SISTEMAS OPERATIVOS",4,4,4),
    ("HUMA-1184","ÉTICA, CIUDADANIA, DISCAPACIDAD E INCLUSIÓN",3,4,2),
    ("ICSI-673","BASE DE DATOS",4,4,4),
    ("ICSI-674","INGENIERÍA DE REQUISITOS",3,4,4),
    ("ISIA-103","SISTEMAS EMPRESARIALES",4,4,3),
    ("HUMA-1183","VIGENCIA Y TRASCENDENCIA DEL PENS. DE A. ORREGO",2,4,2),
    ("ISIA-104","CÓMPUTO DISTRIBUIDO Y PARALELO",3,5,4),
    ("CIEN-746","MEDIO AMBIENTE Y DESARROLLO SOSTENIBLE",3,5,2),
    ("ICSI-521","SISTEMA DE GESTIÓN DE BASE DE DATOS",4,5,4),
    ("ISIA-105","INGENIERÍA DEL SOFTWARE",4,5,4),
    ("ICSI-675","PATRONES DE DISEÑO DE SOFTWARE",4,5,4),
    ("ISIA-106","APRENDIZAJE ESTADÍSTICO",3,5,4),
]
c.executemany("INSERT INTO cursos(codigo,nombre,creditos,ciclo_malla,dificultad) VALUES(?,?,?,?,?)", cursos_data)
print(f"✅ {len(cursos_data)} cursos insertados")

# ══════════════════════════════════════════════
# DATOS — ESTUDIANTE JOSE
# ══════════════════════════════════════════════
c.execute("""INSERT INTO estudiantes
    (codigo,nombres,apellidos,password,carrera,ciclo_actual,trabaja,horas_trabajo_semana,tiempo_traslado_diario)
    VALUES(?,?,?,?,?,?,?,?,?)""",
    ("000287948","JOSE ELIAS","BOCANEGRA VALVERDE","upao2024",
     "Ingeniería de Sistemas e Inteligencia Artificial",5,0,0,30))
est_id = c.lastrowid
print(f"✅ Estudiante insertado (id={est_id})")

# ══════════════════════════════════════════════
# HISTORIAL — ciclos 1-4 completos + ciclo 5 en progreso
# Simulamos: ya acabó ciclo 4, va a entrar a ciclo 5
# ══════════════════════════════════════════════
historial = [
    # (codigo_curso, periodo, nota, estado)
    # CICLO 1 — 2024-10
    ("ICSI-506","2024-10",16,"aprobado"),
    ("HUMA-900","2024-10",17,"aprobado"),
    ("HUMA-899","2024-10",13,"aprobado"),
    ("ICSI-507","2024-10",16,"aprobado"),
    ("CIEN-597","2024-10",16,"aprobado"),
    ("CIEN-397","2024-10",13,"aprobado"),
    # CICLO 2 — 2024-20 y 2025-10
    ("ICSI-509","2024-20",15,"aprobado"),
    ("HUMA-1181","2025-10",17,"aprobado"),
    ("HUMA-901","2024-20",12,"aprobado"),
    ("ADMI-779","2025-10",16,"aprobado"),
    ("CIEN-768","2025-10",16,"aprobado"),
    ("CIEN-599","2024-20",14,"aprobado"),
    # CICLO 3 — 2025-10 y 2025-20
    ("ISIA-101","2025-20",19,"aprobado"),
    ("ICSI-671","2025-10",12,"aprobado"),
    ("HUMA-1182","2025-10",18,"aprobado"),
    ("ICSI-672","2025-10",14,"aprobado"),
    ("CIEN-648","2026-10",None,"en_progreso"),   # Física II - en progreso
    ("CIEN-755","2025-10",13,"aprobado"),
    # CICLO 4 — 2025-20 y 2026-10
    ("ISIA-102","2025-20",14,"aprobado"),
    ("HUMA-1184","2025-20",17,"aprobado"),
    ("ICSI-673","2025-20",13,"aprobado"),
    ("ICSI-674","2025-20",12,"aprobado"),
    ("ISIA-103","2025-20",14,"aprobado"),
    ("HUMA-1183","2026-10",None,"en_progreso"),  # Vigencia - en progreso
    # CICLO 5 — 2026-10 EN PROGRESO
    ("ISIA-104","2026-10",None,"en_progreso"),
    ("CIEN-746","2026-10",None,"en_progreso"),
    ("ICSI-521","2026-10",None,"en_progreso"),
    ("ISIA-105","2026-10",None,"en_progreso"),
    ("ICSI-675","2026-10",None,"en_progreso"),
    ("ISIA-106","2026-10",None,"en_progreso"),
]

for (cod, periodo, nota, estado) in historial:
    cid = curso_id(cod)
    cred = c.execute("SELECT creditos FROM cursos WHERE id=?", (cid,)).fetchone()[0]
    c.execute("""INSERT INTO historial(estudiante_id,curso_id,periodo,nota,creditos_hora,estado)
                 VALUES(?,?,?,?,?,?)""", (est_id, cid, periodo, nota, cred, estado))
print(f"✅ {len(historial)} registros de historial insertados")

# ══════════════════════════════════════════════
# SECCIONES Y HORARIOS — ciclo 5 cursos (2026-10)
# ══════════════════════════════════════════════
PERIODO = "2026-10"

def ins_seccion(curso_cod, liga, tipo, nrc, secc, doc_cod, capa, matric, cerrado):
    cid = curso_id(curso_cod)
    did = doc_id(doc_cod)
    c.execute("""INSERT INTO secciones(curso_id,periodo,liga,tipo,nrc,secc,docente_id,capacidad,matriculados,cerrado)
                 VALUES(?,?,?,?,?,?,?,?,?,?)""",
              (cid, PERIODO, liga, tipo, nrc, secc, did, capa, matric, cerrado))
    return c.lastrowid

def ins_horario(sec_id, dia, ini, fin, aula=None, pab=None):
    c.execute("INSERT INTO horarios(seccion_id,dia,hora_ini,hora_fin,aula,pabellon) VALUES(?,?,?,?,?,?)",
              (sec_id, dia, ini, fin, aula, pab))

# ── FÍSICA II (CIEN-648) ──────────────────────────────────────────
# Liga T2: J05(T) + J06(P) + J07/J08(L2)
sid = ins_seccion("CIEN-648","T2","T","12500","J05","000246264",60,59,0)
ins_horario(sid,"VIE","07:00","08:45","G804","PG")

sid = ins_seccion("CIEN-648","T2","P","12501","J06","000246264",60,59,0)
ins_horario(sid,"VIE","08:50","10:35","G804","PG")

sid = ins_seccion("CIEN-648","T2","L","12502","J07","000246264",32,31,0)
ins_horario(sid,"VIE","10:40","12:25","F203","PF")   # lab opción 1 (viernes)

sid = ins_seccion("CIEN-648","T2","L","12503","J08","000091965",29,28,0)
ins_horario(sid,"VIE","12:30","14:15","F203","PF")   # lab opción 2 (viernes tarde)

# Liga T1: J01(T) + J02(P) + J03/J04(L1)
sid = ins_seccion("CIEN-648","T1","T","5529","J01","000246264",54,29,0)
ins_horario(sid,"MIE","07:00","08:45","G706","PG")

sid = ins_seccion("CIEN-648","T1","P","5530","J02","000246264",54,29,0)
ins_horario(sid,"JUE","07:00","08:45","G304","PG")

sid = ins_seccion("CIEN-648","T1","L","5531","J03","000000217",27,15,0)
ins_horario(sid,"JUE","08:50","10:35","F205","PF")

sid = ins_seccion("CIEN-648","T1","L","5532","J04","000270585",27,14,0)
ins_horario(sid,"VIE","07:00","08:45","F205","PF")

# ── CÓMPUTO DISTRIBUIDO (ISIA-104) ───────────────────────────────
# Liga T1: J01(T) + labs J02(cerrado) + J03(libre)
sid = ins_seccion("ISIA-104","T1","T","5568","J01","000046447",56,47,0)
ins_horario(sid,"MIE","07:00","08:45","G609","PG")

sid = ins_seccion("ISIA-104","T1","L","5569","J02","000046447",25,25,1)  # cerrado
ins_horario(sid,"JUE","07:00","08:45","G801","PG")

sid = ins_seccion("ISIA-104","T1","L","8433","J03","000046447",25,22,0)
ins_horario(sid,"VIE","07:00","08:45","G801","PG")

# Liga T2: J04(T) cerrado + labs J05(cerrado) + J06(libre)
sid = ins_seccion("ISIA-104","T2","T","8434","J04","000046447",56,56,1)  # cerrado
ins_horario(sid,"LUN","07:00","08:45","G702","PG")

sid = ins_seccion("ISIA-104","T2","L","8435","J05","000046447",32,32,1)  # cerrado
ins_horario(sid,"MAR","07:00","08:45","G601","PG")

sid = ins_seccion("ISIA-104","T2","L","12540","J06","000046447",29,24,0)
ins_horario(sid,"MIE","12:30","14:15","G801","PG")

# ── SGBD (ICSI-521) ──────────────────────────────────────────────
# Liga T1: J01(T) + J02/J03(L)
sid = ins_seccion("ICSI-521","T1","T","5581","J01","000005119",51,51,1)
ins_horario(sid,"LUN","07:00","08:45","G706","PG")

sid = ins_seccion("ICSI-521","T1","L","5582","J02","000005119",32,31,0)
ins_horario(sid,"LUN","08:50","12:25","G401","PG")

sid = ins_seccion("ICSI-521","T1","L","6461","J03","000005119",20,20,1)
ins_horario(sid,"LUN","16:10","19:45","F402","PF")

# Liga T2: J04(T) + J05/J06(L)
sid = ins_seccion("ICSI-521","T2","T","5583","J04","000005119",60,53,0)
ins_horario(sid,"MIE","07:00","08:45","G506","PG")

sid = ins_seccion("ICSI-521","T2","L","5584","J05","000005119",32,31,0)
ins_horario(sid,"MIE","08:50","12:25","G601","PG")

sid = ins_seccion("ICSI-521","T2","L","8432","J06","000005119",25,22,0)
ins_horario(sid,"MIE","16:10","19:45","G601","PG")

# Liga T3: J09(T) + J10(L)
sid = ins_seccion("ICSI-521","T3","T","12510","J09","000029331",60,26,0)
ins_horario(sid,"MIE","16:10","17:55","G706","PG")

sid = ins_seccion("ICSI-521","T3","L","12511","J10","000029331",30,26,0)
ins_horario(sid,"SAB","10:40","14:15","G401","PG")

# ── INGENIERÍA DEL SOFTWARE (ISIA-105) ───────────────────────────
# Liga T1: J01(T) + J02(P) + J03(cerrado)/J04(libre)
sid = ins_seccion("ISIA-105","T1","T","5570","J01","000006276",56,49,0)
ins_horario(sid,"MAR","07:00","08:45","G702","PG")

sid = ins_seccion("ISIA-105","T1","P","5571","J02","000000355",56,49,0)
ins_horario(sid,"MAR","08:50","10:35","G702","PG")

sid = ins_seccion("ISIA-105","T1","L","5572","J03","000000355",32,32,1)
ins_horario(sid,"MAR","10:40","12:25","G801","PG")

sid = ins_seccion("ISIA-105","T1","L","5573","J04","000000355",28,17,0)
ins_horario(sid,"MAR","12:30","14:15","G801","PG")

# Liga T2: J05(T) + J06(P) + J08/J09(L)
sid = ins_seccion("ISIA-105","T2","T","5574","J05","000006276",56,48,0)
ins_horario(sid,"JUE","07:00","08:45","G703","PG")

sid = ins_seccion("ISIA-105","T2","P","5575","J06","000000355",56,48,0)
ins_horario(sid,"JUE","08:50","10:35","G703","PG")

sid = ins_seccion("ISIA-105","T2","L","5576","J08","000000355",31,30,0)
ins_horario(sid,"JUE","10:40","12:25","G601","PG")

sid = ins_seccion("ISIA-105","T2","L","12512","J09","000000355",28,18,0)
ins_horario(sid,"JUE","12:30","14:15","G801","PG")

# ── PATRONES DE DISEÑO (ICSI-675) ────────────────────────────────
# Liga T1: J01(T) + J02(cerrado)/J03(libre)
sid = ins_seccion("ICSI-675","T1","T","12513","J01","000000580",50,42,0)
ins_horario(sid,"JUE","08:50","10:35","G804","PG")

sid = ins_seccion("ICSI-675","T1","L","12514","J02","000000580",27,27,1)
ins_horario(sid,"JUE","10:40","14:15","G401","PG")

sid = ins_seccion("ICSI-675","T1","L","12515","J03","000149608",25,15,0)
ins_horario(sid,"SAB","08:50","12:25","G301","PG")

# Liga T2: J04(T) + J05(cerrado)/J06(libre)
sid = ins_seccion("ICSI-675","T2","T","12516","J04","000000580",50,46,0)
ins_horario(sid,"VIE","08:50","10:35","G607","PG")

sid = ins_seccion("ICSI-675","T2","L","12517","J05","000000580",31,31,1)
ins_horario(sid,"VIE","10:40","14:15","G801","PG")

sid = ins_seccion("ICSI-675","T2","L","12518","J06","000149608",25,15,0)
ins_horario(sid,"SAB","16:10","19:45","G301","PG")

# ── APRENDIZAJE ESTADÍSTICO (ISIA-106) ───────────────────────────
# Liga T1: J01(T) + J02/J03(L)
sid = ins_seccion("ISIA-106","T1","T","5562","J01","000000591",60,59,0)
ins_horario(sid,"MIE","08:50","10:35","G704","PG")

sid = ins_seccion("ISIA-106","T1","L","5563","J02","000000591",33,32,0)
ins_horario(sid,"MIE","10:40","12:25","G401","PG")

sid = ins_seccion("ISIA-106","T1","L","5564","J03","000000591",30,27,0)
ins_horario(sid,"MIE","12:30","14:15","G401","PG")

# Liga T2: J04(T) cerrado + J05(cerrado)/J06(libre)
sid = ins_seccion("ISIA-106","T2","T","5565","J04","000000591",60,60,1)
ins_horario(sid,"MAR","08:50","10:35","G602","PG")

sid = ins_seccion("ISIA-106","T2","L","5566","J05","000000591",31,31,1)
ins_horario(sid,"MAR","10:40","12:25","G501","PG")

sid = ins_seccion("ISIA-106","T2","L","5567","J06","000000591",30,29,0)
ins_horario(sid,"MAR","12:30","14:15","G501","PG")

# ── VIGENCIA ORREGO (HUMA-1183) — subset de secciones disponibles ─
# Liga N3: MIE mañana
sid = ins_seccion("HUMA-1183","N3","T","13073","N03","000115077",50,49,0)
ins_horario(sid,"MIE","08:50","09:40","G206","PG")
sid = ins_seccion("HUMA-1183","N3","P","13074","N04","000115077",50,49,0)
ins_horario(sid,"MIE","09:45","11:30","G206","PG")
# Liga Q1: VIE tarde
sid = ins_seccion("HUMA-1183","Q1","T","1437","Q01","000115077",50,47,0)
ins_horario(sid,"VIE","14:20","15:10","G203","PG")
sid = ins_seccion("HUMA-1183","Q1","P","1438","Q02","000115077",50,47,0)
ins_horario(sid,"VIE","15:15","17:00","G203","PG")
# Liga V1: SAB tarde
sid = ins_seccion("HUMA-1183","V1","T","2646","V01","000102226",50,21,0)
ins_horario(sid,"SAB","14:20","15:10","G101","PG")
sid = ins_seccion("HUMA-1183","V1","P","2647","V02","000102226",50,21,0)
ins_horario(sid,"SAB","15:15","17:00","G101","PG")
# Liga B1: MIE noche
sid = ins_seccion("HUMA-1183","B1","T","3161","B01","000032392",50,46,0)
ins_horario(sid,"MIE","18:55","19:45","D305","PD")
sid = ins_seccion("HUMA-1183","B1","P","3162","B02","000032392",50,46,0)
ins_horario(sid,"MIE","19:50","21:35","D305","PD")
# Liga L2: LUN noche
sid = ins_seccion("HUMA-1183","L2","T","4428","L03","000121730",50,40,0)
ins_horario(sid,"LUN","18:55","19:45","G506","PG")
sid = ins_seccion("HUMA-1183","L2","P","4429","L04","000121730",50,40,0)
ins_horario(sid,"LUN","19:50","21:35","G506","PG")
# Liga N1: MIE mediodia
sid = ins_seccion("HUMA-1183","N1","T","7173","N01","000127846",50,28,0)
ins_horario(sid,"MIE","11:35","12:25","G104","PG")
sid = ins_seccion("HUMA-1183","N1","P","7174","N02","000127846",50,28,0)
ins_horario(sid,"MIE","12:30","14:15","G104","PG")

# ── MEDIO AMBIENTE (CIEN-746) — subset disponibles ────────────────
# Liga Q1: SAB mañana
sid = ins_seccion("CIEN-746","Q1","T","1448","Q01","000000811",50,49,0)
ins_horario(sid,"SAB","07:00","08:45","G105","PG")
sid = ins_seccion("CIEN-746","Q1","P","1449","Q02","000000811",50,49,0)
ins_horario(sid,"SAB","08:50","10:35","G105","PG")
# Liga H1: MAR+VIE mañana
sid = ins_seccion("CIEN-746","H1","T","3496","H01","000000489",57,56,0)
ins_horario(sid,"MAR","10:40","12:25","G702","PG")
sid = ins_seccion("CIEN-746","H1","P","3497","H02","000000489",57,56,0)
ins_horario(sid,"VIE","07:00","08:45","G704","PG")
# Liga J1: VIE mañana
sid = ins_seccion("CIEN-746","J1","T","5577","J01","000000355",50,49,0)
ins_horario(sid,"VIE","08:50","10:35","C408","PC")
sid = ins_seccion("CIEN-746","J1","P","5578","J02","000000355",50,49,0)
ins_horario(sid,"VIE","10:40","12:25","C408","PC")
# Liga J2: LUN tarde/noche
sid = ins_seccion("CIEN-746","J2","T","5579","J03","000000355",53,53,1)
ins_horario(sid,"LUN","16:10","17:55","C402","PC")
sid = ins_seccion("CIEN-746","J2","P","5580","J04","000000355",55,53,0)
ins_horario(sid,"LUN","18:00","19:45","G802","PG")
# Liga N2: SAB tarde
sid = ins_seccion("CIEN-746","N2","T","6800","N03","000000811",50,43,0)
ins_horario(sid,"SAB","14:20","16:05","G307","PG")
sid = ins_seccion("CIEN-746","N2","P","6801","N04","000000811",50,43,0)
ins_horario(sid,"SAB","16:10","17:55","G307","PG")
# Liga J3: JUE tarde
sid = ins_seccion("CIEN-746","J3","T","8442","J05","000051007",54,52,0)
ins_horario(sid,"JUE","14:20","16:05","G406","PG")
sid = ins_seccion("CIEN-746","J3","P","8443","J06","000051007",54,52,0)
ins_horario(sid,"JUE","16:10","17:55","G406","PG")

conn.commit()

# ══════════════════════════════════════════════
# VERIFICACIÓN
# ══════════════════════════════════════════════
print("\n=== VERIFICACIÓN FINAL ===")
for tabla in ["estudiantes", "cursos", "docentes", "historial", "secciones", "horarios"]:
    n = c.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    print(f"  {tabla:20s}: {n} filas")

# Stats del estudiante
aprobados = c.execute("""
    SELECT COUNT(*), SUM(h.nota * h.creditos_hora), SUM(h.creditos_hora)
    FROM historial h JOIN estudiantes e ON h.estudiante_id=e.id
    WHERE e.codigo='000287948' AND h.estado='aprobado'
""").fetchone()
print(f"\n  Créditos aprobados : {aprobados[2]}")
print(f"  Puntos de calidad  : {aprobados[1]}")
print(f"  Promedio ponderado : {aprobados[1]/aprobados[2]:.2f}")

conn.close()
print(f"\n✅ BD guardada en: {db_path}")
