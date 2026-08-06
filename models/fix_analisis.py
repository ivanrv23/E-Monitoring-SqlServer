import re
import os

def fix_analisis_model(input_file, output_file):
    """
    Script a prueba de balas para AnalisisModel.py.
    Rastrea bloques SQL y CTEs para inyectar el JOIN y el filtro de grupo_puntos
    únicamente en el contexto correcto, evitando errores de sintaxis.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out_lines = []
    
    # Variables de estado para rastrear el contexto SQL
    in_sql_string = False
    current_alias = None
    join_found_in_current_block = False
    where_found_in_current_block = False
    injected_filter_in_current_block = False

    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 1. Detectar inicio y fin de cadenas SQL (f""" o """)
        if ('sql = f"""' in line or 'sql = """' in line or 'sql=f"""' in line) and not in_sql_string:
            in_sql_string = True
            # Resetear estado para cada nueva consulta
            current_alias = None
            join_found_in_current_block = False
            where_found_in_current_block = False
            injected_filter_in_current_block = False
            
        if in_sql_string and line.strip().endswith('"""'):
            in_sql_string = False
            current_alias = None
            join_found_in_current_block = False
            where_found_in_current_block = False
            injected_filter_in_current_block = False

        # 2. Detectar el JOIN con instrumentacion y capturar el alias (p o datos)
        join_match = re.search(r'(INNER\s+)?JOIN\s+instrumentacion\s+i\s+ON\s+([a-zA-Z0-9_]+)\.nombre_prisma\s*=\s*i\.nombre_equipo', line, re.IGNORECASE)
        if join_match and in_sql_string:
            current_alias = join_match.group(2)
            join_found_in_current_block = True
            where_found_in_current_block = False
            injected_filter_in_current_block = False
            
            out_lines.append(line)
            
            # Inyectar JOIN con componentes si no existe ya (Idempotente)
            if i + 1 < len(lines) and 'INNER JOIN componentes co' not in lines[i+1]:
                indent = re.match(r'^(\s*)', line).group(1)
                out_lines.append(f"{indent}INNER JOIN componentes co ON i.id_componente = co.id_componente\n")
            i += 1
            continue

        # 3. Detectar el WHERE asociado a este bloque
        if join_found_in_current_block and not where_found_in_current_block and re.match(r'^\s*WHERE\s+', line, re.IGNORECASE):
            where_found_in_current_block = True
            
        # 4. Lógica de inyección del filtro dentro del WHERE correcto
        if join_found_in_current_block and where_found_in_current_block and not injected_filter_in_current_block:
            
            # Verificar si el bloque SQL/CTE termina (ORDER BY, GROUP BY, cierre de CTE ')', UNION)
            is_block_end = False
            if re.match(r'^\s*(GROUP\s+BY|ORDER\s+BY|HAVING|UNION|UNION\s+ALL)\b', line, re.IGNORECASE):
                is_block_end = True
            if line.strip() == ')' or line.strip().startswith(')'):
                is_block_end = True
            if '"""' in line and line.strip().endswith('"""'):
                is_block_end = True
                
            if is_block_end:
                # Si el bloque termina sin haber encontrado el filtro, lo inyectamos ANTES de esta línea
                if 'grupo_puntos = co.nombre_componente' not in line and (i - 1 < 0 or 'grupo_puntos = co.nombre_componente' not in lines[i-1]):
                    indent = re.match(r'^(\s*)', line).group(1)
                    filter_line = f"{indent}AND ({current_alias}.grupo_puntos = co.nombre_componente OR {current_alias}.grupo_puntos IS NULL OR {current_alias}.grupo_puntos = '')\n"
                    out_lines.append(filter_line)
                
                # Resetear estado para el siguiente bloque (ej. después de un UNION)
                injected_filter_in_current_block = True
                where_found_in_current_block = False
                join_found_in_current_block = False
                out_lines.append(line)
                i += 1
                continue

            # Si no termina el bloque, buscar la condición de componente para inyectar justo después
            if 'i.id_componente = ?' in line or 'i.id_instrumentacion = ?' in line:
                # Verificación de idempotencia (por si el script se ejecuta dos veces)
                if 'grupo_puntos = co.nombre_componente' not in line and (i + 1 >= len(lines) or 'grupo_puntos = co.nombre_componente' not in lines[i+1]):
                    out_lines.append(line)
                    indent = re.match(r'^(\s*)', line).group(1)
                    filter_line = f"{indent}AND ({current_alias}.grupo_puntos = co.nombre_componente OR {current_alias}.grupo_puntos IS NULL OR {current_alias}.grupo_puntos = '')\n"
                    out_lines.append(filter_line)
                else:
                    out_lines.append(line)
                    
                injected_filter_in_current_block = True
                where_found_in_current_block = False
                join_found_in_current_block = False
                i += 1
                continue

        # 5. Si encontramos un UNION, resetear el estado para evaluar el siguiente bloque SELECT
        if re.match(r'^\s*(UNION|UNION\s+ALL)\b', line, re.IGNORECASE):
            join_found_in_current_block = False
            where_found_in_current_block = False
            injected_filter_in_current_block = False
            current_alias = None

        out_lines.append(line)
        i += 1

    # Guardar el archivo corregido
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(out_lines)
        
    print(f"✅ Proceso completado. Se aplicaron los ajustes correctamente respetando los CTEs.")
    print(f"📁 Archivo generado: {output_file}")

if __name__ == "__main__":
    # Búsqueda inteligente de rutas
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_filename = os.path.join(script_dir, 'AnalisisModel.py')
    if not os.path.exists(input_filename):
        input_filename = os.path.join(script_dir, 'models', 'AnalisisModel.py')
        
    output_filename = input_filename.replace('AnalisisModel.py', 'AnalisisModel_FIXED.py')
    
    if os.path.exists(input_filename):
        fix_analisis_model(input_filename, output_filename)
    else:
        print(f"❌ Error: No se encontró el archivo 'AnalisisModel.py' ni en la raíz ni en la carpeta 'models'.")