import os
import psutil
import win32api
import win32com.client as win32
import shutil
import time

from utils.common.rutasarchivos import resource_path
class ActualizarReporte:
    def limpiar_cache_win32com():
        cache_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Temp', 'gen_py')
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
            except Exception as e:
                print(f"Error limpiando caché COM: {str(e)}")

    def obtener_pid_word(word_app: win32.CDispatch) -> int:
        try:
            hwnd = word_app.Hwnd
            _, pid = win32api.GetWindowThreadProcessId(hwnd)
            return pid
        except Exception as e:
            return -1

    def terminar_instancia_word(pid: int):
        if pid <= 0:
            return
        try:
            proceso = psutil.Process(pid)
            proceso.terminate()
        except psutil.NoSuchProcess:
            print("El proceso ya no existe.")
        except Exception as e:
            print(f"Error terminando proceso: {str(e)}")

    def guardar_y_actualizar_indice_y_ajustar_tablas(ruta_doc,ruta_pdf,doc):
        # Configurar rutas absolutas
        doc_path = resource_path(ruta_doc)
        pdf_path = resource_path(ruta_pdf)

        # Eliminar archivos existentes
        for file_path in [doc_path, pdf_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    return False

        # Guardar documento inicial
        try:
            doc.save(doc_path)
        except Exception as e:
            return False

        # Configurar variables de control
        word_app = None
        word_doc = None
        word_pid = -1
        intentos = 3

        for intento in range(intentos):
            try:
                # Limpiar cache antes de cada intento
                ActualizarReporte.limpiar_cache_win32com()

                # Crear nueva instancia independiente de Word
                word_app = win32.DispatchEx("Word.Application")
                word_app.Visible = False
                word_app.DisplayAlerts = False
                word_pid = ActualizarReporte.obtener_pid_word(word_app)

                # Abrir documento
                word_doc = word_app.Documents.Open(doc_path)

                # Actualizar índice de contenido
                if ActualizarReporte.actualizar_indice_contenido(word_doc):
                    print("Índice actualizado correctamente")

                # Ajustar tablas al contenido
                ActualizarReporte.ajustar_tablas(word_doc)

                # Guardar cambios en .docx
                word_doc.Save()
                # Exportar a PDF
                ActualizarReporte.exportar_a_pdf(word_doc, pdf_path)
                return True

            except Exception as e:
                time.sleep(2)
            finally:
                # Cierre seguro en orden inverso
                if word_doc:
                    try:
                        word_doc.Close(SaveChanges=0)
                    except Exception as e:
                        print(f"Error cerrando documento: {str(e)}")
                
                if word_app:
                    try:
                        word_app.Quit(SaveChanges=0)
                    except Exception as e:
                        ActualizarReporte.terminar_instancia_word(word_pid)
                
                # Limpieza adicional
                word_doc = None
                word_app = None
                if word_pid > 0:
                    ActualizarReporte.terminar_instancia_word(word_pid)

        return False

    def actualizar_indice_contenido(word_doc) -> bool:
        """Actualiza el índice de contenido si existe el marcador"""
        try:
            bookmark_names = [bkm.Name for bkm in word_doc.Bookmarks]
            if "TOCPlaceholder" not in bookmark_names:
                return False

            toc_range = word_doc.Bookmarks("TOCPlaceholder").Range
            word_doc.TablesOfContents.Add(
                Range=toc_range,
                UseHeadingStyles=True,
                IncludePageNumbers=True
            )
            word_doc.TablesOfContents(1).Update()
            return True
        except Exception as e:
            return False

    def ajustar_tablas(word_doc):
        """Ajusta todas las tablas al contenido automáticamente"""
        try:
            for table in word_doc.Tables:
                table.AllowAutoFit = True
                table.AutoFitBehavior(1)  # wdAutoFitContent
            return True
        except Exception as e:
            return False

    def exportar_a_pdf(word_doc, pdf_path: str) -> bool:
        """Exporta el documento a PDF manteniendo formato"""
        try:
            word_doc.ExportAsFixedFormat(
                OutputFileName=pdf_path,
                ExportFormat=17,  # wdExportFormatPDF
                OptimizeFor=0,    # wdExportOptimizeForPrint
                CreateBookmarks=1 # wdExportCreateHeadingBookmarks
            )
            return True
        except Exception as e:
            return False
    