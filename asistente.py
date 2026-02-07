import sys
import struct
import types
import pyaudio
import wave
import os
import requests
import json
import time

# --- PARCHE DE COMPATIBILIDAD PYTHON 3.13 ---
m = types.ModuleType("audioop")
def rms(data, width):
    if width != 2: return 0
    count = len(data) / 2
    shorts = struct.unpack("%dh" % count, data)
    sum_squares = sum((s/32768.0)**2 for s in shorts)
    return int(((sum_squares / count) ** 0.5) * 10000)
def tostereo(data, width, fac1, fac2):
    if width != 2: return data
    out = bytearray()
    for i in range(0, len(data), 2):
        sample = data[i:i+2]
        out.extend(sample); out.extend(sample)
    return bytes(out)
def mul(data, width, factor): return data
m.rms = rms; m.tostereo = tostereo; m.mul = mul
sys.modules["audioop"] = m
# ---------------------------------------------

from pydub import AudioSegment

# --- CONFIGURACIÓN DE HARDWARE ---
MIC_CARD = 2      # USB PnP (Micro)
SPK_CARD = 3      # Ugreen (Salida)

URL_TRANSCRIBE = "http://192.168.100.25:8000/transcribe/"
URL_OLLAMA = "http://192.168.100.25:11435/api/generate"
URL_SYNTHESIZE = "http://192.168.100.25:7000/synthesize/"

THRESHOLD = 200 
SILENCE_LIMIT = 2

BASE_DIR = "/home/jeanpaul/proyecto_grabador_voz"
MP3_USER = os.path.join(BASE_DIR, "v1.mp3")
WAV_RESPONSE = os.path.join(BASE_DIR, "respuesta_ia.wav")
WAV_STEREO = os.path.join(BASE_DIR, "respuesta_stereo.wav")

def grabar_usuario():
    p = pyaudio.PyAudio()
    mic_idx = None
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if f"hw:{MIC_CARD}" in dev['name'] or "USB PnP" in dev['name']:
            mic_idx = i
            break

    if mic_idx is None:
        print(f"❌ No se encontró el micro en Card {MIC_CARD}"); return None

    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,
                        input=True, input_device_index=mic_idx,
                        frames_per_buffer=1024)
    except Exception as e:
        print(f"❌ Error micro: {e}"); return None

    print(f"\n--- LISTO PARA ESCUCHAR (Card {MIC_CARD}) ---")
    frames = []
    recording = False
    silent_chunks = 0

    while True:
        try:
            data = stream.read(1024, exception_on_overflow=False)
            vol = rms(data, 2)
            if vol > THRESHOLD:
                if not recording:
                    print("🔴 Grabando..."); recording = True
                frames.append(data); silent_chunks = 0
            elif recording:
                frames.append(data); silent_chunks += 1
                if silent_chunks > int(SILENCE_LIMIT * 44100 / 1024):
                    print("⏹️ Fin de captura."); break
        except Exception: break

    stream.stop_stream(); stream.close(); p.terminate()
    
    if frames:
        temp_wav = os.path.join(BASE_DIR, "temp_u.wav")
        with wave.open(temp_wav, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(44100)
            wf.writeframes(b''.join(frames))
        AudioSegment.from_wav(temp_wav).export(MP3_USER, format="mp3")
        os.remove(temp_wav)
        return MP3_USER
    return None

def proceso_asistente():
    archivo_audio = grabar_usuario()
    if not archivo_audio: return

    try:
        # 1. Transcribir
        print("☁️ Transcribiendo...")
        with open(archivo_audio, 'rb') as f:
            r = requests.post(URL_TRANSCRIBE, files={'file': ('v1.mp3', f, 'audio/mpeg')}, timeout=15)
        texto = r.json().get('text', '') or r.json().get('transcription', '')
        
        if not texto.strip():
            print("👤 Tú: (Silencio)"); return
            
        print(f"👤 Tú: {texto}")

        # 2. IA
        print("🧠 DeepSeek...")
        r = requests.post(URL_OLLAMA, json={"model": "deepseek-r1:7b", "prompt": texto, "stream": False}, timeout=30)
        texto_ia = r.json().get('response', '')
        if "<think>" in texto_ia: texto_ia = texto_ia.split("</think>")[-1].strip()
        print(f"🤖 IA: {texto_ia}")

        # 3. Voz
        print("🗣️ Sintetizando...")
        r = requests.post(URL_SYNTHESIZE, json={"text": texto_ia}, timeout=20)
        with open(WAV_RESPONSE, 'wb') as f: f.write(r.content)

        # 4. Reproducir
        if os.path.exists(WAV_RESPONSE):
            audio = AudioSegment.from_wav(WAV_RESPONSE)
            audio.set_channels(2).export(WAV_STEREO, format="wav")
            time.sleep(0.3)
            print(f"🔊 Reproduciendo por Card {SPK_CARD}...")
            os.system(f'aplay -D plughw:{SPK_CARD},0 "{WAV_STEREO}"')

        # Limpiar archivos de este turno
        for f in [archivo_audio, WAV_RESPONSE, WAV_STEREO]:
            if os.path.exists(f): os.remove(f)

    except Exception as e:
        print(f"❌ Error en este ciclo: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando Asistente de Voz Infinito...")
    # Limpieza inicial de audio
    os.system("sudo fuser -k /dev/snd/* > /dev/null 2>&1")
    
    try:
        while True:
            proceso_asistente()
            print("\n" + "="*30)
            time.sleep(1) # Pausa para evitar bucles locos o ecos
    except KeyboardInterrupt:
        print("\n👋 Asistente detenido por el usuario.")
