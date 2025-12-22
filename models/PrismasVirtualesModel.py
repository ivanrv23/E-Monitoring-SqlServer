from services.security.apis.conexiones.connection import Connection

class PrismasVirtualesModel:
    
    @staticmethod
    def mdlListarPrismasVirtualesProyecto(proyecto, idcomponente, idequipo):
        sql = f"""SELECT c.id_componente, p.* FROM prismas_virtuales p INNER JOIN instrumentacion t
        ON p.id_prisma_virtual = t.id_equipo INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_equipo = ? AND c.id_componente = ?;"""
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idequipo, idcomponente))
            row = cur.fetchone()
            if row:
                return row
            else:
                return None
        except Exception as e:
            print("Error al consultar equipo adicional: " + str(e))
            return None
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def mdlPrismasVirtuales(ids):
        # Convertir IDs a enteros y eliminar duplicados
        ids = list(set(int(id) for id in ids))
        
        # Construir la consulta SQL dinámicamente
        if not ids:
            return None
            
        placeholders = ','.join(['?' for _ in ids])
        sql = f"""
            SELECT
                p.nombre_prisma_virtual, 
                p.coordenada_x, 
                p.coordenada_y, 
                p.coordenada_z, 
                p.radio_prisma_virtual
            FROM 
                prismas_virtuales p
            INNER JOIN 
                instrumentacion i 
            ON 
                p.id_prisma_virtual = i.id_equipo
            WHERE 
                i.id_equipo IN ({placeholders})
                AND i.tipo_equipo = 'PRISMAVIRTUAL';
        """
        conn = None
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Ejecutar la consulta con la lista de ids (convertida a tupla)
            cur.execute(sql, tuple(ids))  # Convertir ids a tupla
            rows = cur.fetchall()  # Obtener todos los resultados
            if rows:
                return rows
            else:
                return None
        except Exception as e:
            print("Error al consultar datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()