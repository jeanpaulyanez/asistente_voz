# 🎙️ Sistema de Asistencia de Voz Distribuido (DeepSeek-Pi)
**Framework de Inteligencia Artificial Edge-to-Cloud para Raspberry Pi 5**

![Estado: Operativo y Estable](https://img.shields.io/badge/Estado-Operativo_y_Estable-success?style=for-the-badge) 
![Plataforma: RPi 5](https://img.shields.io/badge/Plataforma-Raspberry_Pi_5_(8GB)-red?style=for-the-badge)
![Usuario: Jean-Paul](https://img.shields.io/badge/Preparado_para-Jean--Paul-blue?style=for-the-badge)
![Fecha](https://img.shields.io/badge/Fecha-6_de_febrero_2026-lightgrey?style=for-the-badge)

---

## 1. 🏗️ Arquitectura del Sistema
El proyecto se basa en una arquitectura **Edge-to-Cloud**. La Raspberry Pi actúa como el nodo de interfaz (captura y reproducción), mientras que el procesamiento pesado se delega a un servidor local de alta potencia.

### 🧩 Componentes de Software:
* **Transcripción (STT):** Whisper API (Puerto `8000`) – Convierte audio en texto con alta precisión.
* **Cerebro (LLM):** DeepSeek-R1:7b vía Ollama (Puerto `11435`) – Modelo de razonamiento avanzado.
* **Sintetizador (TTS):** Servidor de síntesis de voz (Puerto `7000`) – Genera archivos WAV a partir de texto.
* **Controlador (Python 3.13):** Script `asistente_vFinal.py` que orquesta todo el flujo.

---

## 2. 🔊 Configuración de Hardware de Audio
El manejo de audio en Linux (**ALSA**) fue el desafío principal debido a la presencia de múltiples tarjetas de sonido USB.

### 🎛️ Inventario de Dispositivos:
| Dispositivo | Marca/Modelo | Rol | Tarjeta (Card ID) |
| :--- | :--- | :--- | :--- |
| **Microphone** | USB PnP Sound Device | Captura de voz | `card 2` |
| **Output** | Ugreen USB Audio | Salida de audio | `card 3` |

### 🔄 Flujo de Datos de Audio:
* **Captura:** Mono, 44100Hz, 16-bit (`S16_LE`).
* **Procesamiento:** Conversión a MP3/WAV para transmisión HTTP.
* **Salida:** Conversión forzada de **Mono a Estéreo** (necesaria para que el hardware Ugreen acepte el stream de datos).

---

## 3. 🛠️ Desafíos Técnicos y Soluciones de Ingeniería

### A. Parche de Compatibilidad Python 3.13 (Mocking)
Python 3.13 eliminó el módulo `audioop`. Para evitar el error `ModuleNotFoundError`, implementamos un **"Mock" (simulación)** que replica las funciones matemáticas necesarias para:
* Calcular el volumen (**RMS**).
* Duplicación de canales (**Stereo**).

### B. Gestión de Fallos de Segmentación (Segfault)
Se detectó que la librería **PyAudio** colapsaba al intentar abrir dispositivos de audio inexistentes (como JACK o OSS).
* **Solución:** Implementamos un manejador de errores en **C** (`snd_lib_error_set_handler`) que silencia las advertencias de ALSA, evitando que desborden el buffer de memoria.

### C. Optimización de Tiempos de Respuesta (Timeouts)
Debido a que DeepSeek-R1 realiza pasos de "pensamiento" interno (`<think>`), se ajustó el timeout de las peticiones HTTP a **120 segundos** para evitar cortes prematuros.

---

## 4. ⌨️ Comandos Críticos de Terminal

### 🔧 Mantenimiento de Audio
```bash
# Listar dispositivos de salida
aplay -l

# Listar dispositivos de grabación
arecord -l

# Liberar el hardware de audio si se queda bloqueado
sudo fuser -k /dev/snd/*

# Crear entorno
python -m venv venv
# Activar entorno
source venv/bin/activate
# Instalar dependencias
pip install pyaudio pydub requests

🚀 5. El Script Maestro (Resumen Lógico)
El código final integra todas las soluciones mencionadas. Aquí el flujo lógico detallado:

Inicio: Limpieza inicial mediante procesos fuser y silenciamiento de logs de ALSA.

Bucle principal (while True):

Grabar: Abre MIC_CARD 2, monitorea el flujo y espera a que el volumen supere el THRESHOLD establecido.

Procesar: Envía el stream de datos hacia Whisper ➡️ DeepSeek ➡️ TTS.

Filtro Neuronal: Remueve las etiquetas <think> del flujo de texto para que la IA no "lea" sus pensamientos internos durante la síntesis.

Reproducir: Exporta el resultado a estéreo y ejecuta la salida física mediante aplay -D plughw:3,0.

Limpiar: Borra automáticamente los archivos temporales (input.wav, res.wav) para proteger el almacenamiento y la vida útil de la SD.

💡 6. Mejores Prácticas para el Futuro
Aislamiento de Hardware: No desconectar los USB mientras el script corre; ALSA reasigna los IDs (card 2, card 3) y el script fallaría.

Calibración de Sensibilidad:

Ambiente ruidoso: Subir el THRESHOLD a 300.

Ambiente silencioso: Bajar el THRESHOLD a 150.

Persistencia: Para que el script corra siempre de forma autónoma, se recomienda crear un servicio en systemd.

Desarrollado por: Jean-Paul

Estado del Proyecto: Operativo y Estable