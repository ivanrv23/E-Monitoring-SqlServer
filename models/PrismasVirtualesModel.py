from services.security.apis.conexiones.connection import Connection

class PrismasVirtualesModel:
    
    @staticmethod
    def mdlListarPrismasVirtualesProyecto(proyecto, idcomponente, idequipo):
        conn = None
        sql = f"""SELECT c.id_componente, p.* FROM prismas_virtuales p INNER JOIN instrumentacion t
        ON p.id_prisma_virtual = t.id_equipo INNER JOIN componentes c ON t.id_componente = c.id_componente
        WHERE c.id_proyecto = ? AND t.id_equipo = ? AND c.id_componente = ?;"""
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            cur.execute(sql, (proyecto, idequipo, idcomponente))
            row = cur.fetchone()
            if row:
                return tuple(row)
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
        conn = None
        # Convertir IDs a enteros y eliminar duplicados para asegurar integridad
        # Esto es importante en SQL Server para evitar conversiones implícitas de tipos
        ids_procesados = list(set(int(id) for id in ids))
        
        # Generar placeholders dinámicos para la cláusula IN
        placeholders = ','.join(['?' for _ in ids_procesados])
        
        # Construir la consulta SQL dinámicamente
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
        
        try:
            conn = Connection.connectionDB()
            cur = conn.cursor()
            # Ejecutar la consulta pasando la lista procesada
            cur.execute(sql, ids_procesados)
            rows = cur.fetchall()
            
            # Regla Crítica: Convertir filas de pyodbc a tuplas nativas
            results = [tuple(row) for row in rows]
            
            if results:
                return results
            else:
                return None
        except Exception as e:
            print("Error al consultar datos: " + str(e))
            return None
        finally:
            if conn:
                conn.close()