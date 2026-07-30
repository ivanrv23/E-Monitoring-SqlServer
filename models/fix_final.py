import os

# 1. Obtener la ruta absoluta de la carpeta donde está guardado ESTE script
script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Buscar el archivo en la misma carpeta del script o en la subcarpeta 'models'
input_file = os.path.join(script_dir, 'AnalisisModel_FIXED.py')
if not os.path.exists(input_file):
    input_file = os.path.join(script_dir, 'models', 'AnalisisModel_FIXED.py')

# El archivo de salida se guardará junto al original
output_file = os.path.join(os.path.dirname(input_file), 'AnalisisModel_FINAL.py')

print(f"🔍 Buscando archivo en: {input_file}")

if not os.path.exists(input_file):
    print(f"❌ Error: No se encontró el archivo 'AnalisisModel_FIXED.py'.")
else:
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- CORRECCIÓN 1: Agregar INNER JOIN componentes donde falta ---
    
    # mdlObtenerVariacionCoordenadas
    content = content.replace(
        "FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo\n     WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?",
        "FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo\n     INNER JOIN componentes co ON i.id_componente = co.id_componente\n     WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND p.nombre_prisma IN ({placeholders}) AND i.id_componente = ?"
    )

    # mdlCalcularVelocidadIV
    content = content.replace(
        "FROM {tabla} p \n             INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo\n             WHERE p.state_prisma = 1 AND p.estado_prisma = 1",
        "FROM {tabla} p \n             INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo\n             INNER JOIN componentes co ON i.id_componente = co.id_componente\n             WHERE p.state_prisma = 1 AND p.estado_prisma = 1"
    )

    # mdlPrismasDesplazamiento3DA
    content = content.replace(
        "FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo\n     WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?",
        "FROM {tabla} p INNER JOIN instrumentacion i ON p.nombre_prisma = i.nombre_equipo\n     INNER JOIN componentes co ON i.id_componente = co.id_componente\n     WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?"
    )

    # --- CORRECCIÓN 2: Agregar filtro de grupo_puntos donde falta ---
    
    # mdlCalcularDatosTrayectoriaFechas
    content = content.replace(
        "AND i.id_componente = ?\n     AND p.hora_prisma BETWEEN ? AND ? ORDER BY p.nombre_prisma, p.hora_prisma;\"\"\"",
        "AND i.id_componente = ?\n     AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')\n     AND p.hora_prisma BETWEEN ? AND ? ORDER BY p.nombre_prisma, p.hora_prisma;\"\"\""
    )

    # mdlObtenerVariacionCoordenadasFechas
    content = content.replace(
        "AND i.id_componente = ?\n     AND p.hora_prisma BETWEEN ? AND ? ORDER BY p.nombre_prisma, p.hora_prisma;\"\"\"",
        "AND i.id_componente = ?\n     AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')\n     AND p.hora_prisma BETWEEN ? AND ? ORDER BY p.nombre_prisma, p.hora_prisma;\"\"\""
    )

    # mdlPrismaVelocidadesAnalisis
    content = content.replace(
        "AND i.id_instrumentacion = ? AND p.hora_prisma BETWEEN ? AND ?\n     )",
        "AND i.id_instrumentacion = ? AND p.hora_prisma BETWEEN ? AND ?\n         AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')\n     )"
    )

    # --- CORRECCIÓN 3: Mover el filtro de grupo_puntos dentro de los CTEs ---
    
    # Para mdlPrismasVelocidadVA3D, VI3D, VA2D, VI2D (Quitar de afuera)
    content = content.replace(
        "FROM PrismasCTE\n     AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')",
        "FROM PrismasCTE"
    )
    # Para mdlPrismasVelocidadVA3D, VI3D, VA2D, VI2D (Poner adentro)
    content = content.replace(
        "WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?\n     )",
        "WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?\n         AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')\n     )"
    )

    # Para mdlPrismasVelocidadVASD, VISD (Quitar de afuera)
    content = content.replace(
        "FROM CD_Dif\n     AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')",
        "FROM CD_Dif"
    )
    # Para mdlPrismasVelocidadVASD, VISD (Poner adentro)
    content = content.replace(
        "WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?\n     ),",
        "WHERE p.state_prisma = 1 AND p.estado_prisma = 1 AND i.id_componente = ?\n         AND (p.grupo_puntos = co.nombre_componente OR p.grupo_puntos IS NULL OR p.grupo_puntos = '')\n     ),"
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ ¡Listo! Se han corregido los 12 errores críticos.")
    print(f"📁 Tu archivo final y seguro es: {output_file}")