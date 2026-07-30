import re
import os

def fix_velocidad_model(input_file, output_file):
    """
    Lee el archivo VelocidadModel.py, inyecta el JOIN con componentes y el filtro de grupo_puntos
    en todas las consultas SQL que hagan JOIN con instrumentacion, manejando CTEs y UNIONs.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out_lines = []
    current_alias = None
    modifications = 0
    
    for i, line in enumerate(lines):
        # Resetear el contexto del alias cada vez que inicia una nueva consulta SQL
        if 'sql = f' in line:
            current_alias = None

        # 1. Detectar la cláusula FROM que hace JOIN con instrumentacion
        # Soporta "INNER JOIN" y "JOIN", y captura el alias de la tabla (p o datos)
        match_from = re.search(
            r'(FROM\s+\{tabla\}\s+(\w+)\s+(?:INNER\s+)?JOIN\s+instrumentacion\s+i\s+ON\s+\2\.nombre_prisma\s*=\s*i\.nombre_equipo)', 
            line, re.IGNORECASE
        )
        
        if match_from:
            current_alias = match_from.group(2) # Será 'p' o 'datos'
            out_lines.append(line)
            
            # Inyectar el JOIN con la tabla componentes
            indent = re.match(r'^(\s*)', line).group(1)
            out_lines.append(f"{indent}INNER JOIN componentes co ON i.id_componente = co.id_componente\n")
            continue

        # 2. Detectar la condición WHERE para el componente
        if current_alias and 'i.id_componente = ?' in line:
            # Prevenir doble inyección si el script se ejecuta más de una vez
            if 'grupo_puntos = co.nombre_componente' not in line and \
               (i + 1 >= len(lines) or 'grupo_puntos = co.nombre_componente' not in lines[i+1]):
                
                out_lines.append(line)
                indent = re.match(r'^(\s*)', line).group(1)
                filter_line = f"{indent}AND ({current_alias}.grupo_puntos = co.nombre_componente OR {current_alias}.grupo_puntos IS NULL OR {current_alias}.grupo_puntos = '')\n"
                out_lines.append(filter_line)
                modifications += 1
                continue
        
        out_lines.append(line)

    # Guardar el archivo modificado
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(out_lines)
        
    print(f"✅ Proceso completado. Se aplicaron los ajustes en {modifications} bloques de consultas SQL.")
    print(f"📁 Archivo generado: {output_file}")

# ==========================================
# Instrucciones de uso:
# ==========================================
if __name__ == "__main__":
    # 1. Obtener la ruta absoluta de la carpeta donde está guardado ESTE script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Definir rutas inteligentes (busca en la misma carpeta o en la subcarpeta 'models')
    input_filename = os.path.join(script_dir, 'VelocidadModel.py')
    if not os.path.exists(input_filename):
        input_filename = os.path.join(script_dir, 'models', 'VelocidadModel.py')
        
    # El archivo de salida se guardará junto al original con el sufijo _FIXED
    output_filename = input_filename.replace('VelocidadModel.py', 'VelocidadModel_FIXED.py')
    
    print(f"🔍 Buscando archivo en: {input_filename}")
    
    # 3. Ejecutar si existe
    if os.path.exists(input_filename):
        fix_velocidad_model(input_filename, output_filename)
    else:
        print(f"❌ Error: No se encontró el archivo 'VelocidadModel.py' ni en la raíz ni en la carpeta 'models'.")