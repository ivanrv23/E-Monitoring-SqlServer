import csv
import datetime
import random

# --- Parámetros de la generación ---
FECHA_INICIO = datetime.date(2020, 1, 1)
FECHA_FIN = datetime.date(2025, 12, 31)
HORA_LECTURA_DIARIA = "12:00:00"  # Hora fija para la única lectura del día
NOMBRE_ARCHIVO = "datos_diarios_completos.csv"

# --- Proceso de generación ---
print(f"Generando datos desde {FECHA_INICIO.strftime('%d/%m/%Y')} hasta {FECHA_FIN.strftime('%d/%m/%Y')}...")

with open(NOMBRE_ARCHIVO, mode='w', newline='', encoding='utf-8') as archivo_csv:
    # Usamos punto y coma como delimitador para compatibilidad con Excel en español
    escritor_csv = csv.writer(archivo_csv, delimiter=';')
    
    # Escribir la cabecera
    escritor_csv.writerow(['Fecha', 'Hora', 'Valor'])
    
    # Iterar por cada día en el rango
    fecha_actual = FECHA_INICIO
    delta = datetime.timedelta(days=1)
    
    while fecha_actual <= FECHA_FIN:
        fecha_str = fecha_actual.strftime("%d/%m/%Y")
        
        # Generar un valor aleatorio entre 0.0 y 8.0 con dos decimales
        valor = round(random.uniform(0.0, 20.0), 2)
        
        # Escribir la única fila para el día actual
        # Reemplaza el punto por coma para el formato decimal en español
        escritor_csv.writerow([fecha_str, HORA_LECTURA_DIARIA, str(valor).replace('.', ',')])

        fecha_actual += delta

print(f"¡Listo! Se ha creado el archivo '{NOMBRE_ARCHIVO}' con éxito.")