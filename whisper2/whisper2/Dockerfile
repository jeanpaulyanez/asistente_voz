# Usa una imagen base con Python
FROM python:3.10-slim

# Instala dependencias del sistema necesarias, incluyendo FFmpeg 
# (crucial para manejar MP3)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Configura el directorio de trabajo
WORKDIR /app

# Copia los archivos de requisitos e instala las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el script principal
COPY main.py .

# Exponer el puerto donde corre Uvicorn (8000)
EXPOSE 8000

# Comando para ejecutar el servidor Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]