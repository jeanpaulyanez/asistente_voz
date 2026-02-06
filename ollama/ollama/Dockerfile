# Dockerfile para la aplicación Express
FROM node:18-slim

WORKDIR /app

# Copia los archivos de configuración
COPY package*.json ./

# Instala las dependencias
RUN npm install

# Copia el código principal
COPY server.js .

# El puerto interno de Express
EXPOSE 3000

CMD ["node", "server.js"]
