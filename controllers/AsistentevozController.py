import pyttsx3
import speech_recognition as sr
import noisereduce as nr
import numpy as np
import time
from models.AsistentevozModel import AsistenteVozModel

class AsistenteVozController:
    motor_tts = pyttsx3.init()  # Inicializa el motor TTS una vez

    asistente_en_ejecucion = True
    tiempo_inactividad_maximo = 300  # Tiempo máximo (en segundos)
    ultima_actividad_tiempo = time.time()

    @staticmethod
    def iniciarAsistente():
        AsistenteVozController.asistente_en_ejecucion = True
        activation_phrase = "iniciar asistente"
        asistente = AsistenteVozController()

        while AsistenteVozController.asistente_en_ejecucion:
            command = asistente.reconocer_voz()

            if command and activation_phrase in command:
                asistente.responder_audio("¡Hola! Soy tu asistente de voz. ¿En qué puedo ayudarte hoy?")
                AsistenteVozController.ultima_actividad_tiempo = time.time()

                while AsistenteVozController.asistente_en_ejecucion:
                    command = asistente.reconocer_voz()
                    AsistenteVozController.ultima_actividad_tiempo = time.time()

                    if command:
                        if "detener asistente" in command:
                            asistente.despedirse()
                            AsistenteVozController.asistente_en_ejecucion = False
                            break
                        elif "primer análisis" in command:
                            asistente.analisis1()
                        elif "segundo análisis" in command:
                            asistente.analisis2()
                        elif "tercer análisis" in command:
                            asistente.analisis3()
                        elif "cuarto análisis" in command:
                            asistente.analisis4()
                        elif "quinto análisis" in command:
                            asistente.analisis5()
                        else:
                            asistente.no_entendido()

            if time.time() - AsistenteVozController.ultima_actividad_tiempo > AsistenteVozController.tiempo_inactividad_maximo:
                AsistenteVozController.asistente_en_ejecucion = False
            elif command:
                print("Esperando activación...")

    @staticmethod
    def responder_audio(texto):
        AsistenteVozController.motor_tts.say(texto)
        AsistenteVozController.motor_tts.runAndWait()

    @staticmethod
    def despedirse():
        AsistenteVozController.responder_audio("Hasta luego. ¡Que tengas un buen día!")

    @staticmethod
    def analisis1():
        AsistenteVozController.responder_audio("El ajuste es muy bajo, esta curva tiene muy mala tendencia, No hay peligro")

    @staticmethod
    def analisis2():
        AsistenteVozController.responder_audio("El ajuste es bajo, esta curva tiene mala tendencia, No hay peligro")

    @staticmethod
    def analisis3():
        AsistenteVozController.responder_audio("El ajuste es regular, esta curva tiene tendencia regular, podriamos estar en peligro o estar en movimiento constante por ahora sin aceleración")

    @staticmethod
    def analisis4():
        AsistenteVozController.responder_audio("El ajuste es muy bueno, esta curva tiene buena tendencia, podriamos estar en peligro o estar en movimiento constante por ahora sin aceleración, si la curva es exponencial ve a campo y mira que pasa")

    @staticmethod
    def analisis5():
        AsistenteVozController.responder_audio("El ajuste es muy bueno, esta curva tiene muy buena tendencia, si la curva es exponencial por favor toma accion inmediata, si es lineal sigue monitoreando pero no te descuides")

    @staticmethod
    def no_entendido():
        AsistenteVozController.responder_audio("Lo siento, no entiendo ese comando. ¿Puedes repetirlo?")

    @staticmethod
    def reconocer_voz():
        reconocedor = sr.Recognizer()

        try:
            with sr.Microphone() as source:
                audio = reconocedor.listen(source, timeout=5)

            audio_array = np.frombuffer(audio.frame_data, dtype=np.int16)
            sr_audio = audio.sample_rate

            # Reducción de ruido utilizando noisereduce
            audio_reducido = nr.reduce_noise(audio_array, sr=sr_audio)

            audio_reducido_data = sr.AudioData(audio_reducido.tobytes(), sample_rate=sr_audio, sample_width=2)
            texto = reconocedor.recognize_google(audio_reducido_data, language="es-ES")
            return texto.lower()

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            AsistenteVozController.asistente_en_ejecucion = False
            return ""
    
    def ctrlObtenerInformacionPrismas(tabla, prismas, idcomponente, fechaini, fechafin):
        data = AsistenteVozModel.mdlObtenerInformacionPrismas(tabla, prismas, idcomponente, fechaini, fechafin)
        return data
    
    def ctrlResumenVozDesplazamiento(tabla, prismas, idcomponente, fechaini, fechafin):
        data = AsistenteVozModel.mdlResumenVozDesplazamiento(tabla, prismas, idcomponente, fechaini, fechafin)
        return data
    
    def ctrlResumenVozVelocidad(tabla, prismas, idcomponente, fechaini, fechafin):
        data = AsistenteVozModel.mdlResumenVozVelocidad(tabla, prismas, idcomponente, fechaini, fechafin)
        return data
    