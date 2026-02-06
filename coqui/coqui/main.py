from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from TTS.api import TTS
import io
import soundfile as sf

app = FastAPI()

# Carga un modelo TTS pre-entrenado (ajusta el modelo si quieres)
#tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)
#tts = TTS(model_name="tts_models/es/mai/tacotron2-DDC", progress_bar=False, gpu=False)
tts = TTS(model_name="tts_models/es/css10/vits", progress_bar=False, gpu=False)
class TextToSpeechRequest(BaseModel):
    text: str

@app.post("/synthesize/", response_class=StreamingResponse)
async def synthesize(req: TextToSpeechRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Texto vacío")

    # Sintetiza el audio
    wav = tts.tts(text)

    # Convertir numpy array a wav en memoria
    buffer = io.BytesIO()
    sf.write(buffer, wav, tts.synthesizer.output_sample_rate, format="WAV")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="audio/wav")
