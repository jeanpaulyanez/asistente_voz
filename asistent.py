import sys
import struct
import types
import pyaudio
import wave
import os
import requests
import json
import time
from ctypes import *

# --- TRUCO PARA SILENCIAR ERRORES DE ALSA EN TERMINAL ---
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
asound = cdll.LoadLibrary('libasound.so.2')
asound.snd_lib_error_set_handler(c_error_handler)

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

# --- CONFIGURACIÓN ---
MIC_CARD = 2
SPK_CARD = 3
URL_TRANSCRIBE = "http://192.168.100.25:8000/transcribe/"
URL_OLLAMA = "http://192.168.100.25:11435/api/generate"
URL_SYNTHESIZE = "http://192.168.100.25:7000/synthesize/"

THRESHOLD = 200 
SILENCE_LIMIT = 2
BASE_DIR = "/home/jeanpaul/proyecto_grabador_voz"

def grabar_usuario():
    p = pyaudio.PyAudio()
    mic_idx = None
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if f"hw:{MIC_CARD}" in dev['name'] or "USB PnP" in dev['name']:
            mic_idx = i
            break

    if mic_idx is None: return None

    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,
                    input=True, input_device_index=mic_idx,
                    frames_per_buffer=1024)

    print(f"\n👂 ESCUCHANDO...")
    frames = []
    recording = False
    silent_chunks = 0

    while True:
        data = stream.read(1024, exception_on_overflow=False)
        vol = rms(data, 2)
        if vol > THRESHOLD:
            if not recording:
                print("🔴 Grabando..."); recording = True
            frames.append(data); silent_chunks = 0
        elif recording:
            frames.append(data); silent_chunks += 1
            if silent_chunks > int(SILENCE_LIMIT * 44100 / 1024):
                print("⏹️ Procesando..."); break

    stream.stop_stream(); stream.close(); p.terminate()
    
    if frames:
        path = os.path.join(BASE_DIR, "v1.mp3")
        temp_wav = os.path.join(BASE_DIR, "temp.wav")
        with wave.open(temp_wav, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(44100)
            wf.writeframes(b''.join(frames))
        AudioSegment.from_wav(temp_wav).export(path, format="mp3")
        os.remove(temp_wav)
        return path
    return None

def proceso():
    audio = grabar_usuario()
    if not audio: return

    try:
        # 1. Transcribir
        r = requests.post(URL_TRANSCRIBE, files={'file': ('v1.mp3', open(audio, 'rb'), 'audio/mpeg')}, timeout=20)
        texto = r.json().get('text') or r.json().get('transcription') or ""
        if not texto.strip(): return
        print(f"👤 Tú: {texto}")

        # 2. IA - Aumentamos timeout a 90 para DeepSeek
        print("🧠 DeepSeek pensando...")
        r = requests.post(URL_OLLAMA, json={"model": "deepseek-r1:7b", "prompt": texto, "stream": False}, timeout=90)
        texto_ia = r.json().get('response', '')
        if "<think>" in texto_ia: texto_ia = texto_ia.split("</think>")[-1].strip()
        print(f"🤖 IA: {texto_ia}")

        # 3. Voz
        r = requests.post(URL_SYNTHESIZE, json={"text": texto_ia}, timeout=30)
        wav_res = os.path.join(BASE_DIR, "res.wav")
        with open(wav_res, 'wb') as f: f.write(r.content)

        # 4. Reproducir
        stereo = os.path.join(BASE_DIR, "stereo.wav")
        AudioSegment.from_wav(wav_res).set_channels(2).export(stereo, format="wav")
        os.system(f'aplay -D plughw:{SPK_CARD},0 "{stereo}" > /dev/null 2>&1')

        # Limpiar
        for f in [audio, wav_res, stereo]:
            if os.path.exists(f): os.remove(f)

    except Exception as e:
        print(f"⚠️ Reintentando... (Error: {e})")

if __name__ == "__main__":
    os.system("sudo fuser -k /dev/snd/* > /dev/null 2>&1")
    print("🚀 Asistente Iniciado. Control+C para salir.")
    try:
        while True:
            proceso()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nBye!")
