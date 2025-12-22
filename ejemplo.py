import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from obspy import read_inventory
import os

class LectorStationXML:
    def __init__(self, root):
        self.root = root
        self.root.title("Lector de StationXML con ObsPy")
        self.root.geometry("700x500")
        
        # Variables
        self.archivo_seleccionado = None
        self.inventory_data = None
        
        # Configurar la interfaz
        self.configurar_interfaz()
    
    def configurar_interfaz(self):
        # Marco principal
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = tk.Label(main_frame, text="Lector de StationXML - ObsPy", 
                         font=("Arial", 16, "bold"))
        titulo.pack(pady=(0, 20))
        
        # Marco para botones
        botones_frame = tk.Frame(main_frame)
        botones_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Botón para seleccionar archivo
        self.btn_seleccionar = tk.Button(botones_frame, text="📁 Seleccionar StationXML",
                                        command=self.seleccionar_archivo,
                                        bg="#4CAF50", fg="white", font=("Arial", 12),
                                        padx=20, pady=10)
        self.btn_seleccionar.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón para leer archivo
        self.btn_leer = tk.Button(botones_frame, text="📖 Leer Inventario",
                                 command=self.leer_archivo,
                                 bg="#2196F3", fg="white", font=("Arial", 12),
                                 padx=20, pady=10, state=tk.DISABLED)
        self.btn_leer.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón para limpiar
        self.btn_limpiar = tk.Button(botones_frame, text="🗑️ Limpiar",
                                    command=self.limpiar_resultados,
                                    bg="#FF9800", fg="white", font=("Arial", 12),
                                    padx=20, pady=10)
        self.btn_limpiar.pack(side=tk.LEFT)
        
        # Etiqueta para mostrar archivo seleccionado
        self.label_archivo = tk.Label(main_frame, text="Ningún archivo seleccionado",
                                     font=("Arial", 10), fg="gray")
        self.label_archivo.pack(anchor=tk.W, pady=(0, 10))
        
        # Área de texto para mostrar resultados
        self.texto_resultados = scrolledtext.ScrolledText(main_frame, 
                                                         width=80, height=20,
                                                         font=("Courier", 10))
        self.texto_resultados.pack(fill=tk.BOTH, expand=True)
        
        # Mensaje inicial
        self.agregar_mensaje("Bienvenido al lector de StationXML con ObsPy")
        self.agregar_mensaje("1. Haz clic en 'Seleccionar StationXML' para elegir un archivo")
        self.agregar_mensaje("2. Haz clic en 'Leer Inventario' para cargar los metadatos")
        self.agregar_mensaje("-" * 60)
    
    def seleccionar_archivo(self):
        """Abre el diálogo para seleccionar archivo XML"""
        tipos_archivo = [
            ("Archivos StationXML", "*.xml"),
            ("Todos los archivos", "*.*")
        ]
        
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo StationXML",
            filetypes=tipos_archivo
        )
        
        if archivo:
            self.archivo_seleccionado = archivo
            nombre_archivo = os.path.basename(archivo)
            self.label_archivo.config(text=f"Archivo seleccionado: {nombre_archivo}",
                                     fg="green")
            self.btn_leer.config(state=tk.NORMAL)
            self.agregar_mensaje(f"📁 Archivo seleccionado: {archivo}")
    
    def leer_archivo(self):
        """Lee el archivo StationXML seleccionado con ObsPy"""
        if not self.archivo_seleccionado:
            messagebox.showwarning("Advertencia", "Por favor selecciona un archivo primero")
            return
        
        try:
            self.agregar_mensaje(f"📖 Leyendo StationXML: {self.archivo_seleccionado}")
            self.agregar_mensaje("Procesando inventario...")
            
            # Actualizar interfaz
            self.root.update()
            
            # Leer el archivo con read_inventory
            self.inventory_data = read_inventory(self.archivo_seleccionado)
            
            # Mostrar información de éxito
            self.agregar_mensaje("✅ ¡Archivo StationXML leído correctamente!")
            self.agregar_mensaje(f"📊 Número de redes: {len(self.inventory_data)}")
            self.agregar_mensaje("")
            
            # Mostrar información del inventario
            self.agregar_mensaje("📈 Información del Inventario:")
            self.agregar_mensaje(str(self.inventory_data))
            self.agregar_mensaje("")
            
            # Mostrar detalles de redes y estaciones
            self.agregar_mensaje("📋 Detalles de redes y estaciones:")
            total_estaciones = 0
            total_canales = 0
            
            for network in self.inventory_data:
                self.agregar_mensaje(f"  Red: {network.code}")
                if network.description:
                    self.agregar_mensaje(f"    Descripción: {network.description}")
                self.agregar_mensaje(f"    Inicio: {network.start_date}")
                self.agregar_mensaje(f"    Fin: {network.end_date if network.end_date else 'Activa'}")
                self.agregar_mensaje(f"    Número de estaciones: {len(network.stations)}")
                total_estaciones += len(network.stations)
                
                for station in network.stations:
                    self.agregar_mensaje(f"      Estación: {station.code}")
                    self.agregar_mensaje(f"        Latitud: {station.latitude}°")
                    self.agregar_mensaje(f"        Longitud: {station.longitude}°")
                    self.agregar_mensaje(f"        Elevación: {station.elevation} m")
                    self.agregar_mensaje(f"        Inicio: {station.start_date}")
                    self.agregar_mensaje(f"        Fin: {station.end_date if station.end_date else 'Activa'}")
                    self.agregar_mensaje(f"        Canales: {len(station.channels)}")
                    total_canales += len(station.channels)
                    
                    # Mostrar algunos canales
                    for i, channel in enumerate(station.channels[:3]):  # Mostrar máximo 3 canales
                        self.agregar_mensaje(f"          Canal {i+1}: {channel.code}")
                        self.agregar_mensaje(f"            Frecuencia: {channel.sample_rate} Hz")
                        self.agregar_mensaje(f"            Azimut: {channel.azimuth}°")
                        self.agregar_mensaje(f"            Inclinación: {channel.dip}°")
                    
                    if len(station.channels) > 3:
                        self.agregar_mensaje(f"          ... y {len(station.channels) - 3} canales más")
                    
                    self.agregar_mensaje("")
                
                self.agregar_mensaje("")
            
            # Resumen final
            self.agregar_mensaje("📊 RESUMEN:")
            self.agregar_mensaje(f"  Total de redes: {len(self.inventory_data)}")
            self.agregar_mensaje(f"  Total de estaciones: {total_estaciones}")
            self.agregar_mensaje(f"  Total de canales: {total_canales}")
            
            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", "¡Archivo StationXML leído correctamente!")
            
        except Exception as e:
            error_msg = f"❌ Error al leer el archivo StationXML: {str(e)}"
            self.agregar_mensaje(error_msg)
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{str(e)}")
    
    def limpiar_resultados(self):
        """Limpia el área de resultados"""
        self.texto_resultados.delete(1.0, tk.END)
        self.archivo_seleccionado = None
        self.inventory_data = None
        self.label_archivo.config(text="Ningún archivo seleccionado", fg="gray")
        self.btn_leer.config(state=tk.DISABLED)
        
        # Mensaje inicial
        self.agregar_mensaje("Área de resultados limpiada")
        self.agregar_mensaje("Selecciona un nuevo archivo StationXML para continuar")
    
    def agregar_mensaje(self, mensaje):
        """Agrega un mensaje al área de texto"""
        self.texto_resultados.insert(tk.END, mensaje + "\n")
        self.texto_resultados.see(tk.END)
        self.root.update()

def main():
    # Verificar que ObsPy esté instalado
    try:
        import obspy
        print("ObsPy detectado correctamente")
    except ImportError:
        print("Error: ObsPy no está instalado")
        print("Instala ObsPy ejecutando: pip install obspy")
        return
    
    # Crear y ejecutar la aplicación
    root = tk.Tk()
    app = LectorStationXML(root)
    root.mainloop()

if __name__ == "__main__":
    main()