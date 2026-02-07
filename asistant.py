import sys
import os
import time
import pyaudio
import wave
import requests
m6import struct

# --- PARCHE SIMPLE PARA AUDIOOP ---
# Evitamos usar 'types.ModuleType' que puede causar Segfault en Python 3.13
class MockAudioop:
    @staticmethod
    def rms(data, width):
        if not data: return 0
        count = len(data) // 2
        shorts = struct.unpack(f"{count}h", data)
        sum_squares = sum((s/32768.0)**2 for s in shorts)
        return int(((sum_squares / count) ** 0.5) * 10000)
sys.modules["audioop"] = MockAudioop

from pydub import AudioSegment

# --- CONFIGURACIÓN ---
MIC_CARD = 2
SPK_CARD = 3
IP = "192.168.100.25"
THRESHOLD = 250
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def grabar():
    p = pyaudio.PyAudio()
    mic_idx = None
    # Detectar el micro de la Card 2
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if f"hw:{MIC_CARD}" in dev['name'] or "USB PnP" in dev['name']:
            mic_idx = i
            break
    
    if mic_idx is None:
        p.terminate()
        return None

    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,
                        input=True, input_device_index=mic_idx, frames_per_buffer=1024)
    except:
        p.terminate()
        return None

    print("\n👂 ESCUCHANDO...")
    frames = []
    recording = False
    silence = 0

    while True:
        try:
            data = stream.read(1024, exception_on_overflow=False)
            vol = MockAudioop.rms(data, 2)
            if vol > THRESHOLD:
                if not recording: 
                    print("🔴 Grabando...")
                    recording = True
                frames.append(data)
                silence = 0
            elif recording:
                frames.append(data)
                silence += 1
                if silence > 60: break # ~1.5 seg de silencio
        except: break

    stream.stop_stream()
    stream.close()
    p.terminate()

    if frames:
        wav_path = os.path.join(BASE_DIR, "input.wav")
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(44100)
            wf.writeframes(b''.join(frames))
        return wav_path
    return None

def proceso():
    wav_in = grabar()
    if not wav_in: return

    try:
        # 1. Transcribir (Enviamos WAV directo para evitar conversiones pesadas)
        print("☁️ Transcribiendo...")
        with open(wav_in, 'rb') as f:
            r = requests.post(f"http://{IP}:8000/transcribe/", files={'file': f}, timeout=20)
        txt = r.json().get('text') or r.json().get('transcription') or ""
        if not txt.strip(): return
        print(f"👤 Tú: {txt}")

        # 2. IA
        print("🧠 DeepSeek...")
        r = requests.post(f"http://{IP}:11435/api/generate", 
                          json={"model": "deepseek-r1:7b", "prompt": txt, "stream": False}, timeout=100)
        res = r.json().get('response', '').split("</think>")[-1].strip()
        print(f"🤖 IA: {res}")

        # 3. Voz
        print("🗣️ Generando...")
        r = requests.post(f"http://{IP}:7000/synthesize/", json={"text": res}, timeout=40)
        v_res = os.path.join(BASE_DIR, "res.wav")
        with open(v_res, 'wb') as f: f.write(r.content)

        # 4. Reproducir
        # Convertimos a estéreo solo si es necesario para el Ugreen
        print("🔊 Hablando...")
        v_st = os.path.join(BASE_DIR, "stereo.wav")
        AudioSegment.from_wav(v_res).set_channels(2).export(v_st, format="wav")
        os.system(f'aplay -D plughw:{SPK_CARD},0 "{v_st}" > /dev/null 2>&1')

        # Limpiar
        for f in [wav_in, v_res, v_st]:
            if os.path.exists(f): os.remove(f)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(2)

if __name__ == "__main__":
    print("🚀 ASISTENTE INICIADO (Ctrl+C para salir)")
    try:
        while True:
            proceso()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n¡Adiós!")
