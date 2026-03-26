import schedule
import threading
import time
from contextlib import closing
import os
import csv
import shutil
from utils.common.rutasarchivos import resource_path
from services.security.apis.conexiones.connection import Connection

# ─── Configuración global ──────────────────────────────────────────────────────
CHUNK_SIZE = 50000
BASE_DIR = "Respaldo"
BUFFER_SIZE = 1024 * 1024
DB_TYPES = ['sqlite', 'sqlserver', 'mysql', 'csv']

# ─── Mapeo de tipos SQL Server → tipo interno ─────────────────────────────────
SQLSERVER_TYPE_MAP = {
    'int':           'INTEGER',
    'bigint':        'INTEGER',
    'smallint':      'INTEGER',
    'tinyint':       'INTEGER',
    'bit':           'BOOLEAN',
    'float':         'REAL',
    'real':          'REAL',
    'decimal':       'NUMERIC',
    'numeric':       'NUMERIC',
    'money':         'NUMERIC',
    'smallmoney':    'NUMERIC',
    'nvarchar':      'TEXT',
    'varchar':       'TEXT',
    'nchar':         'TEXT',
    'char':          'TEXT',
    'text':          'TEXT',
    'ntext':         'TEXT',
    'date':          'DATE',
    'datetime':      'DATETIME',
    'datetime2':     'DATETIME',
    'smalldatetime': 'DATETIME',
    'varbinary':     'BLOB',
    'binary':        'BLOB',
    'image':         'BLOB',
}

# ─── Mapeo de tipo interno → tipo de salida por motor ─────────────────────────
TYPE_MAP = {
    'INTEGER': {
        'sqlite':    'INTEGER PRIMARY KEY AUTOINCREMENT',
        'sqlserver': 'INT IDENTITY(1,1) PRIMARY KEY',
        'mysql':     'INT AUTO_INCREMENT PRIMARY KEY',
        'csv':       'INTEGER'
    },
    'TEXT': {
        'sqlite':    'TEXT',
        'sqlserver': 'NVARCHAR(MAX)',
        'mysql':     'VARCHAR(545) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci',
        'csv':       'TEXT'
    },
    'REAL': {
        'sqlite':    'REAL',
        'sqlserver': 'FLOAT',
        'mysql':     'DOUBLE',
        'csv':       'REAL'
    },
    'NUMERIC': {
        'sqlite':    'NUMERIC',
        'sqlserver': 'DECIMAL(38,10)',
        'mysql':     'DECIMAL(38,10)',
        'csv':       'NUMERIC'
    },
    'BOOLEAN': {
        'sqlite':    'BOOLEAN',
        'sqlserver': 'BIT',
        'mysql':     'BOOLEAN',
        'csv':       'BOOLEAN'
    },
    'BLOB': {
        'sqlite':    'BLOB',
        'sqlserver': 'VARBINARY(MAX)',
        'mysql':     'LONGBLOB',
        'csv':       'BLOB'
    },
    'DATE': {
        'sqlite':    'TEXT',
        'sqlserver': 'DATE',
        'mysql':     'DATE',
        'csv':       'DATE'
    },
    'DATETIME': {
        'sqlite':    'TEXT',
        'sqlserver': 'DATETIME2',
        'mysql':     'DATETIME',
        'csv':       'DATETIME'
    }
}


def get_connection():
    """Obtiene conexión usando la clase Connection del proyecto."""
    conn = Connection.connectionDB()
    if conn is None:
        raise ConnectionError("No se pudo establecer conexión con SQL Server. Verifique las variables de entorno.")
    return conn


