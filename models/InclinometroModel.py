from services.security.apis.conexiones.conexion import Connection
from sqlite3 import Error
from datetime import datetime

class InclinometroModel:
     
    def mdlObtenerInclinometroTipo(idproyecto, idcomponente, idinstru):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql = """SELECT i.tipo_inclinometro FROM inclinometros i
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE c.id_proyecto = ? AND c.id_componente = ? AND t.id_instrumentacion = ?;"""
            cur.execute(sql, (idproyecto, idcomponente, idinstru))
            resultado = cur.fetchone()
            if resultado:
                return resultado
            else:
                return None 
        except Error as e:
            print("Error al obtener tipo inclino:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlListarInclinometrosProyecto(idproyecto, idcomponente, idinstrumento):
        sql = """SELECT i.id_inclinometro, e.id_encabezado, i.nombre_inclinometro, c.id_componente, i.este_inclinometro,
        i.norte_inclinometro, i.elevacion_inclinometro, e.fecha_inclinometro, i.tipo_inclinometro, i.inclinacion_inclinometro,
        i.azimut_inclinometro, i.profundidad_inclinometro, i.estado_inclinometro FROM inclinometros i
        INNER JOIN inclinometro_encabezado e ON i.id_inclinometro = e.id_inclinometro
		INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
		INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_instrumentacion = ? AND c.id_componente = ? AND e.estado_base = 1
		ORDER BY e.fecha_inclinometro;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idproyecto, idinstrumento, idcomponente))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar Inclinometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # RST
    def mdlObtenerDAAB_RST(tabla, idcomponente, idinstru, fechas, unidadmedida):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, ie.estado_base,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2, NULL) AS media_a,
                COALESCE((id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2, NULL) AS media_b
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'RST' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                COALESCE(media_a, NULL) AS media_a_base,
                COALESCE(media_b, NULL) AS media_b_base
            FROM detalle_calculado WHERE estado_base = 1
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            SUM(COALESCE(dc.media_a - COALESCE(bv.media_a_base, dc.media_a), NULL)) 
            OVER (PARTITION BY dc.nombre_inclinometro, dc.fecha_inclinometro 
            ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS Desplaz_Acumula_A,
            SUM(COALESCE(dc.media_b - COALESCE(bv.media_b_base, dc.media_b), NULL)) 
            OVER (PARTITION BY dc.nombre_inclinometro, dc.fecha_inclinometro 
            ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS Desplaz_Acumula_B
            FROM detalle_calculado dc
            LEFT JOIN base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro 
                AND dc.profundidad_detalle = bv.profundidad_detalle
            WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
            ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar rst AB acum: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    def mdlObtenerDIAB_RST(tabla, idcomponente, idinstru, fechas, unidadmedida):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, ie.estado_base,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2, NULL) AS media_a,
                COALESCE((id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2, NULL) AS media_b
            FROM inclinometros i
            INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'RST' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                COALESCE(media_a, NULL) AS media_a_base,
                COALESCE(media_b, NULL) AS media_b_base
            FROM detalle_calculado
            WHERE estado_base = 1
        )
        SELECT 
            dc.nombre_inclinometro,
            dc.fecha_inclinometro,
            dc.profundidad_detalle,
            COALESCE(dc.media_a - COALESCE(bv.media_a_base, dc.media_a), NULL) * {unidadmedida} AS Desplaz_Inc_A,
            COALESCE(dc.media_b - COALESCE(bv.media_b_base, dc.media_b), NULL) * {unidadmedida} AS Desplaz_Inc_B
        FROM detalle_calculado dc
        LEFT JOIN base_values bv 
            ON dc.nombre_inclinometro = bv.nombre_inclinometro 
            AND dc.profundidad_detalle = bv.profundidad_detalle
        WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar diab: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlObtenerDINE_RST(tabla, idcomponente, idinstru, fechas, unidadmedida, alfa):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, ie.estado_base,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 * COS({alfa} * PI() / 180) 
                - (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 * SIN({alfa} * PI() / 180), NULL) AS media_x,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 * SIN({alfa} * PI() / 180) 
                + (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 * COS({alfa} * PI() / 180), NULL) AS media_y
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'RST' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                COALESCE(media_x, NULL) AS media_x_base,
                COALESCE(media_y, NULL) AS media_y_base
            FROM detalle_calculado
            WHERE estado_base = 1
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            COALESCE(dc.media_x - COALESCE(bv.media_x_base, dc.media_x), NULL) * {unidadmedida} AS Desplaz_Inc_X,
            COALESCE(dc.media_y - COALESCE(bv.media_y_base, dc.media_y), NULL) + {unidadmedida} AS Desplaz_Inc_Y
        FROM detalle_calculado dc
        LEFT JOIN base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro 
            AND dc.profundidad_detalle = bv.profundidad_detalle
        WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlObtenerDANE_RST(tabla, idcomponente, idinstru, fechas, unidadmedida, alfa):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, ie.estado_base,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 * COS({alfa} * PI() / 180) 
                - (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 * SIN({alfa} * PI() / 180), NULL) AS media_x,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 * SIN({alfa} * PI() / 180) 
                + (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 * COS({alfa} * PI() / 180), NULL) AS media_y
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'RST' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                COALESCE(media_x, NULL) AS media_x_base,
                COALESCE(media_y, NULL) AS media_y_base
            FROM detalle_calculado
            WHERE estado_base = 1
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            SUM(COALESCE(dc.media_x - COALESCE(bv.media_x_base, dc.media_x), NULL)) 
                OVER (PARTITION BY dc.nombre_inclinometro, dc.fecha_inclinometro 
                    ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS Desplaz_Acumula_X,
            SUM(COALESCE(dc.media_y - COALESCE(bv.media_y_base, dc.media_y), NULL)) 
                OVER (PARTITION BY dc.nombre_inclinometro, dc.fecha_inclinometro 
                    ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS Desplaz_Acumula_Y
        FROM detalle_calculado dc
        LEFT JOIN base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro 
            AND dc.profundidad_detalle = bv.profundidad_detalle
        WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar DANE: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerDANEvisor_RST(idproyecto, idinclino, fechas, este, norte, nivel, escala):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idinclino] + fechas
        conn = Connection.connectionDB()
        sql = f"""WITH detalle_calculado AS (
                    SELECT
                        i.nombre_inclinometro,
                        ie.fecha_inclinometro,
                        id.profundidad_detalle,
                        ie.estado_base,
                        COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 * COS(450 * PI() / 180) 
                        - (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 * SIN(450 * PI() / 180), NULL) AS media_x,
                        COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 * SIN(450 * PI() / 180) 
                        + (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 * COS(450 * PI() / 180), NULL) AS media_y
                    FROM 
                        inclinometros i
                    INNER JOIN 
                        inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
                    INNER JOIN 
                        inclinometro_detalle{idproyecto} id ON ie.id_encabezado = id.id_encabezado
                    WHERE i.id_inclinometro = ? AND i.tipo_inclinometro = 'RST' AND ie.fecha_inclinometro IN ({placeholders})
                ),
                base_values AS (
                    SELECT
                        nombre_inclinometro,
                        profundidad_detalle, fecha_inclinometro AS fecha_base,
                        COALESCE(media_x, NULL) AS media_x_base,
                        COALESCE(media_y, NULL) AS media_y_base
                    FROM 
                        detalle_calculado
                    WHERE 
                        estado_base = 1
                )
                SELECT
                    dc.nombre_inclinometro,
                    dc.fecha_inclinometro,
                    {nivel}-abs(dc.profundidad_detalle) AS profundidad_detalle,
                    SUM(COALESCE(dc.media_x - COALESCE(bv.media_x_base, dc.media_x), NULL)) 
                        OVER (PARTITION BY dc.nombre_inclinometro, dc.fecha_inclinometro 
                            ORDER BY dc.profundidad_detalle ASC) * {escala} + {este} AS Desplaz_Acumula_X,
                    SUM(COALESCE(dc.media_y - COALESCE(bv.media_y_base, dc.media_y), NULL)) 
                        OVER (PARTITION BY dc.nombre_inclinometro, dc.fecha_inclinometro 
                            ORDER BY dc.profundidad_detalle ASC) * {escala} + {norte} AS Desplaz_Acumula_Y
                FROM 
                    detalle_calculado dc
                LEFT JOIN 
                    base_values bv 
                    ON dc.nombre_inclinometro = bv.nombre_inclinometro 
                    AND dc.profundidad_detalle = bv.profundidad_detalle
                WHERE 
                    dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
                ORDER BY 
                    dc.fecha_inclinometro ASC,  
                    dc.profundidad_detalle DESC;
                """
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerPAAB_RST(tabla, idcomponente, idinstru, fechas, unidadmedida):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, ie.estado_base,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2, NULL) AS media_a,
                COALESCE((id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2, NULL) AS media_b
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'RST' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            SUM(dc.media_a) OVER (PARTITION BY dc.fecha_inclinometro 
            ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS posicion_absoluta_a,
            SUM(dc.media_b) OVER (PARTITION BY dc.fecha_inclinometro 
            ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS posicion_absoluta_b
        FROM detalle_calculado dc
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar PAAB: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlObtenerPANE_RST(tabla, idcomponente, idinstru, fechas, unidadmedida, alfa):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, ie.estado_base,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 * COS({alfa} * PI() / 180) 
                - (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 * SIN({alfa} * PI() / 180), NULL) AS media_x,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 * SIN({alfa} * PI() / 180) 
                + (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 * COS({alfa} * PI() / 180), NULL) AS media_y
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'RST' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            SUM(dc.media_x) OVER (PARTITION BY dc.fecha_inclinometro 
            ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS posicion_absoluta_x,
            SUM(dc.media_y) OVER (PARTITION BY dc.fecha_inclinometro 
            ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS posicion_absoluta_y
        FROM detalle_calculado dc
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle DESC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar PANE: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    def mdlObtenerCSAB_RST(tabla, idcomponente, idinstru, fechas, unidadmedida):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas

        sql = f"""
        SELECT
            i.nombre_inclinometro,
            ie.fecha_inclinometro,
            id.profundidad_detalle,
            (id.apositivo_detalle + id.anegativo_detalle) * {unidadmedida} AS checksum_a,
            (id.bpositivo_detalle + id.bnegativo_detalle) * {unidadmedida} AS checksum_b
        FROM inclinometros i
        INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
        INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
        INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
        INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE i.tipo_inclinometro = 'RST'
        AND c.id_componente = ?
        AND t.id_instrumentacion = ?
        AND ie.fecha_inclinometro IN ({placeholders})
        ORDER BY ie.fecha_inclinometro ASC, id.profundidad_detalle DESC;
        """

        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar PANE: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    # GKN
    def mdlObtenerDAAB_GKN(tabla, idcomponente, idinstru, fechas, unidadmedida, zz=0, mrint=0.025):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, id.apositivo_detalle, id.anegativo_detalle,
                id.bpositivo_detalle, id.bnegativo_detalle, ie.estado_base,
                (id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 AS SA,
                (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 AS SB
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'GEOKON' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                (apositivo_detalle - anegativo_detalle) * 1.0 / 2 AS SA_base,
                (bpositivo_detalle - bnegativo_detalle) * 1.0 / 2 AS SB_base
            FROM detalle_calculado
            WHERE estado_base = 1
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            SUM(
                (({mrint} * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * COS(({zz} * PI()) / 180) 
                - ({mrint} * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * SIN(({zz} * PI()) / 180))) * {unidadmedida})
            ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) AS DicA,
            SUM(
                (({mrint} * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * SIN(({zz} * PI()) / 180) 
                + ({mrint} * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * COS(({zz} * PI()) / 180))) * {unidadmedida})
            ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) AS DicB
        FROM detalle_calculado dc
        LEFT JOIN 
            base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro 
            AND dc.profundidad_detalle = bv.profundidad_detalle
        WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlObtenerDIAB_GKN(tabla, idcomponente, idinstru, fechas, unidadmedida, zz, mrint):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, id.apositivo_detalle, id.anegativo_detalle,
                id.bpositivo_detalle, id.bnegativo_detalle, ie.estado_base,
                (id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 AS SA,
                (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 AS SB
            FROM inclinometros i
            INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'GEOKON' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                (apositivo_detalle - anegativo_detalle) * 1.0 / 2 AS SA_base,
                (bpositivo_detalle - bnegativo_detalle) * 1.0 / 2 AS SB_base
            FROM detalle_calculado
            WHERE estado_base = 1
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            (({mrint} * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2
            - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * COS(({zz} * PI()) / 180)
            - ({mrint} * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2
            - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * SIN(({zz} * PI()) / 180))) * {unidadmedida})
            AS DicA_Inc,
            (({mrint} * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2
            - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * SIN(({zz} * PI()) / 180)
            + ({mrint} * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2
            - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * COS(({zz} * PI()) / 180))) * {unidadmedida})
            AS DicB_Inc
        FROM detalle_calculado dc
        LEFT JOIN
            base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro
            AND dc.profundidad_detalle = bv.profundidad_detalle
        WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlObtenerDINE_GKN(tabla, idcomponente, idinstru, fechas, unidadmedida, alfa, mrint):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, id.apositivo_detalle,
                id.anegativo_detalle, id.bpositivo_detalle, id.bnegativo_detalle, ie.estado_base,
                (id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 AS SA,
                (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 AS SB
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'GEOKON' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                (apositivo_detalle - anegativo_detalle) * 1.0 / 2 AS SA_base,
                (bpositivo_detalle - bnegativo_detalle) * 1.0 / 2 AS SB_base
            FROM detalle_calculado
            WHERE estado_base = 1
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            (({mrint} * (dc.SA - COALESCE(bv.SA_base, dc.SA)) * COS({alfa} * PI() / 180) 
            - {mrint} * (dc.SB - COALESCE(bv.SB_base, dc.SB)) * SIN({alfa} * PI() / 180)) * {unidadmedida}) AS DIX,
            (({mrint} * (dc.SA - COALESCE(bv.SA_base, dc.SA)) * SIN({alfa} * PI() / 180) 
            + {mrint} * (dc.SB - COALESCE(bv.SB_base, dc.SB)) * COS({alfa} * PI() / 180)) * {unidadmedida}) AS DIY
        FROM detalle_calculado dc
        LEFT JOIN base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro 
            AND dc.profundidad_detalle = bv.profundidad_detalle
        WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar DINE: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerDANE_GKN(tabla, idcomponente, idinstru, fechas, unidadmedida, alfa, mrint, zz):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, id.apositivo_detalle, id.anegativo_detalle,
                id.bpositivo_detalle, id.bnegativo_detalle, ie.estado_base,
                (id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 AS SA,
                (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 AS SB
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'GEOKON' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                (apositivo_detalle - anegativo_detalle) * 1.0 / 2 AS SA_base,
                (bpositivo_detalle - bnegativo_detalle) * 1.0 / 2 AS SB_base
            FROM detalle_calculado
            WHERE estado_base = 1
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            SUM(
                (({mrint} * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * COS(({zz} * PI()) / 180)) 
                - ({mrint} * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * SIN(({zz} * PI()) / 180))) * {unidadmedida}
            ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * COS({alfa} * PI() / 180)
            - SUM(
                (({mrint} * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * SIN(({zz} * PI()) / 180)) 
                + ({mrint} * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2
                - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * COS(({zz} * PI()) / 180))) * {unidadmedida}
            ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * SIN({alfa} * PI() / 180) AS DacX,
            SUM(
                (({mrint} * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * COS(({zz} * PI()) / 180)) 
                - ({mrint} * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * SIN(({zz} * PI()) / 180))) * {unidadmedida}
            ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * SIN({alfa} * PI() / 180)
            + SUM(
                (({mrint} * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * SIN(({zz} * PI()) / 180)) 
                + ({mrint} * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2 
                - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * COS(({zz} * PI()) / 180))) * {unidadmedida}
            ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * COS({alfa} * PI() / 180) AS DacY
        FROM detalle_calculado dc
        LEFT JOIN base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro 
            AND dc.profundidad_detalle = bv.profundidad_detalle
        WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerDANEvisor_GKN(idproyecto, idinclino, fechas, este, norte, nivel, escala):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idinclino] + fechas
        conn = Connection.connectionDB()
        sql = f"""WITH detalle_calculado AS (
                    SELECT
                        i.nombre_inclinometro,
                        ie.fecha_inclinometro,
                        id.profundidad_detalle,
                        id.apositivo_detalle,
                        id.anegativo_detalle,
                        id.bpositivo_detalle,
                        id.bnegativo_detalle,
                        ie.estado_base,
                        (id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2 AS SA,
                        (id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2 AS SB
                    FROM 
                        inclinometros i
                    INNER JOIN 
                        inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
                    INNER JOIN 
                        inclinometro_detalle{idproyecto} id ON ie.id_encabezado = id.id_encabezado
                    WHERE i.id_inclinometro = ? AND i.tipo_inclinometro = 'GEOKON' AND ie.fecha_inclinometro IN ({placeholders})
                ),
                base_values AS (
                    SELECT
                        nombre_inclinometro,
                        profundidad_detalle, fecha_inclinometro AS fecha_base,
                        (apositivo_detalle - anegativo_detalle) * 1.0 / 2 AS SA_base,
                        (bpositivo_detalle - bnegativo_detalle) * 1.0 / 2 AS SB_base
                    FROM 
                        detalle_calculado
                    WHERE 
                        estado_base = 1
                )
                SELECT
                    dc.nombre_inclinometro,
                    dc.fecha_inclinometro,
                    {nivel}-abs(dc.profundidad_detalle) AS profundidad_detalle,
                    (
                        SUM(
                            ((0.05 * 0.5 * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                            - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * COS((0.0 * PI()) / 180)) 
                            - (0.05 * 0.5 * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2 
                            - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * SIN((0.0 * PI()) / 180))) / 1
                        ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * COS((450 - 0) * PI() / 180)
                        - SUM(
                            ((0.05 * 0.5 * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                            - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * SIN((0.0 * PI()) / 180)) 
                            + (0.05 * 0.5 * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2 
                            - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * COS((0.0 * PI()) / 180))) / 1
                        ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * SIN((450 - 0) * PI() / 180)
                    ) * {escala} / 1000 + {este} AS DacX,
                    (
                        SUM(
                            ((0.05 * 0.5 * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                            - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * COS((0.0 * PI()) / 180)) 
                            - (0.05 * 0.5 * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2 
                            - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * SIN((0.0 * PI()) / 180))) / 1
                        ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * SIN((450 - 0) * PI() / 180)
                        + SUM(
                            ((0.05 * 0.5 * ((dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2 
                            - COALESCE(bv.SA_base, (dc.apositivo_detalle - dc.anegativo_detalle) * 1.0 / 2)) * SIN((0.0 * PI()) / 180)) 
                            + (0.05 * 0.5 * ((dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2 
                            - COALESCE(bv.SB_base, (dc.bpositivo_detalle - dc.bnegativo_detalle) * 1.0 / 2)) * COS((0.0 * PI()) / 180))) / 1
                        ) OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * COS((450 - 0) * PI() / 180)
                    ) * {escala} / 1000 + {norte} AS DacY

                FROM 
                    detalle_calculado dc
                LEFT JOIN 
                    base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro 
                    AND dc.profundidad_detalle = bv.profundidad_detalle
                WHERE 
                    dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
                ORDER BY 
                    dc.fecha_inclinometro ASC,  
                    dc.profundidad_detalle ASC;
                """
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerPAAB_GKN(tabla, idcomponente, idinstru, fechas, unidadmedida, mrint):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, id.apositivo_detalle,
                id.anegativo_detalle, id.bpositivo_detalle, id.bnegativo_detalle, ie.estado_base,
                {mrint} * ((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2) AS CA_dig,
                {mrint} * ((id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2) AS CB_dig
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'GEOKON' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            SUM(dc.CA_dig * 1.0 * {unidadmedida}) 
                OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) AS posicion_absoluta_a,
            SUM(dc.CB_dig * 1.0 * {unidadmedida}) 
                OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) AS posicion_absoluta_b
        FROM detalle_calculado dc
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar PAAB: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlObtenerPANE_GKN(tabla, idcomponente, idinstru, fechas, unidadmedida, alfa, mrint):
        placeholders = ', '.join(['?' for _ in fechas])
        params = [idcomponente] + [idinstru] + fechas
        sql = f"""WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, id.apositivo_detalle,
                id.anegativo_detalle, id.bpositivo_detalle, id.bnegativo_detalle, ie.estado_base,
                {mrint} * ((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2) AS CA_dig,
                {mrint} * ((id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2) AS CB_dig
            FROM inclinometros i INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'GEOKON' AND c.id_componente = ? AND t.id_instrumentacion = ?
            AND ie.fecha_inclinometro IN ({placeholders})
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            (SUM(dc.CA_dig * 1.0 * {unidadmedida}) 
                OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * COS({alfa} * PI() / 180) 
            - SUM(dc.CB_dig * 1.0 * {unidadmedida}) 
                OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * SIN({alfa} * PI() / 180)) AS posicion_absoluta_x,
            (SUM(dc.CA_dig * 1.0 * {unidadmedida}) 
                OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * SIN({alfa} * PI() / 180) 
            + SUM(dc.CB_dig * 1.0 * {unidadmedida}) 
                OVER (PARTITION BY dc.fecha_inclinometro ORDER BY dc.profundidad_detalle DESC) * COS({alfa} * PI() / 180)) AS posicion_absoluta_y
        FROM detalle_calculado dc
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle ASC;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows= cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar : " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # LISTAR LOS NOMBRES DE LOS INCLINOMETROS POR PROYECTO    
    def mdlListarInclinometrosNombreProyecto(proyecto):
        sql = """SELECT * FROM inclinometros WHERE id_proyecto = ?"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto,))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar inclinometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    def mdlRegistrarDataInclinometro(proyectoid, id_inclinometro, fecha_hora, data):
        conn = Connection.connectionDB()
        try:
            cur = conn.cursor()

            # Verificar si ya existe un encabezado con la misma fecha y el mismo id_inclinometro
            sql_verificar = """
            SELECT 1 FROM inclinometro_encabezado
            WHERE id_inclinometro = ? AND fecha_inclinometro = ?
            """
            cur.execute(sql_verificar, (id_inclinometro, fecha_hora))
            if cur.fetchone():
                return "duplicado"

            # Iniciar una transacción
            conn.execute("BEGIN")

            # Insertar en la tabla inclinometro_encabezado
            sql_encabezado = """
            INSERT INTO inclinometro_encabezado (id_inclinometro, fecha_inclinometro)
            VALUES (?, ?)
            """
            cur.execute(sql_encabezado, (id_inclinometro, fecha_hora))
            id_encabezado = cur.lastrowid

            # Crear la tabla inclinometro_detalle si no existe
            tabla = f"inclinometro_detalle{proyectoid}"
            sqltable = f"""
            CREATE TABLE IF NOT EXISTS {tabla} (
                "id_detalle"	INTEGER NOT NULL UNIQUE,
                "id_encabezado"	INTEGER NOT NULL,
                "profundidad_detalle"	NUMERIC NOT NULL,
                "apositivo_detalle"	NUMERIC NOT NULL,
                "anegativo_detalle"	NUMERIC NOT NULL,
                "bpositivo_detalle"	NUMERIC NOT NULL,
                "bnegativo_detalle"	NUMERIC NOT NULL,
                PRIMARY KEY("id_detalle" AUTOINCREMENT)
            )
            """
            cur.execute(sqltable)

            # Insertar los datos en la tabla inclinometro_detalle
            sql_detalle = f"""
            INSERT INTO {tabla} (id_encabezado, profundidad_detalle, apositivo_detalle, anegativo_detalle, bpositivo_detalle, bnegativo_detalle)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            for row in data:
                cur.execute(sql_detalle, (id_encabezado, row[0], row[1], row[2], row[3], row[4]))

            # Confirmar la transacción
            conn.commit()
            return "ok"
        except Error as e:
            print("Error al registrar inclinometros: " + str(e))
            # Realizar rollback en caso de error
            conn.rollback()
            return "error"
        finally:
            if conn:
                conn.close()
    
    # ACTUALIZAR LECTURA INCLINOMETRO DESDE TABLA      
    def mdlActualizarLecturaInclinometro(tabla, datos, idproyecto, username, nombres):
        sql = f"""UPDATE {tabla} SET apositivo_detalle = ?, anegativo_detalle = ?, bpositivo_detalle = ?, 
        bnegativo_detalle = ? WHERE id_detalle = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            query_select = f"""SELECT apositivo_detalle, anegativo_detalle, bpositivo_detalle,
            bnegativo_detalle, id_detalle FROM {tabla} WHERE id_detalle = ?;"""
            cur.execute(query_select, (datos[-1],))
            datos_anteriores = cur.fetchone()
            if datos_anteriores:
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "update"
                cambios = f"Antiguos: {datos_anteriores}, Nuevos: {datos}"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # actualizar inclinometro
            cur.execute(sql, datos)
            conn.commit()
            return True
        except Error as e:
            print("Error al editar lectura inclinometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarInclinometros(idcomponente):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'INCLINOMETRO';"""
            cursor.execute(query_select, (idcomponente,))
            dataincli = cursor.fetchall()
            if dataincli:
                query = """DELETE FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'INCLINOMETRO';"""
                cursor.execute(query, (idcomponente,))
                conn.commit()
                if cursor.rowcount > 0:
                    return dataincli
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar inclinometros: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarDataInclinometros(tabla, inclinometros):
        placeholders = ','.join(['?' for _ in inclinometros])
        try:
            with Connection.connectionDB() as conn:
                cursor = conn.cursor()
                query_select = f"""SELECT id_encabezado FROM inclinometro_encabezado WHERE id_inclinometro IN ({placeholders});"""
                cursor.execute(query_select, tuple(inclinometros))
                encabezados = [row[0] for row in cursor.fetchall()]
                if not encabezados:
                    return False
                with conn:
                    placeholders_encabezados = ','.join(['?' for _ in encabezados])
                    query_delete_data = f"""DELETE FROM {tabla} WHERE id_encabezado IN ({placeholders_encabezados});"""
                    cursor.execute(query_delete_data, tuple(encabezados))
                    # Eliminar encabezados
                    query_delete_headers = f"""DELETE FROM inclinometro_encabezado WHERE id_inclinometro IN ({placeholders});"""
                    cursor.execute(query_delete_headers, tuple(inclinometros))
                    # Eliminar inclinómetros
                    query_delete_inclinometros = f"""DELETE FROM inclinometros WHERE id_inclinometro IN ({placeholders});"""
                    cursor.execute(query_delete_inclinometros, tuple(inclinometros))
                return True
        except Exception as e:
            print(f"Error al eliminar data de inclinometros: {str(e)}")
            return False
    
    def mdlObtenerInfoInclinometro(idinstrumento):
        sql = """SELECT i.* FROM inclinometros i INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo WHERE t.id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinstrumento,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar inclinometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    # def mdlActualizarInclinometro(idproyecto, datos):
    #     try:
    #         conn = Connection.connectionDB()
    #         cur = conn.cursor()
    #         # Insertar en la tabla inclinometros
    #         query_inclinometro = """
    #         UPDATE inclinometros SET tipo_inclinometro = ?, nombre_inclinometro = ?, codigo_inclinometro = ?,
    #         norte_inclinometro = ?, este_inclinometro = ?, elevacion_inclinometro = ?, profundidad_inclinometro = ?,
    #         inclinacion_inclinometro = ?, azimut_inclinometro = ?, comentario_inclinometro = ? WHERE id_inclinometro = ?;
    #         """
    #         cur.execute(query_inclinometro, (
    #             datos['tipoEquipo'], datos['nombre'], datos['codigo'],
    #             datos['norte'], datos['este'], datos['nivel'],
    #             datos['profundidad'], datos['inclinacion'], datos['azimut'],
    #             datos['comentario'], datos['codeincli']
    #         ))
    #         # Actualizar en la tabla instrumentacion
    #         query_instrumentacion = """
    #         UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
    #         WHERE id_instrumentacion = ? AND tipo_equipo = 'INCLINOMETRO';
    #         """
    #         cur.execute(query_instrumentacion, (
    #             datos['componente'], datos['nombre'], datos['instrumento']
    #         ))
    #         # Confirmar la transacción
    #         conn.commit()
    #         return True
    #     except Error as e:
    #         print("Error:", e)
    #         if conn:
    #             conn.rollback()
    #         return False
    #     finally:
    #         if conn:
    #             conn.close()

    def mdlActualizarInclinometro(idproyecto, datos):
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()

            # Verificar si el nombre ya existe en la tabla inclinometros para otro id_inclinometro
            query_verificar = """
            SELECT COUNT(*)
            FROM inclinometros
            WHERE nombre_inclinometro = ? AND id_inclinometro != ?
            """
            cur.execute(query_verificar, (datos['nombre'], datos['codeincli']))
            count = cur.fetchone()[0]

            if count > 0:
                print("El nombre del inclinómetro ya existe para otro registro.")
                return False

            # Actualizar en la tabla inclinometros
            query_inclinometro = """
            UPDATE inclinometros SET tipo_inclinometro = ?, nombre_inclinometro = ?, codigo_inclinometro = ?,
            norte_inclinometro = ?, este_inclinometro = ?, elevacion_inclinometro = ?, profundidad_inclinometro = ?,
            inclinacion_inclinometro = ?, azimut_inclinometro = ?, comentario_inclinometro = ?
            WHERE id_inclinometro = ?;
            """
            cur.execute(query_inclinometro, (
                datos['tipoEquipo'], datos['nombre'], datos['codigo'],
                datos['norte'], datos['este'], datos['nivel'],
                datos['profundidad'], datos['inclinacion'], datos['azimut'],
                datos['comentario'], datos['codeincli']
            ))

            # Actualizar en la tabla instrumentacion
            query_instrumentacion = """
            UPDATE instrumentacion SET id_componente = ?, nombre_equipo = ?
            WHERE id_instrumentacion = ? AND tipo_equipo = 'INCLINOMETRO';
            """
            cur.execute(query_instrumentacion, (
                datos['componente'], datos['nombre'], datos['instrumento']
            ))

            # Confirmar la transacción
            conn.commit()
            return True
        except Error as e:
            print("Error:", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    
    def mdlCambiarComponenteInclinometros(idcomponente, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_componente = ? AND tipo_equipo = 'INCLINOMETRO';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # guardar en historial
            cur.execute(sql, (nuevocomponente, idcomponente))
            if cur.rowcount > 0:
                conn.commit()
                query_select = """SELECT * FROM instrumentacion WHERE id_componente = ? AND tipo_equipo = 'INCLINOMETRO';"""
                cur.execute(query_select, (nuevocomponente,))
                dataincli = cur.fetchall()
                if dataincli:
                    return dataincli
                else:
                    return None
            else:
                return None
        except Error as e:
            print("Error al cambiar componente inclinometros: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarInclinometroComponente(idinstrumento, nuevocomponente):
        sql = """UPDATE instrumentacion SET id_componente = ? WHERE id_instrumentacion = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (nuevocomponente, idinstrumento))
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar componente inclinometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarInclinometroUnico(idinstrumento):
        try:
            conn = Connection.connectionDB()
            cursor = conn.cursor()
            # guardar en historial
            query_select = """SELECT * FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'INCLINOMETRO';"""
            cursor.execute(query_select, (idinstrumento,))
            dataincli = cursor.fetchone()
            if dataincli:
                query = """DELETE FROM instrumentacion WHERE id_instrumentacion = ? AND tipo_equipo = 'INCLINOMETRO';"""
                cursor.execute(query, (idinstrumento,))
                conn.commit()
                if cursor.rowcount > 0:
                    return dataincli
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(f"Error al eliminar inclinometro: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarInclinometroData(tabla, idinstrumento):
        try:
            with Connection.connectionDB() as conn:
                cursor = conn.cursor()
                query_select = f"""SELECT id_encabezado FROM inclinometro_encabezado WHERE id_inclinometro = ?;"""
                cursor.execute(query_select, (idinstrumento,))
                encabezados = [row[0] for row in cursor.fetchall()]
                if not encabezados:
                    return False
                with conn:
                    placeholders_encabezados = ','.join(['?' for _ in encabezados])
                    query_delete_data = f"""DELETE FROM {tabla} WHERE id_encabezado IN ({placeholders_encabezados});"""
                    cursor.execute(query_delete_data, tuple(encabezados))
                    # Eliminar encabezados
                    query_delete_headers = f"""DELETE FROM inclinometro_encabezado WHERE id_inclinometro = ?;"""
                    cursor.execute(query_delete_headers, (idinstrumento,))
                    # Eliminar inclinómetros
                    query_delete_inclinometros = f"""DELETE FROM inclinometros WHERE id_inclinometro = ?;"""
                    cursor.execute(query_delete_inclinometros, (idinstrumento,))
                return True
        except Exception as e:
            print(f"Error al eliminar data de inclinometro: {str(e)}")
            return False
    
    def mdlListarFechasInclinometro(idcomponente, idinstrumento, proyectoid):
        conn = Connection.connectionDB()
        sql = """SELECT e.fecha_inclinometro, i.tipo_inclinometro, e.estado_base, e.id_encabezado, e.id_inclinometro
        FROM inclinometro_encabezado e
        INNER JOIN inclinometros i ON i.id_inclinometro = e.id_inclinometro
		INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
		INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_instrumentacion = ? AND c.id_componente = ?
		ORDER BY e.fecha_inclinometro;"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (proyectoid, idinstrumento, idcomponente))
            row = cur.fetchall()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al consultar fechas inclinometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarBaseInclinometro(idencabezado, idinclinome):
        sql = """UPDATE inclinometro_encabezado SET estado_base = 1 WHERE id_encabezado = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # actualizar todos
            query_select = """UPDATE inclinometro_encabezado SET estado_base = 0 WHERE id_inclinometro = ?;"""
            cur.execute(query_select, (idinclinome,))
            cur.execute(sql, (idencabezado,))
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar estado base inclinometro: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlCambiarEstadoFechasInclinometro(iddesmarcadas, idinclinometro):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # actualizar todos
            query_select = """UPDATE inclinometro_encabezado SET estado_base = 0 WHERE id_inclinometro = ? AND estado_base != 1;"""
            cur.execute(query_select, (idinclinometro,))
            if iddesmarcadas: 
                placeholders = ', '.join(['?' for _ in iddesmarcadas])
                sql = f"""UPDATE inclinometro_encabezado SET estado_base = 2 WHERE id_encabezado IN ({placeholders}) AND estado_base != 1;"""
                cur.execute(sql, iddesmarcadas)
            conn.commit()
            return True
        except Error as e:
            print("Error al cambiar estado inclinometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlEliminarLecturaInclinometro(tabla, idproyecto, idencabezado, idinclinome, username, nombres):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Primero ejecutamos la eliminación y capturamos las filas afectadas
            sql = f"""DELETE FROM {tabla} WHERE id_encabezado = ?;"""
            cur.execute(sql, (idencabezado,))
            rows = cur.rowcount
            if rows > 0:
                query_delete = """DELETE FROM inclinometro_encabezado WHERE id_encabezado = ? AND id_inclinometro = ?;"""
                cur.execute(query_delete, (idencabezado, idinclinome))
                # ingresar al historial
                fecha_cambio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                accion = "delete"
                cambios = f"idencabezado: {idencabezado}, [tabla: inclinometro_encabezado, tabla: {tabla}]"
                query_historial = """INSERT INTO historial (idproyecto, fecha, accion, tabla, cambios, usuario, nombres)
                VALUES (?, ?, ?, ?, ?, ?, ?);"""
                cur.execute(query_historial, (idproyecto, fecha_cambio, accion, tabla, cambios, username, nombres))
            # commit
            conn.commit()
            return True
        except Error as e:
            print("Error al eliminar lectura inclinometro: " + str(e))
            return False
        finally:
            if conn:
                conn.close()
    
    def mdlObtenerIdIinclinometro(id_intrumentacion):
        conn = Connection.connectionDB()
        sql = """SELECT id_equipo FROM instrumentacion WHERE id_instrumentacion=?"""
        try:
            cur = conn.cursor()
            cur.execute(sql, (id_intrumentacion,))
            row = cur.fetchone()  # Usamos fetchone() para obtener una sola fila
            if row:
                return row[0]  # Devolvemos solo el valor de id_equipo
            else:
                return None
        except Error as e:
            print("Error al consultar id: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    #-----
    def mdlObtenerDAA_RST(tabla, id_inclinometro, unidadmedida):
        sql = f"""
        WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, ie.estado_base,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2, NULL) AS media_a,
                COALESCE((id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2, NULL) AS media_b
            FROM inclinometros i
            INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'RST' AND i.id_inclinometro = ? AND ie.estado_base != 2
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                COALESCE(media_a, NULL) AS media_a_base,
                COALESCE(media_b, NULL) AS media_b_base
            FROM detalle_calculado WHERE estado_base = 1
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            SUM(COALESCE(dc.media_a - COALESCE(bv.media_a_base, dc.media_a), NULL))
            OVER (PARTITION BY dc.nombre_inclinometro, dc.fecha_inclinometro
            ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS Desplaz_Acumula_A
        FROM detalle_calculado dc
        LEFT JOIN base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro
            AND dc.profundidad_detalle = bv.profundidad_detalle
        WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle DESC;
        """
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (id_inclinometro,))
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar rst A acum: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

    def mdlObtenerDAA_GKN(tabla, id_inclinometro, unidadmedida):
        sql = f"""
        WITH detalle_calculado AS (
            SELECT i.nombre_inclinometro, ie.fecha_inclinometro, id.profundidad_detalle, ie.estado_base,
                COALESCE((id.apositivo_detalle - id.anegativo_detalle) * 1.0 / 2, NULL) AS media_a,
                COALESCE((id.bpositivo_detalle - id.bnegativo_detalle) * 1.0 / 2, NULL) AS media_b
            FROM inclinometros i
            INNER JOIN inclinometro_encabezado ie ON i.id_inclinometro = ie.id_inclinometro
            INNER JOIN {tabla} id ON ie.id_encabezado = id.id_encabezado
            INNER JOIN instrumentacion t ON i.id_inclinometro = t.id_equipo
            INNER JOIN componentes c ON t.id_componente = c.id_componente
            WHERE i.tipo_inclinometro = 'GEOKON' AND i.id_inclinometro = ? AND ie.estado_base != 2
        ),
        base_values AS (
            SELECT nombre_inclinometro, profundidad_detalle, fecha_inclinometro AS fecha_base,
                COALESCE(media_a, NULL) AS media_a_base,
                COALESCE(media_b, NULL) AS media_b_base
            FROM detalle_calculado WHERE estado_base = 1
        )
        SELECT dc.nombre_inclinometro, dc.fecha_inclinometro, dc.profundidad_detalle,
            SUM(COALESCE(dc.media_a - COALESCE(bv.media_a_base, dc.media_a), NULL))
            OVER (PARTITION BY dc.nombre_inclinometro, dc.fecha_inclinometro
            ORDER BY dc.profundidad_detalle ASC) * {unidadmedida} AS Desplaz_Acumula_A
        FROM detalle_calculado dc
        LEFT JOIN base_values bv ON dc.nombre_inclinometro = bv.nombre_inclinometro
            AND dc.profundidad_detalle = bv.profundidad_detalle
        WHERE dc.estado_base <> 1 AND dc.fecha_inclinometro >= bv.fecha_base
        ORDER BY dc.fecha_inclinometro ASC, dc.profundidad_detalle DESC;
        """
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (id_inclinometro,))
            rows = cur.fetchall()
            if rows:
                return rows
            else:
                return None
        except Error as e:
            print("Error al consultar incli geokon A acum: " + str(e))
            return None
        finally:
            if conn:
                conn.close()

                
    def mdlObtener_datos_incli_reporte(idcomponente):
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            sql = """SELECT inst.id_equipo,inst.nombre_equipo,incl.tipo_inclinometro FROM instrumentacion inst INNER JOIN inclinometros incl ON inst.id_equipo=incl.id_inclinometro WHERE inst.tipo_equipo='INCLINOMETRO' and inst.id_componente=?"""
            cur.execute(sql, (idcomponente,))
            resultado = cur.fetchall()
            if resultado:
                return resultado
            else:
                return None 
        except Error as e:
            print("Error al obtener tipo inclino:", e)
            return None
        finally:
            if conn:
                conn.close()
    
    def mdlTraerDataInclinometro(idinclinometro):
        sql = """SELECT i.id_instrumentacion, i.id_componente, c.nombre_componente FROM instrumentacion i
        INNER JOIN componentes c ON i.id_componente = c.id_componente
        WHERE i.id_equipo = ? AND i.tipo_equipo = 'INCLINOMETRO';"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (idinclinometro,))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Error as e:
            print("Error al traer data inclino: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
    