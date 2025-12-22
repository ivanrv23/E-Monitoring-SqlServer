from cx_Freeze import setup, Executable

setup(
    name="MiPrograma",
    version="1.0",
    description="Mi aplicación Python",
    executables=[Executable("ejemplo.py")]
)