class ExportarDatos:

    # ─── Introspección ────────────────────────────────────────────────────────

    def tabla_existe(cursor, nombre_tabla):
        """Devuelve True si la tabla existe en SQL Server."""
        cursor.execute(
            "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME=?",
            (nombre_tabla,)
        )
        return cursor.fetchone() is not None

    def obtener_info_columnas(cursor, tabla):
        """
        Devuelve lista de (nombre, tipo_interno, not_null, es_pk)
        equivalente al PRAGMA table_info de SQLite.
        """
        cursor.execute("""
            SELECT
                c.COLUMN_NAME,
                c.DATA_TYPE,
                CASE WHEN c.IS_NULLABLE = 'NO' THEN 1 ELSE 0 END
            FROM INFORMATION_SCHEMA.COLUMNS c
            WHERE c.TABLE_NAME = ?
            ORDER BY c.ORDINAL_POSITION
        """, (tabla,))
        columnas = cursor.fetchall()

        cursor.execute("""
            SELECT kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
              AND tc.TABLE_NAME = ?
        """, (tabla,))
        pks = {row[0] for row in cursor.fetchall()}

        return [
            (nombre, SQLSERVER_TYPE_MAP.get(tipo.lower(), 'TEXT'), not_null, 1 if nombre in pks else 0)
            for nombre, tipo, not_null in columnas
        ]

    # ─── Programación ─────────────────────────────────────────────────────────

    def programar_exportacion():
        def eliminar_carpeta_exportados():
            ruta = resource_path(BASE_DIR)
            if os.path.exists(ruta):
                shutil.rmtree(ruta)

        exportaciones = [
            ExportarDatos.exportar_prismas,
            ExportarDatos.exportar_inclinometros_rst,
            ExportarDatos.exportar_inclinometros_gkn,
            ExportarDatos.exportar_piezometros_manuales,
            ExportarDatos.exportar_piezometros_cuerda,
            ExportarDatos.exportar_celdas_asentamiento,
        ]

        for hora in ["00:00", "08:00", "16:35"]:
            schedule.every().day.at(hora).do(eliminar_carpeta_exportados)
            for fn in exportaciones:
                schedule.every().day.at(hora).do(
                    lambda f=fn: ExportarDatos._ejecutar_seguro(f)
                )

        def loop():
            while True:
                schedule.run_pending()
                time.sleep(1)

        threading.Thread(target=loop, daemon=True).start()

    def _ejecutar_seguro(fn):
        try:
            fn()
        except Exception as e:
            print(f"[ExportarDatos] Error en {fn.__name__}: {e}")

    # ─── Exportadores ─────────────────────────────────────────────────────────

    def exportar_prismas():
        ExportarDatos.exportar_tablas_por_patron('prismas%')

    def exportar_tablas_por_patron(patron):
        try:
            conn = get_connection()
            with closing(conn):
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME LIKE ?",
                    (patron,)
                )
                tablas = [row[0] for row in cursor.fetchall()]

                for tabla in tablas:
                    directorios = ExportarDatos.crear_directorios(tabla)
                    for tipo_db in DB_TYPES:
                        dir_actual = directorios[tipo_db]
                        if tipo_db != 'csv':
                            ExportarDatos.generar_esquema(tipo_db, tabla, cursor, dir_actual)
                        if tabla.lower().startswith('prisma'):
                            if tipo_db == 'csv':
                                ExportarDatos.generar_datos_prismas_csv(tabla, cursor, dir_actual)
                            else:
                                ExportarDatos.generar_datos_prismas_sql(tipo_db, tabla, cursor, dir_actual)
                        else:
                            if tipo_db == 'csv':
                                ExportarDatos.generar_datos_csv(tabla, cursor, dir_actual)
                            else:
                                ExportarDatos.generar_datos_sql(tipo_db, tabla, cursor, dir_actual)
        except Exception as e:
            print(f"[ExportarDatos] Error en exportar_tablas_por_patron: {e}")
            raise

    def exportar_piezometros_manuales():
        tabla_maestra = 'piezometromanuales'
        try:
            conn = get_connection()
            with closing(conn):
                cursor = conn.cursor()
                if not ExportarDatos.tabla_existe(cursor, tabla_maestra):
                    print(f"[ExportarDatos] '{tabla_maestra}' no existe. Se omite.")
                    return
                cursor.execute(
                    "SELECT id_piezometro, "
                    "CONCAT('piezometromanual_detalle', CAST(id_proyecto AS NVARCHAR)) "
                    "FROM piezometromanuales"
                )
                tablas_dinamicas = cursor.fetchall()
        except Exception as e:
            print(f"[ExportarDatos] Error leyendo '{tabla_maestra}': {e}")
            return

        for id_piezometro, detalle in tablas_dinamicas:
            try:
                conn = get_connection()
                with closing(conn):
                    cursor = conn.cursor()
                    if not ExportarDatos.tabla_existe(cursor, detalle):
                        print(f"[ExportarDatos] Tabla '{detalle}' no existe. Se omite.")
                        continue
                    consulta = f"""
                        SELECT pm.nombre_piezometro,
                            pmd.fecha_piezometro,
                            pmd.medida_piezometro,
                            pmd.observacion_detalle
                        FROM piezometromanuales pm
                        INNER JOIN [{detalle}] pmd ON pm.id_piezometro = pmd.id_piezometro
                        WHERE pm.id_piezometro = ?
                        ORDER BY pm.nombre_piezometro, pmd.fecha_piezometro
                    """
                    directorios = ExportarDatos.crear_directorios('piezometros_casagrande')
                    for tipo_db in DB_TYPES:
                        dir_actual = directorios[tipo_db]
                        if tipo_db != 'csv':
                            ExportarDatos.generar_esquema(tipo_db, 'piezometros_casagrande', cursor, dir_actual)
                        if tipo_db == 'csv':
                            ExportarDatos.generar_datos_csv('piezometros_casagrande', cursor, dir_actual, consulta, (id_piezometro,))
                        else:
                            ExportarDatos.generar_datos_sql(tipo_db, 'piezometros_casagrande', cursor, dir_actual, consulta, (id_piezometro,))
            except Exception as e:
                print(f"[ExportarDatos] Error exportando piezómetro manual id={id_piezometro}: {e}")

    def exportar_piezometros_cuerda():
        tabla_maestra = 'piezometrocuerdas'
        try:
            conn = get_connection()
            with closing(conn):
                cursor = conn.cursor()
                if not ExportarDatos.tabla_existe(cursor, tabla_maestra):
                    print(f"[ExportarDatos] '{tabla_maestra}' no existe. Se omite.")
                    return
                cursor.execute(
                    "SELECT id_piezometro, "
                    "CONCAT('piezometrocuerda_detalle', CAST(id_proyecto AS NVARCHAR)) "
                    "FROM piezometrocuerdas"
                )
                tablas_dinamicas = cursor.fetchall()
        except Exception as e:
            print(f"[ExportarDatos] Error leyendo '{tabla_maestra}': {e}")
            return

        for id_piezometro, detalle in tablas_dinamicas:
            try:
                conn = get_connection()
                with closing(conn):
                    cursor = conn.cursor()
                    if not ExportarDatos.tabla_existe(cursor, detalle):
                        print(f"[ExportarDatos] Tabla '{detalle}' no existe. Se omite.")
                        continue
                    consulta = f"""
                        SELECT pzc.nombre_piezometro,
                            pcd.fecha_cuerda,
                            pcd.frecuencia_cuerda,
                            pcd.temperatura_cuerda,
                            pcd.presion_barometrica,
                            pcd.medida_calculada,
                            pcd.observacion_cuerda
                        FROM piezometrocuerdas pzc
                        INNER JOIN [{detalle}] pcd ON pzc.id_piezometro = pcd.id_piezometro
                        WHERE pzc.id_piezometro = ?
                        ORDER BY pzc.nombre_piezometro, pcd.fecha_cuerda
                    """
                    directorios = ExportarDatos.crear_directorios('piezometros_cuerda')
                    for tipo_db in DB_TYPES:
                        dir_actual = directorios[tipo_db]
                        if tipo_db != 'csv':
                            ExportarDatos.generar_esquema(tipo_db, 'piezometros_cuerda', cursor, dir_actual)
                        if tipo_db == 'csv':
                            ExportarDatos.generar_datos_csv('piezometros_cuerda', cursor, dir_actual, consulta, (id_piezometro,))
                        else:
                            ExportarDatos.generar_datos_sql(tipo_db, 'piezometros_cuerda', cursor, dir_actual, consulta, (id_piezometro,))
            except Exception as e:
                print(f"[ExportarDatos] Error exportando piezómetro cuerda id={id_piezometro}: {e}")

    def exportar_inclinometros_rst():
        ExportarDatos._exportar_inclinometros('RST', 'inclinometros_rst')

    def exportar_inclinometros_gkn():
        ExportarDatos._exportar_inclinometros('GEOKON', 'inclinometros_gkn')

    def _exportar_inclinometros(tipo, carpeta):
        tabla_maestra = 'inclinometros'
        try:
            conn = get_connection()
            with closing(conn):
                cursor = conn.cursor()
                if not ExportarDatos.tabla_existe(cursor, tabla_maestra):
                    print(f"[ExportarDatos] '{tabla_maestra}' no existe. Se omite.")
                    return
                cursor.execute("""
                    SELECT DISTINCT incli.id_inclinometro,
                        CONCAT('inclinometro_detalle', CAST(incli.id_proyecto AS NVARCHAR))
                    FROM inclinometros incli
                    WHERE incli.tipo_inclinometro = ?
                """, (tipo,))
                tablas_dinamicas = cursor.fetchall()
        except Exception as e:
            print(f"[ExportarDatos] Error leyendo inclinómetros ({tipo}): {e}")
            return

        for id_inclinometro, detail_inclinometro in tablas_dinamicas:
            try:
                conn = get_connection()
                with closing(conn):
                    cursor = conn.cursor()
                    if not ExportarDatos.tabla_existe(cursor, detail_inclinometro):
                        print(f"[ExportarDatos] Tabla '{detail_inclinometro}' no existe. Se omite.")
                        continue
                    consulta = f"""
                        SELECT inclideta.id_detalle,
                            incli.nombre_inclinometro,
                            inclien.fecha_inclinometro,
                            inclideta.profundidad_detalle,
                            inclideta.apositivo_detalle,
                            inclideta.anegativo_detalle,
                            inclideta.bpositivo_detalle,
                            inclideta.bnegativo_detalle
                        FROM inclinometros incli
                        INNER JOIN inclinometro_encabezado inclien
                            ON incli.id_inclinometro = inclien.id_inclinometro
                        INNER JOIN [{detail_inclinometro}] inclideta
                            ON inclien.id_encabezado = inclideta.id_encabezado
                        WHERE incli.id_inclinometro = ?
                        ORDER BY incli.nombre_inclinometro, inclien.fecha_inclinometro
                    """
                    directorios = ExportarDatos.crear_directorios(carpeta)
                    for tipo_db in DB_TYPES:
                        dir_actual = directorios[tipo_db]
                        if tipo_db != 'csv':
                            ExportarDatos.generar_esquema(tipo_db, 'inclinometros', cursor, dir_actual)
                        if tipo_db == 'csv':
                            ExportarDatos.generar_datos_csv('inclinometros', cursor, dir_actual, consulta, (id_inclinometro,))
                        else:
                            ExportarDatos.generar_datos_sql(tipo_db, 'inclinometros', cursor, dir_actual, consulta, (id_inclinometro,))
            except Exception as e:
                print(f"[ExportarDatos] Error exportando inclinómetro {tipo} id={id_inclinometro}: {e}")

    def exportar_celdas_asentamiento():
        tabla_maestra = 'celdas'
        try:
            conn = get_connection()
            with closing(conn):
                cursor = conn.cursor()
                if not ExportarDatos.tabla_existe(cursor, tabla_maestra):
                    print(f"[ExportarDatos] '{tabla_maestra}' no existe. Se omite.")
                    return
                cursor.execute(
                    "SELECT id_celda, "
                    "CONCAT('celda_detalle', CAST(id_proyecto AS NVARCHAR)) "
                    "FROM celdas"
                )
                tablas_dinamicas = cursor.fetchall()
        except Exception as e:
            print(f"[ExportarDatos] Error leyendo '{tabla_maestra}': {e}")
            return

        for id_celda, detalle in tablas_dinamicas:
            try:
                conn = get_connection()
                with closing(conn):
                    cursor = conn.cursor()
                    if not ExportarDatos.tabla_existe(cursor, detalle):
                        print(f"[ExportarDatos] Tabla '{detalle}' no existe. Se omite.")
                        continue
                    consulta = f"""
                        SELECT c.nombre_celda,
                            cd.fecha_detalle,
                            cd.frecuencia_digits,
                            cd.frecuencia_hz,
                            cd.temperatura_detalle,
                            cd.medida_calculada
                        FROM celdas c
                        INNER JOIN [{detalle}] cd ON c.id_celda = cd.id_celda
                        WHERE c.id_celda = ?
                        ORDER BY c.nombre_celda, cd.fecha_detalle
                    """
                    directorios = ExportarDatos.crear_directorios('celdas_asentamiento')
                    for tipo_db in DB_TYPES:
                        dir_actual = directorios[tipo_db]
                        if tipo_db != 'csv':
                            ExportarDatos.generar_esquema(tipo_db, 'celdas', cursor, dir_actual)
                        if tipo_db == 'csv':
                            ExportarDatos.generar_datos_csv('celdas', cursor, dir_actual, consulta, (id_celda,))
                        else:
                            ExportarDatos.generar_datos_sql(tipo_db, 'celdas', cursor, dir_actual, consulta, (id_celda,))
            except Exception as e:
                print(f"[ExportarDatos] Error exportando celda id={id_celda}: {e}")

    # ─── Helpers de archivos ──────────────────────────────────────────────────

    def crear_directorios(tabla):
        base_dir = resource_path(BASE_DIR)
        estructura = {
            'base':      os.path.join(base_dir, tabla),
            'sqlite':    os.path.join(base_dir, tabla, 'sqlite'),
            'sqlserver': os.path.join(base_dir, tabla, 'sqlserver'),
            'mysql':     os.path.join(base_dir, tabla, 'mysql'),
            'csv':       os.path.join(base_dir, tabla, 'csv')
        }
        for d in estructura.values():
            os.makedirs(d, exist_ok=True)
        return estructura

    def obtener_quoter(tipo_db):
        return {
            'sqlite':    lambda x: f'"{x}"',
            'sqlserver': lambda x: f'[{x}]',
            'mysql':     lambda x: f'`{x}`',
            'csv':       lambda x: f'"{x}"'
        }[tipo_db]

    def formatear_valor(valor, tipo_col, tipo_db):
        if valor is None:
            return 'NULL' if tipo_db != 'csv' else ''
        if isinstance(valor, (bytes, bytearray)):
            return f"X'{valor.hex()}'" if tipo_db != 'csv' else valor.hex()
        if isinstance(valor, bool):
            return ('1' if valor else '0') if tipo_db != 'csv' else ('TRUE' if valor else 'FALSE')
        if isinstance(valor, str):
            valor = valor.replace("'", "''")
            if tipo_db == 'mysql' and any(ord(c) > 154 for c in valor):
                return f"_utf8mb4 '{valor}'"
            return f"'{valor}'" if tipo_db != 'csv' else valor
        # datetime, date, Decimal, int, float → siempre con comillas en SQL
        if tipo_db != 'csv':
            return f"'{valor}'"
        return str(valor)

    def generar_esquema(tipo_db, tabla, cursor, directorio):
        try:
            columnas = ExportarDatos.obtener_info_columnas(cursor, tabla)
        except Exception as e:
            print(f"[ExportarDatos] No se pudo obtener esquema de '{tabla}': {e}")
            return
        if not columnas:
            return

        quoter = ExportarDatos.obtener_quoter(tipo_db)
        nombre_archivo = f"{tabla}_{tipo_db}_schema.sql"
        ruta = resource_path(os.path.join(directorio, nombre_archivo))

        with open(ruta, 'w', encoding='utf-8') as f:
            if tipo_db in ['sqlserver', 'mysql']:
                f.write(f"DROP TABLE IF EXISTS {quoter(tabla)};\n")
            f.write(f"CREATE TABLE {quoter(tabla)} (\n")
            definiciones = []
            pk_cols = []
            for nombre, tipo_interno, not_null, es_pk in columnas:
                tipo_salida = TYPE_MAP.get(tipo_interno, {}).get(tipo_db, 'TEXT')
                constraints = []
                if not_null:
                    constraints.append('NOT NULL')
                if es_pk:
                    pk_cols.append(quoter(nombre))
                    if tipo_db == 'csv' or len(pk_cols) > 1:
                        constraints = [c for c in constraints if c != 'PRIMARY KEY']
                definicion = f"    {quoter(nombre)} {tipo_salida}"
                if constraints:
                    definicion += f" {' '.join(constraints)}"
                definiciones.append(definicion.strip())
            if pk_cols and (tipo_db == 'csv' or len(pk_cols) > 1):
                definiciones.append(f'    PRIMARY KEY ({", ".join(pk_cols)})')
            f.write(',\n'.join(definiciones))
            if tipo_db == 'mysql':
                f.write('\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n')
            else:
                f.write('\n);\n')

    def generar_datos_sql(tipo_db, tabla, cursor, directorio, consulta=None, parametros=None):
        quoter = ExportarDatos.obtener_quoter(tipo_db)
        if consulta:
            cursor.execute(consulta, parametros)
            nombres_col = [desc[0] for desc in cursor.description]
            tipos_col = [None] * len(nombres_col)
        else:
            info = ExportarDatos.obtener_info_columnas(cursor, tabla)
            nombres_col = [c[0] for c in info]
            tipos_col = [c[1] for c in info]
            cursor.execute(f"SELECT * FROM [{tabla}]")

        chunk_number = 1
        while True:
            nombre_archivo = f"{tabla}_{tipo_db}_data_chunk_{chunk_number}.sql"
            ruta = resource_path(os.path.join(directorio, nombre_archivo))
            primera_vez = not os.path.exists(ruta)

            with open(ruta, 'a+' if not primera_vez else 'w+', encoding='utf-8', buffering=BUFFER_SIZE) as f:
                if primera_vez:
                    f.write(f"INSERT INTO {quoter(tabla)} ({', '.join(quoter(n) for n in nombres_col)})\nVALUES\n")
                else:
                    f.seek(0)
                    contenido = f.read()
                    if contenido.strip().endswith(';'):
                        contenido = contenido.rstrip(';\n') + ',\n'
                        f.seek(0); f.truncate(); f.write(contenido)

                primera_iteracion = True
                registros_procesados = 0
                while registros_procesados < CHUNK_SIZE:
                    registros = cursor.fetchmany(500)
                    if not registros:
                        break
                    valores = [
                        f"({', '.join(ExportarDatos.formatear_valor(r[i], tipos_col[i], tipo_db) for i in range(len(nombres_col)))})"
                        for r in registros
                    ]
                    if primera_iteracion:
                        f.write(',\n'.join(valores))
                        primera_iteracion = False
                    else:
                        f.write(',\n' + ',\n'.join(valores))
                    registros_procesados += len(registros)

                f.seek(0, os.SEEK_END)
                if f.tell() > 0:
                    f.seek(f.tell() - 1)
                    if f.read(1) == ',':
                        f.seek(f.tell() - 1); f.truncate()
                f.write(';\n')

            if registros_procesados < CHUNK_SIZE:
                break
            chunk_number += 1

    def generar_datos_csv(tabla, cursor, directorio, consulta=None, parametros=None):
        if consulta:
            cursor.execute(consulta, parametros)
            nombres_col = [desc[0] for desc in cursor.description]
        else:
            info = ExportarDatos.obtener_info_columnas(cursor, tabla)
            nombres_col = [c[0] for c in info]
            cursor.execute(f"SELECT * FROM [{tabla}]")

        chunk_number = 1
        while True:
            nombre_archivo = f"{tabla}_csv_data_chunk_{chunk_number}.csv"
            ruta = resource_path(os.path.join(directorio, nombre_archivo))
            primera_vez = not os.path.exists(ruta)

            with open(ruta, 'a', encoding='utf-8-sig', newline='', buffering=BUFFER_SIZE) as f:
                escritor = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL)
                if primera_vez:
                    escritor.writerow(nombres_col)

                registros_procesados = 0
                while registros_procesados < CHUNK_SIZE:
                    registros = cursor.fetchmany(500)
                    if not registros:
                        break
                    for registro in registros:
                        fila = [
                            valor.hex() if isinstance(valor, (bytes, bytearray))
                            else ('TRUE' if valor else 'FALSE') if isinstance(valor, bool)
                            else (str(valor) if valor is not None else '')
                            for valor in registro
                        ]
                        escritor.writerow(fila)
                    registros_procesados += len(registros)

            if registros_procesados < CHUNK_SIZE:
                break
            chunk_number += 1

    def generar_datos_prismas_sql(tipo_db, tabla, cursor, directorio):
        quoter = ExportarDatos.obtener_quoter(tipo_db)
        info = ExportarDatos.obtener_info_columnas(cursor, tabla)
        nombres_col = [c[0] for c in info]
        tipos_col = [c[1] for c in info]

        chunk_number = 1
        while True:
            offset = (chunk_number - 1) * CHUNK_SIZE
            # SQL Server usa OFFSET/FETCH en lugar de LIMIT/OFFSET
            cursor.execute(
                f"SELECT * FROM [{tabla}] ORDER BY (SELECT NULL) "
                f"OFFSET {offset} ROWS FETCH NEXT {CHUNK_SIZE} ROWS ONLY"
            )
            registros = cursor.fetchall()
            if not registros:
                break

            nombre_archivo = f"{tabla}_{tipo_db}_data_chunk_{chunk_number}.sql"
            ruta = resource_path(os.path.join(directorio, nombre_archivo))
            primera_vez = not os.path.exists(ruta)

            with open(ruta, 'a+' if not primera_vez else 'w+', encoding='utf-8', buffering=BUFFER_SIZE) as f:
                if primera_vez:
                    f.write(f"INSERT INTO {quoter(tabla)} ({', '.join(quoter(n) for n in nombres_col)})\nVALUES\n")
                else:
                    f.seek(0)
                    contenido = f.read()
                    if contenido.strip().endswith(';'):
                        contenido = contenido.rstrip(';\n') + ',\n'
                        f.seek(0); f.truncate(); f.write(contenido)

                valores = [
                    f"({', '.join(ExportarDatos.formatear_valor(r[i], tipos_col[i], tipo_db) for i in range(len(nombres_col)))})"
                    for r in registros
                ]
                f.write(',\n'.join(valores))
                f.seek(0, os.SEEK_END)
                if f.tell() > 0:
                    f.seek(f.tell() - 1)
                    if f.read(1) == ',':
                        f.seek(f.tell() - 1); f.truncate()
                f.write(';\n')

            if len(registros) < CHUNK_SIZE:
                break
            chunk_number += 1

    def generar_datos_prismas_csv(tabla, cursor, directorio):
        info = ExportarDatos.obtener_info_columnas(cursor, tabla)
        nombres_col = [c[0] for c in info]

        chunk_number = 1
        while True:
            offset = (chunk_number - 1) * CHUNK_SIZE
            cursor.execute(
                f"SELECT * FROM [{tabla}] ORDER BY (SELECT NULL) "
                f"OFFSET {offset} ROWS FETCH NEXT {CHUNK_SIZE} ROWS ONLY"
            )
            registros = cursor.fetchall()
            if not registros:
                break

            nombre_archivo = f"{tabla}_csv_data_chunk_{chunk_number}.csv"
            ruta = resource_path(os.path.join(directorio, nombre_archivo))
            primera_vez = not os.path.exists(ruta)

            with open(ruta, 'a', encoding='utf-8-sig', newline='', buffering=BUFFER_SIZE) as f:
                escritor = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL)
                if primera_vez:
                    escritor.writerow(nombres_col)
                for registro in registros:
                    fila = [
                        valor.hex() if isinstance(valor, (bytes, bytearray))
                        else ('TRUE' if valor else 'FALSE') if isinstance(valor, bool)
                        else (str(valor) if valor is not None else '')
                        for valor in registro
                    ]
                    escritor.writerow(fila)

            if len(registros) < CHUNK_SIZE:
                break
            chunk_number += 1
    