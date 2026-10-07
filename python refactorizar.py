import re

ruta_archivo = 'models/DesplazamientoModel.py' # Ajusta la ruta si es diferente

with open(ruta_archivo, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Añadir import pandas al inicio si no está
if 'import pandas as pd' not in content:
    content = content.replace('from mysql.connector import Error', 'from mysql.connector import Error\nimport pandas as pd')

# 2. Reemplazar el patrón 1: "return row if row else None"
content = re.sub(
    r'(cur\.execute\(sql, params\)\s+)row = cur\.fetchall\(\)\s+return row if row else None',
    r'\1df = pd.read_sql(sql, conn, params=params)\n        return df if not df.empty else None',
    content
)

# 3. Reemplazar el patrón 2: "if row: return row else: return None"
content = re.sub(
    r'(cur\.execute\(sql, params\)\s+)row = cur\.fetchall\(\)\s+if row:\s+return row\s+else:\s+return None',
    r'\1df = pd.read_sql(sql, conn, params=params)\n        return df if not df.empty else None',
    content
)

with open(ruta_archivo, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Modelo refactorizado con éxito a Pandas.")