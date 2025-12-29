import re
from PySide6.QtGui import QKeySequence,QShortcut
from PySide6.QtWidgets import QApplication,QTableWidgetItem

def configurar_tabla_para_pegado(tabla):
    # Configura la tabla para que escuche pegados y siempre mantenga una fila en blanco
    tabla.setRowCount(1)
    tabla.itemChanged.connect(lambda: agregar_fila_en_blanco(tabla))
    shortcut = QShortcut(QKeySequence("Ctrl+V"), tabla)
    shortcut.activated.connect(lambda: pegar_desde_portapapeles(tabla))

def agregar_fila_en_blanco(tabla):
    # Agrega una fila en blanco si la última fila tiene algún dato
    ultima_fila = tabla.rowCount() - 1
    if any(tabla.item(ultima_fila, col) for col in range(tabla.columnCount())):
        tabla.insertRow(tabla.rowCount())  # Añade una nueva fila en blanco

def pegar_desde_portapapeles(tabla):
    clipboard = QApplication.clipboard()
    data = clipboard.text().strip()
    if not data:
        return
    filas = data.split("\n")
    es_encabezado, columnas_validas = comprobar_encabezado(filas[0])
    
    # Si se detecta encabezado, eliminamos esa fila de datos
    if es_encabezado:
        filas = filas[1:]
    
    # Insertar datos en las filas de la tabla
    insertar_datos(tabla, filas, columnas_validas, es_encabezado)
    
    # Asegurarse de que siempre haya una fila vacía al final
    asegurar_fila_vacia(tabla)

def comprobar_encabezado(primera_fila):
    encabezados_posibles = primera_fila.split("\t")
    es_encabezado = es_fila_encabezado_valido(encabezados_posibles)
    
    # Para celdas combinadas, identificar qué columnas tienen contenido
    columnas_validas = []
    if es_encabezado:
        for i, encabezado in enumerate(encabezados_posibles):
            if encabezado.strip():  # Solo columnas con contenido
                columnas_validas.append(i)
    
    return es_encabezado, columnas_validas

def es_fila_encabezado_valido(fila):
    celdas_no_vacias = [celda.strip() for celda in fila if celda.strip()]
    if not celdas_no_vacias:
        return False  # Si todas las celdas están vacías, no es encabezado
    
    # Verificación extra: si TODAS las celdas parecen números o fechas, definitivamente no es encabezado
    # (esto ayuda si copias una fila entera de fechas)
    es_todo_datos = all(re.search(r"^[\d/.-]+$", c) for c in celdas_no_vacias)
    if es_todo_datos:
        return False

    return all(es_encabezado_valido(celda) for celda in celdas_no_vacias)

def es_encabezado_valido(celda):
    # Si parece una fecha con barras (ej: 21/12/23), NO es un encabezado
    if re.search(r"\d+/\d+", celda):
        return False
    # Busca letras o símbolos (excluyendo la barra sola para no confundir con fechas)
    return bool(re.search(r"[A-Za-z()°%]", celda))

def insertar_datos(tabla, filas, columnas_validas, es_encabezado):
    fila_actual = tabla.currentRow()
    columna_actual = tabla.currentColumn()
    
    for i, fila in enumerate(filas):
        columnas = fila.split("\t")
        fila_tabla = fila_actual + i
        
        # Expandir filas si es necesario
        if fila_tabla >= tabla.rowCount():
            tabla.insertRow(tabla.rowCount())
        
        # Determinar qué columnas procesar
        if es_encabezado and columnas_validas:
            # Caso: hay encabezado con celdas combinadas
            visible_col = columna_actual
            for j in columnas_validas:
                if j >= len(columnas):
                    continue
                
                # Buscar la siguiente columna visible
                while visible_col < tabla.columnCount() and tabla.isColumnHidden(visible_col):
                    visible_col += 1
                
                # Establecer el valor de la celda
                if visible_col < tabla.columnCount():
                    tabla.setItem(fila_tabla, visible_col, QTableWidgetItem(columnas[j].strip()))
                    visible_col += 1
        else:
            # Caso: no hay encabezado o no hay celdas combinadas
            visible_col = columna_actual
            for j in range(len(columnas)):
                # Buscar la siguiente columna visible
                while visible_col < tabla.columnCount() and tabla.isColumnHidden(visible_col):
                    visible_col += 1
                
                # Establecer el valor de la celda
                if visible_col < tabla.columnCount():
                    tabla.setItem(fila_tabla, visible_col, QTableWidgetItem(columnas[j].strip()))
                    visible_col += 1

def asegurar_fila_vacia(tabla):
    cantidad_filas = tabla.rowCount()
    if cantidad_filas == 0 or tabla.item(cantidad_filas - 1, 0) is not None:
        tabla.insertRow(cantidad_filas)
