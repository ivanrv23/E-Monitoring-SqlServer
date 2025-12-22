import pandas as pd

def cargar_archivo(archivo_ruta_completa):
    if archivo_ruta_completa:
        # Asegurarse de que archivo_ruta_completa sea una cadena, no una lista
        if isinstance(archivo_ruta_completa, list):
            archivo = archivo_ruta_completa[0]  # Tomar el primer archivo si es una lista
        else:
            archivo = archivo_ruta_completa
        # Verifica la extensión del archivo
        if archivo.endswith('.csv') or archivo.endswith('.txt'):
            try:
                # Intentar leer con utf-8 (que soporta bien caracteres especiales como °)
                df = pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(archivo, encoding='latin-1')
            # Extraer el encabezado del archivo
            encabezado_archivo = [col.strip() for col in df.columns.tolist()]
            # Guardar el encabezado en un archivo de texto
            with open('encabezado_guardado.txt', 'w', encoding='utf-8') as f:
                f.write(','.join(encabezado_archivo))
    