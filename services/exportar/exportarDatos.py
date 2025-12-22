import schedule
import threading
import time
from contextlib import closing
import sqlite3
import os
import csv
import shutil 
from utils.common.rutasarchivos import resource_path
# Configuración global
CHUNK_SIZE = 50000
BASE_DIR = "Respaldo"
BUFFER_SIZE = 1024 * 1024
DB_TYPES = ['sqlite', 'sqlserver', 'mysql', 'csv']

TYPE_MAP = {
    'INTEGER': {
        'sqlite': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'sqlserver': 'INT IDENTITY(1,1) PRIMARY KEY',
        'mysql': 'INT AUTO_INCREMENT PRIMARY KEY',
        'csv': 'INTEGER'
    },
    'TEXT': {
        'sqlite': 'TEXT',
        'sqlserver': 'NVARCHAR(MAX)',
        'mysql': 'VARCHAR(545) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci',
        'csv': 'TEXT'
    },
    'REAL': {
        'sqlite': 'REAL',
        'sqlserver': 'FLOAT',
        'mysql': 'DOUBLE',
        'csv': 'REAL'
    },
    'NUMERIC': {
        'sqlite': 'NUMERIC',
        'sqlserver': 'DECIMAL(38,10)',
        'mysql': 'DECIMAL(38,10)',
        'csv': 'NUMERIC'
    },
    'BOOLEAN': {
        'sqlite': 'BOOLEAN',
        'sqlserver': 'BIT',
        'mysql': 'BOOLEAN',
        'csv': 'BOOLEAN'
    },
    'BLOB': {
        'sqlite': 'BLOB',
        'sqlserver': 'VARBINARY(MAX)',
        'mysql': 'LONGBLOB',
        'csv': 'BLOB'
    },
    'DATE': {
        'sqlite': 'TEXT',
        'sqlserver': 'DATE',
        'mysql': 'DATE',
        'csv': 'DATE'
    },
    'DATETIME': {
        'sqlite': 'TEXT',
        'sqlserver': 'DATETIME2',
        'mysql': 'DATETIME',
        'csv': 'DATETIME'
    }
}

