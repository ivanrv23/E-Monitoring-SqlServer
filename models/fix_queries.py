import re
import os

def fix_desplazamiento_model(input_file, output_file):
    """
    Lee el archivo modelo, inyecta el JOIN con componentes y el filtro de grupo_puntos
    en todas las consultas SQL que hagan JOIN con instrumentacion.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out_lines = []
    i = 0
    functions_modified = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Regex para capturar el JOIN con instrumentacion y el alias (p o datos)
        match_join = re.search(r'^(\s*)(?:FROM\s+[\w\{\}]+\s+\w+\s+)?INNER JOIN instrumentacion i ON (\w+)\.nombre_prisma = i\.nombre_equipo', line)
        
        if match_join:
            indent = match_join.group(1)
            alias = match_join.group(2) # Será 'p' o 'datos'
            
            # 1. Agregar la línea original del JOIN
            out_lines.append(line)
            
            # 2. Verificar si ya existe el JOIN con componentes para evitar duplicados
            if i + 1 < len(lines) and 'INNER JOIN componentes co ON i.id_componente = co.id_componente' in lines[i+1]:
                pass # Ya existe, no hacer nada
            else:
                # Inyectar el JOIN con la tabla componentes
                out_lines.append(f"{indent}INNER JOIN componentes co ON i.id_componente = co.id_componente\n")
            
            # 3. Buscar el WHERE correspondiente a este bloque SQL
            j = i + 1
            where_idx = -1
            while j < len(lines):
                if re.match(r'^\s*WHERE\s+', lines[j]):
                    where_idx = j
                    break
                # Si nos topamos con otro FROM, WITH o SELECT (sin INNER JOIN), nos pasamos de bloque
                if re.match(r'^\s*(FROM|WITH|SELECT)\s+', lines[j]) and 'INNER JOIN' not in lines[j]:
                    break
                j += 1
            
            if where_idx != -1:
                # Copiar las líneas intermedias (ej. otros INNER JOIN como ValoresCero o fechas_inicio)
                for k in range(i + 1, where_idx):
                    out_lines.append(lines[k])
                
                # Agregar la línea WHERE
                out_lines.append(lines[where_idx])
                
                # 4. Buscar dónde insertar el filtro de grupo_puntos dentro del WHERE
                k = where_idx + 1
                inserted = False
                while k < len(lines):
                    cond_line = lines[k]
                    
                    # Opción A: Insertar justo después de "i.id_componente = ?"
                    if 'i.id_componente = ?' in cond_line:
                        out_lines.append(cond_line)
                        cond_indent = re.match(r'^(\s*)', cond_line).group(1)
                        filter_line = f"{cond_indent}AND ({alias}.grupo_puntos = co.nombre_componente OR {alias}.grupo_puntos IS NULL OR {alias}.grupo_puntos = '')\n"
                        out_lines.append(filter_line)
                        inserted = True
                        i = k # Actualizar índice para saltar líneas procesadas
                        functions_modified += 1
                        break
                        
                    # Opción B: Si llegamos al final del WHERE (GROUP BY, ORDER BY), insertar antes
                    elif re.match(r'^\s*(GROUP BY|ORDER BY|HAVING)', cond_line):
                        cond_indent = re.match(r'^(\s*)', cond_line).group(1)
                        filter_line = f"{cond_indent}AND ({alias}.grupo_puntos = co.nombre_componente OR {alias}.grupo_puntos IS NULL OR {alias}.grupo_puntos = '')\n"
                        out_lines.append(filter_line)
                        out_lines.append(cond_line)
                        inserted = True
                        i = k
                        functions_modified += 1
                        break
                    else:
                        out_lines.append(cond_line)
                    k += 1
                
                if not inserted:
                    i = k - 1
        else:
            out_lines.append(line)
            
        i += 1

    # Guardar el archivo modificado
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(out_lines)
        
    print(f"✅ Proceso completado. Se aplicaron los ajustes en {functions_modified} bloques de consultas SQL.")
    print(f"📁 Archivo generado: {output_file}")
    return functions_modified

# ==========================================
# Instrucciones de uso:
# ==========================================
if __name__ == "__main__":
    # 1. Obtener la ruta absoluta de la carpeta donde está guardado ESTE script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Definir rutas inteligentes (busca en la misma carpeta o en la subcarpeta 'models')
    input_filename = os.path.join(script_dir, 'DesplazamientoModel.py')
    if not os.path.exists(input_filename):
        input_filename = os.path.join(script_dir, 'models', 'DesplazamientoModel.py')
        
    # El archivo de salida se guardará junto al original con el sufijo _FIXED
    output_filename = input_filename.replace('DesplazamientoModel.py', 'DesplazamientoModel_FIXED.py')
    
    print(f"🔍 Buscando archivo en: {input_filename}")
    
    # 3. Ejecutar si existe
    if os.path.exists(input_filename):
        fix_desplazamiento_model(input_filename, output_filename)
    else:
        print(f"❌ Error: No se encontró el archivo 'DesplazamientoModel.py' ni en la raíz ni en la carpeta 'models'.")