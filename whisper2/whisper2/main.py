import os
import shutil
import whisper
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="Whisper Transcription API",
    description="Recibe un MP3 y devuelve la transcripción usando OpenAI Whisper."
)

# Cargar el modelo de Whisper al inicio (solo una vez)
# Usaremos 'base' para ser rápidos; puedes cambiar a 'small', 'medium', etc.
try:
    print("🧠 Cargando modelo Whisper (base)... Esto puede tardar la primera vez.")
    MODEL = whisper.load_model("base")
    print("✅ Modelo Whisper cargado exitosamente.")
except Exception as e:
    print(f"❌ Error al cargar el modelo Whisper: {e}")
    # En un entorno real, querrías que el contenedor fallara si el modelo no carga.

# Esquema de respuesta para la API
class TranscriptionResponse(BaseModel):
    filename: str
    transcription: str
    model_used: str

@app.get("/")
def read_root():
    """Endpoint de bienvenida."""
    return {"message": "Whisper API está en funcionamiento. Usa el endpoint /transcribe/ para enviar un MP3."}

@app.post("/transcribe/", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(..., description="Archivo MP3 con audio para transcribir.")):
    """Recibe un archivo MP3, lo transcribe con Whisper y retorna el texto."""
    
    # 1. Validación básica del archivo
    if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos MP3, WAV o M4A.")
    
    # Crea un nombre de archivo temporal
    temp_file_path = f"/tmp/{file.filename}"
    
    # 2. Guardar el archivo cargado localmente
    try:
        with open(temp_file_path, "wb") as buffer:
            # shutil.copyfileobj es eficiente para manejar archivos grandes
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {e}")

    # 3. Transcripción con Whisper
    transcription_text = ""
    try:
        print(f"📝 Transcribiendo archivo: {file.filename}")
        # Transcripción (fp16=False recomendado para CPU)
        result = MODEL.transcribe(temp_file_path, fp16=False)
        transcription_text = result["text"]
        print("✅ Transcripción exitosa.")
        
    except Exception as e:
        print(f"❌ Error durante la transcripción: {e}")
        raise HTTPException(status_code=500, detail=f"Error de transcripción de Whisper: {e}")
    finally:
        # 4. Limpieza: Eliminar el archivo temporal
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # 5. Devolver la respuesta
    return TranscriptionResponse(
        filename=file.filename,
        transcription=transcription_text.strip(),
        model_used="base"
    )

# Para ejecutar la API con Uvicorn (servidor ASGI)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)