class ExportarDatos:
    
    def programar_exportacion():
        db_path = resource_path('services/database/databaseeigha.db')
        def eliminar_carpeta_exportados():
            if os.path.exists(resource_path(BASE_DIR)):
                shutil.rmtree(resource_path(BASE_DIR))
        # Programar 1 pruebas de pruebas
        # schedule.every().day.at("16:05").do(lambda: eliminar_carpeta_exportados())
        # schedule.every().day.at("16:05").do(lambda: ExportarDatos.exportar_prismas(db_path))
        # schedule.every().day.at("16:05").do(lambda: ExportarDatos.exportar_inclinometros_rst(db_path))
        # schedule.every().day.at("16:05").do(lambda: ExportarDatos.exportar_inclinometros_gkn(db_path))
        # schedule.every().day.at("16:05").do(lambda: ExportarDatos.exportar_piezometros_manuales(db_path))
        # schedule.every().day.at("16:05").do(lambda: ExportarDatos.exportar_piezometros_cuerda(db_path))
        # schedule.every().day.at("16:05").do(lambda: ExportarDatos.exportar_celdas_asentamiento(db_path))
        # Programar 1
        schedule.every().day.at("00:00").do(lambda: eliminar_carpeta_exportados())
        schedule.every().day.at("00:00").do(lambda: ExportarDatos.exportar_prismas(db_path))
        schedule.every().day.at("00:00").do(lambda: ExportarDatos.exportar_inclinometros_rst(db_path))
        schedule.every().day.at("00:00").do(lambda: ExportarDatos.exportar_inclinometros_gkn(db_path))
        schedule.every().day.at("00:00").do(lambda: ExportarDatos.exportar_piezometros_manuales(db_path))
        schedule.every().day.at("00:00").do(lambda: ExportarDatos.exportar_piezometros_cuerda(db_path))
        schedule.every().day.at("00:00").do(lambda: ExportarDatos.exportar_celdas_asentamiento(db_path))
        # Programar 2
        schedule.every().day.at("08:00").do(lambda: eliminar_carpeta_exportados())
        schedule.every().day.at("08:00").do(lambda: ExportarDatos.exportar_prismas(db_path))
        schedule.every().day.at("08:00").do(lambda: ExportarDatos.exportar_inclinometros_rst(db_path))
        schedule.every().day.at("08:00").do(lambda: ExportarDatos.exportar_inclinometros_gkn(db_path))
        schedule.every().day.at("08:00").do(lambda: ExportarDatos.exportar_piezometros_manuales(db_path))
        schedule.every().day.at("08:00").do(lambda: ExportarDatos.exportar_piezometros_cuerda(db_path))
        schedule.every().day.at("08:00").do(lambda: ExportarDatos.exportar_celdas_asentamiento(db_path))
        # Programar 2
        schedule.every().day.at("16:00").do(lambda: eliminar_carpeta_exportados())
        schedule.every().day.at("16:00").do(lambda: ExportarDatos.exportar_prismas(db_path))
        schedule.every().day.at("16:00").do(lambda: ExportarDatos.exportar_inclinometros_rst(db_path))
        schedule.every().day.at("16:00").do(lambda: ExportarDatos.exportar_inclinometros_gkn(db_path))
        schedule.every().day.at("16:00").do(lambda: ExportarDatos.exportar_piezometros_manuales(db_path))
        schedule.every().day.at("16:00").do(lambda: ExportarDatos.exportar_piezometros_cuerda(db_path))
        schedule.every().day.at("16:00").do(lambda: ExportarDatos.exportar_celdas_asentamiento(db_path))
        
        def ejecutar_programacion():
            while True:
                schedule.run_pending()
                time.sleep(1)
        thread = threading.Thread(target=ejecutar_programacion)
        thread.start()
    
    def exportar_tablas_por_patron(db_path, patron):
        try:
            with closing(sqlite3.connect(db_path)) as conn:
                conn.execute("PRAGMA journal_mode = MEMORY")
                cursor = conn.cursor()

                # Obtener todas las tablas que coincidan con el patrón
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (patron,))
                tablas = cursor.fetchall()
                for tabla in tablas:
                    tabla = tabla[0]
                    directorios = ExportarDatos.crear_directorios(tabla)
                    for tipo_db in DB_TYPES:
                        dir_actual = directorios[tipo_db]
                        if tipo_db != 'csv':
                            ExportarDatos.generar_esquema(tipo_db, tabla, cursor, dir_actual)
                        if tabla.startswith('prisma'):
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
            raise
    
    def exportar_prismas(db_path):
        ExportarDatos.exportar_tablas_por_patron(db_path,'prismas%')
    
    def exportar_piezometros_manuales(db_path):
        # Obtener los nombres de las tablas dinámicas
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("PRAGMA journal_mode = MEMORY")
            cursor = conn.cursor()
            cursor.execute("""SELECT id_piezometro, 'piezometromanual_detalle' || id_proyecto AS detalle FROM piezometromanuales""")
            tablas_dinamicas = cursor.fetchall()

        for id_piezometro, detalle in tablas_dinamicas:
            # Verificar si la tabla de detalle existe
            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{detalle}'")
                    if not cursor.fetchone():
                        continue
            except Exception as e:
                continue

            consulta = f"""SELECT pm.nombre_piezometro,
                pmd.fecha_piezometro,
                pmd.medida_piezometro,
                pmd.observacion_detalle
            FROM piezometromanuales pm
            INNER JOIN {detalle} pmd ON pm.id_piezometro = pmd.id_piezometro
            WHERE pm.id_piezometro = ?
            ORDER BY pm.nombre_piezometro, pmd.fecha_piezometro;"""

            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    conn.execute("PRAGMA journal_mode = MEMORY")
                    cursor = conn.cursor()
                    # Crear directorios para piezómetros
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
                raise
    
    def exportar_piezometros_cuerda(db_path):
        # Obtener los nombres de las tablas dinámicas
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("PRAGMA journal_mode = MEMORY")
            cursor = conn.cursor()
            cursor.execute("""SELECT id_piezometro, 'piezometrocuerda_detalle' || id_proyecto AS detalle FROM piezometrocuerdas""")
            tablas_dinamicas = cursor.fetchall()
        for id_piezometro, detalle in tablas_dinamicas:
            # Verificar si la tabla de detalle existe
            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{detalle}'")
                    if not cursor.fetchone():
                        continue
            except Exception as e:
                continue

            consulta = f"""SELECT pzc.nombre_piezometro,
                pcd.fecha_cuerda,
                pcd.frecuencia_cuerda,
                pcd.temperatura_cuerda,
                pcd.presion_barometrica,
                pcd.medida_calculada,
                pcd.observacion_cuerda
            FROM piezometrocuerdas pzc
            INNER JOIN {detalle} pcd ON pzc.id_piezometro = pcd.id_piezometro
            WHERE pzc.id_piezometro = ?
            ORDER BY pzc.nombre_piezometro, pcd.fecha_cuerda;"""
            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    conn.execute("PRAGMA journal_mode = MEMORY")
                    cursor = conn.cursor()
                    # Crear directorios para piezómetros
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
                raise
    
    def exportar_inclinometros_rst(db_path):
        # Obtener los nombres de las tablas dinámicas
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("PRAGMA journal_mode = MEMORY")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT incli.id_inclinometro, 'inclinometro_detalle' || incli.id_proyecto AS detail_inclinometro
                FROM inclinometros incli WHERE incli.tipo_inclinometro = 'RST'
            """)
            tablas_dinamicas = cursor.fetchall()
        for id_inclinometro, detail_inclinometro in tablas_dinamicas:
            # Verificar si la tabla de detalle existe
            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{detail_inclinometro}'")
                    if not cursor.fetchone():
                        continue
            except Exception as e:
                continue

            consulta = f"""SELECT inclideta.id_detalle,
                incli.nombre_inclinometro,
                inclien.fecha_inclinometro,
                inclideta.profundidad_detalle,
                inclideta.apositivo_detalle,
                inclideta.anegativo_detalle,
                inclideta.bpositivo_detalle,
                inclideta.bnegativo_detalle
            FROM inclinometros incli
            INNER JOIN inclinometro_encabezado inclien ON incli.id_inclinometro = inclien.id_inclinometro
            INNER JOIN {detail_inclinometro} inclideta ON inclien.id_encabezado = inclideta.id_encabezado
            WHERE incli.id_inclinometro = ?
            ORDER BY incli.nombre_inclinometro, inclien.fecha_inclinometro;"""

            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    conn.execute("PRAGMA journal_mode = MEMORY")
                    cursor = conn.cursor()
                    # Crear directorios para inclinómetros
                    directorios = ExportarDatos.crear_directorios('inclinometros_rst')
                    for tipo_db in DB_TYPES:
                        dir_actual = directorios[tipo_db]
                        if tipo_db != 'csv':
                            ExportarDatos.generar_esquema(tipo_db, 'inclinometros', cursor, dir_actual)
                        if tipo_db == 'csv':
                            ExportarDatos.generar_datos_csv('inclinometros', cursor, dir_actual, consulta, (id_inclinometro,))
                        else:
                            ExportarDatos.generar_datos_sql(tipo_db, 'inclinometros', cursor, dir_actual, consulta, (id_inclinometro,))
            except Exception as e:
                raise
    
    def exportar_inclinometros_gkn(db_path):
        # Obtener los nombres de las tablas dinámicas
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("PRAGMA journal_mode = MEMORY")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT incli.id_inclinometro, 'inclinometro_detalle' || incli.id_proyecto AS detail_inclinometro
                FROM inclinometros incli WHERE incli.tipo_inclinometro = 'GEOKON'
            """)
            tablas_dinamicas = cursor.fetchall()

        for id_inclinometro, detail_inclinometro in tablas_dinamicas:
            # Verificar si la tabla de detalle existe
            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{detail_inclinometro}'")
                    if not cursor.fetchone():
                        continue
            except Exception as e:
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
            INNER JOIN inclinometro_encabezado inclien ON incli.id_inclinometro = inclien.id_inclinometro
            INNER JOIN {detail_inclinometro} inclideta ON inclien.id_encabezado = inclideta.id_encabezado
            WHERE incli.id_inclinometro = ?
            ORDER BY incli.nombre_inclinometro, inclien.fecha_inclinometro;
            """

            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    conn.execute("PRAGMA journal_mode = MEMORY")
                    cursor = conn.cursor()
                    # Crear directorios para inclinómetros
                    directorios = ExportarDatos.crear_directorios('inclinometros_gkn')
                    for tipo_db in DB_TYPES:
                        dir_actual = directorios[tipo_db]
                        if tipo_db != 'csv':
                            ExportarDatos.generar_esquema(tipo_db, 'inclinometros', cursor, dir_actual)
                        if tipo_db == 'csv':
                            ExportarDatos.generar_datos_csv('inclinometros', cursor, dir_actual, consulta, (id_inclinometro,))
                        else:
                            ExportarDatos.generar_datos_sql(tipo_db, 'inclinometros', cursor, dir_actual, consulta, (id_inclinometro,))
            except Exception as e:
                raise
    
    def exportar_celdas_asentamiento(db_path):
        # Obtener los nombres de las tablas dinámicas
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute("PRAGMA journal_mode = MEMORY")
            cursor = conn.cursor()
            cursor.execute("""SELECT id_celda, 'celda_detalle' || id_proyecto AS detalle FROM celdas""")
            tablas_dinamicas = cursor.fetchall()
        for id_celda, detalle in tablas_dinamicas:
            # Verificar si la tabla de detalle existe
            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{detalle}'")
                    if not cursor.fetchone():
                        continue
            except Exception as e:
                continue
            
            consulta = f"""SELECT c.nombre_celda,
                cd.fecha_detalle,
                cd.frecuencia_digits,
                cd.frecuencia_hz,
                cd.temperatura_detalle,
                cd.medida_calculada
            FROM celdas c
            INNER JOIN {detalle} cd ON c.id_celda = cd.id_celda
            WHERE c.id_celda = ?
            ORDER BY c.nombre_celda, cd.fecha_detalle;"""
            
            try:
                with closing(sqlite3.connect(db_path)) as conn:
                    conn.execute("PRAGMA journal_mode = MEMORY")
                    cursor = conn.cursor()
                    # Crear directorios para celdas
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
                raise

    def crear_directorios(tabla):
        # Usar resource_path para obtener la ruta base
        base_dir = resource_path(BASE_DIR)
        estructura = {
            'base': os.path.join(base_dir, tabla),
            'sqlite': os.path.join(base_dir, tabla, 'sqlite'),
            'sqlserver': os.path.join(base_dir, tabla, 'sqlserver'),
            'mysql': os.path.join(base_dir, tabla, 'mysql'),
            'csv': os.path.join(base_dir, tabla, 'csv')
        }
        for directorio in estructura.values():
            os.makedirs(directorio, exist_ok=True)
        return estructura
    
    def obtener_quoter(tipo_db):
        return {
            'sqlite': lambda x: f'"{x}"',
            'sqlserver': lambda x: f'[{x}]',
            'mysql': lambda x: f'`{x}`',
            'csv': lambda x: f'"{x}"'
        }[tipo_db]

    def formatear_valor(valor, tipo_col, tipo_db):
        # Formatea valores para SQL y CSV
        if valor is None:
            return 'NULL' if tipo_db != 'csv' else ''
        if isinstance(valor, bytes):
            return f"X'{valor.hex()}'" if tipo_db != 'csv' else valor.hex()
        if isinstance(valor, bool):
            return '1' if valor else '0' if tipo_db != 'csv' else ('TRUE' if valor else 'FALSE')
        if tipo_db == 'csv' and tipo_col in ['DATE', 'DATETIME']:
            return valor.replace("'", "").strip('#')
        if isinstance(valor, str):
            valor = valor.replace("'", "''")
            if tipo_db == 'mysql' and any(ord(c) > 154 for c in valor):
                return f"_utf8mb4 '{valor}'"
            return f"'{valor}'" if tipo_db != 'csv' else valor
        return str(valor)
    
    def generar_esquema(tipo_db, tabla, cursor, directorio):
        try:
            cursor.execute(f"PRAGMA table_info({tabla})")
        except sqlite3.OperationalError:
            return
        # Genera archivo DDL con la estructura de la tabla
        quoter = ExportarDatos.obtener_quoter(tipo_db)
        columnas = cursor.fetchall()
        nombre_archivo = f"{tabla}_{tipo_db}_schema.sql"
        ruta = resource_path(os.path.join(directorio, nombre_archivo))
        with open(ruta, 'w', encoding='utf-8') as f:
            if tipo_db in ['sqlserver', 'mysql']:
                f.write(f"DROP TABLE IF EXISTS {quoter(tabla)};\n")
            f.write(f"CREATE TABLE {quoter(tabla)} (\n")
            definiciones = []
            pk = []
            for col in columnas:
                nombre = quoter(col[1])
                tipo_sqlite = col[2].upper() if col[2] else 'TEXT'
                tipo_db_mapped = TYPE_MAP.get(tipo_sqlite, {}).get(tipo_db, 'TEXT')
                constraints = []
                if col[3]:  # NOT NULL
                    constraints.append('NOT NULL')
                if col[5]:  # PRIMARY KEY
                    pk.append(nombre)
                    if tipo_db == 'csv' or len(pk) > 1:
                        constraints = [c for c in constraints if c != 'PRIMARY KEY']
                definicion = f"    {nombre} {tipo_db_mapped}"
                if constraints:
                    definicion += f" {' '.join(constraints)}"
                definiciones.append(definicion.strip())
            if pk and (tipo_db == 'csv' or len(pk) > 1):
                definiciones.append(f'    PRIMARY KEY ({", ".join(pk)})')
            f.write(',\n'.join(definiciones))
            if tipo_db == 'mysql':
                f.write('\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n')
            else:
                f.write('\n);\n')
    
    def generar_datos_sql(tipo_db, tabla, cursor, directorio, consulta=None, parametros=None):
        # Genera archivos de datos en chunks para motores SQL
        quoter = ExportarDatos.obtener_quoter(tipo_db)
        if consulta:
            cursor.execute(consulta, parametros)
            nombres_col = [desc[0] for desc in cursor.description]
            tipos_col = [None] * len(nombres_col)
        else:
            cursor.execute(f"PRAGMA table_info({tabla})")
            columnas = cursor.fetchall()
            nombres_col = [col[1] for col in columnas]
            tipos_col = [col[2].upper() if col[2] else 'TEXT' for col in columnas]
        chunk_number = 1
        while True:
            nombre_archivo = f"{tabla}_{tipo_db}_data_chunk_{chunk_number}.sql"
            ruta = resource_path(os.path.join(directorio, nombre_archivo))
            primera_vez = not os.path.exists(ruta)

            with open(ruta, 'a+' if not primera_vez else 'w+', encoding='utf-8', buffering=BUFFER_SIZE) as archivo_actual:
                if primera_vez:
                    archivo_actual.write(f"INSERT INTO {quoter(tabla)} ({', '.join(quoter(n) for n in nombres_col)})\nVALUES\n")
                else:
                    # Leer el archivo completo en memoria
                    archivo_actual.seek(0)
                    contenido = archivo_actual.read()
                    if contenido.strip().endswith(';'):
                        contenido = contenido.rstrip(';\n') + ',\n'
                        archivo_actual.seek(0)
                        archivo_actual.truncate()
                        archivo_actual.write(contenido)
                primera_iteracion = True
                registros_procesados = 0
                while registros_procesados < CHUNK_SIZE:
                    registros = cursor.fetchmany(500)
                    if not registros:
                        break

                    valores = []
                    for registro in registros:
                        valores.append(
                            f"({', '.join(ExportarDatos.formatear_valor(registro[i], tipos_col[i], tipo_db) for i in range(len(nombres_col)))})"
                        )

                    if primera_iteracion:
                        archivo_actual.write(',\n'.join(valores))
                        primera_iteracion = False
                    else:
                        archivo_actual.write(',\n')
                        archivo_actual.write(',\n'.join(valores))

                    registros_procesados += len(registros)

                # Cerrar la instrucción INSERT al final del archivo
                archivo_actual.seek(0, os.SEEK_END)
                if archivo_actual.tell() > 0:
                    archivo_actual.seek(archivo_actual.tell() - 1)
                    if archivo_actual.read(1) == ',':
                        archivo_actual.seek(archivo_actual.tell() - 1)
                        archivo_actual.truncate()
                archivo_actual.write(';\n')
            if registros_procesados < CHUNK_SIZE:
                break
            chunk_number += 1
    
    def generar_datos_csv(tabla, cursor, directorio, consulta=None, parametros=None):
        # Genera archivos CSV en chunks para CSV
        if consulta:
            cursor.execute(consulta, parametros)
            nombres_col = [desc[0] for desc in cursor.description]
            tipos_col = [None] * len(nombres_col)
        else:
            cursor.execute(f"PRAGMA table_info({tabla})")
            column_info = cursor.fetchall()
            nombres_col = [col[1] for col in column_info]
            tipos_col = [col[2].upper() if col[2] else 'TEXT' for col in column_info]
        chunk_number = 1
        while True:
            nombre_archivo = f"{tabla}_csv_data_chunk_{chunk_number}.csv"
            ruta = resource_path(os.path.join(directorio, nombre_archivo))
            primera_vez = not os.path.exists(ruta)

            with open(ruta, 'a', encoding='utf-8-sig', newline='', buffering=BUFFER_SIZE) as archivo_actual:
                escritor = csv.writer(archivo_actual, delimiter=';', quoting=csv.QUOTE_ALL)

                if primera_vez:
                    escritor.writerow(nombres_col)

                registros_procesados = 0
                while registros_procesados < CHUNK_SIZE:
                    registros = cursor.fetchmany(500)
                    if not registros:
                        break

                    for registro in registros:
                        fila = []
                        for idx, valor in enumerate(registro):
                            tipo_col = tipos_col[idx]
                            if isinstance(valor, bytes):
                                fila.append(valor.hex())
                            elif isinstance(valor, bool):
                                fila.append('TRUE' if valor else 'FALSE')
                            elif isinstance(valor, str) and tipo_col in ['DATE', 'DATETIME']:
                                fila.append(valor.replace("'", "").strip('#'))
                            else:
                                fila.append(str(valor) if valor is not None else '')
                        escritor.writerow(fila)

                    registros_procesados += len(registros)

            if registros_procesados < CHUNK_SIZE:
                break

            chunk_number += 1
    
    def generar_datos_prismas_sql(tipo_db, tabla, cursor, directorio):
        # Genera archivos de datos en chunks para la tabla prismas en formato SQL
        quoter = ExportarDatos.obtener_quoter(tipo_db)

        cursor.execute(f"PRAGMA table_info({tabla})")
        columnas = cursor.fetchall()
        nombres_col = [col[1] for col in columnas]
        tipos_col = [col[2].upper() if col[2] else 'TEXT' for col in columnas]

        chunk_number = 1
        while True:
            nombre_archivo = f"{tabla}_{tipo_db}_data_chunk_{chunk_number}.sql"
            ruta = resource_path(os.path.join(directorio, nombre_archivo))
            primera_vez = not os.path.exists(ruta)

            cursor.execute(f"SELECT * FROM {tabla} LIMIT {CHUNK_SIZE} OFFSET {(chunk_number - 1) * CHUNK_SIZE}")
            registros = cursor.fetchall()

            if not registros:
                break

            with open(ruta, 'a+' if not primera_vez else 'w+', encoding='utf-8', buffering=BUFFER_SIZE) as archivo_actual:
                if primera_vez:
                    archivo_actual.write(f"INSERT INTO {quoter(tabla)} ({', '.join(quoter(n) for n in nombres_col)})\nVALUES\n")
                else:
                    # Leer el archivo completo en memoria
                    archivo_actual.seek(0)
                    contenido = archivo_actual.read()
                    if contenido.strip().endswith(';'):
                        contenido = contenido.rstrip(';\n') + ',\n'
                        archivo_actual.seek(0)
                        archivo_actual.truncate()
                        archivo_actual.write(contenido)
                primera_iteracion = True
                valores = []
                for registro in registros:
                    valores.append(
                        f"({', '.join(ExportarDatos.formatear_valor(registro[i], tipos_col[i], tipo_db) for i in range(len(nombres_col)))})"
                    )

                if primera_iteracion:
                    archivo_actual.write(',\n'.join(valores))
                    primera_iteracion = False
                else:
                    archivo_actual.write(',\n')
                    archivo_actual.write(',\n'.join(valores))

                # Cerrar la instrucción INSERT al final del archivo
                archivo_actual.seek(0, os.SEEK_END)
                if archivo_actual.tell() > 0:
                    archivo_actual.seek(archivo_actual.tell() - 1)
                    if archivo_actual.read(1) == ',':
                        archivo_actual.seek(archivo_actual.tell() - 1)
                        archivo_actual.truncate()
                archivo_actual.write(';\n')
            if len(registros) < CHUNK_SIZE:
                break
            chunk_number += 1
    
    def generar_datos_prismas_csv(tabla, cursor, directorio):
        """Genera archivos CSV en chunks para la tabla prismas"""
        cursor.execute(f"PRAGMA table_info({tabla})")
        column_info = cursor.fetchall()
        nombres_col = [col[1] for col in column_info]
        tipos_col = [col[2].upper() if col[2] else 'TEXT' for col in column_info]

        chunk_number = 1
        while True:
            nombre_archivo = f"{tabla}_csv_data_chunk_{chunk_number}.csv"
            ruta = resource_path(os.path.join(directorio, nombre_archivo))
            primera_vez = not os.path.exists(ruta)

            cursor.execute(f"SELECT * FROM {tabla} LIMIT {CHUNK_SIZE} OFFSET {(chunk_number - 1) * CHUNK_SIZE}")
            registros = cursor.fetchall()

            if not registros:
                break

            with open(ruta, 'a', encoding='utf-8-sig', newline='', buffering=BUFFER_SIZE) as archivo_actual:
                escritor = csv.writer(archivo_actual, delimiter=';', quoting=csv.QUOTE_ALL)

                if primera_vez:
                    escritor.writerow(nombres_col)

                for registro in registros:
                    fila = []
                    for idx, valor in enumerate(registro):
                        tipo_col = tipos_col[idx]
                        if isinstance(valor, bytes):
                            fila.append(valor.hex())
                        elif isinstance(valor, bool):
                            fila.append('TRUE' if valor else 'FALSE')
                        elif isinstance(valor, str) and tipo_col in ['DATE', 'DATETIME']:
                            fila.append(valor.replace("'", "").strip('#'))
                        else:
                            fila.append(str(valor) if valor is not None else '')
                    escritor.writerow(fila)
            if len(registros) < CHUNK_SIZE:
                break
            chunk_number += 1
    