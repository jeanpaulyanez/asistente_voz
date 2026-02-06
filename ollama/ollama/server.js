// server.js - Código Express (Ya compatible con Docker)
import express from 'express';
import ollama from 'ollama'; 
import { performance } from 'perf_hooks'; 

const app = express();

// --- CONFIGURACIÓN DE HOSTS USANDO VARIABLES DE ENTORNO ---
const PUERTO = process.env.PORT || 3000;
const HOST_OLLAMA = process.env.OLLAMA_HOST_INTERNAL || 'http://localhost:11434'; 
const NOMBRE_MODELO = 'deepseek-r1:1.5b'; 

app.use(express.json());

app.post('/generar-texto', async (req, res) => {
    const { prompt } = req.body;

    if (!prompt) {
        return res.status(400).json({ error: 'Falta el campo "prompt" en el cuerpo de la solicitud.' });
    }

    console.log(`\n--- Nueva Solicitud Recibida ---`);
    console.log(`[${new Date().toLocaleTimeString('es-CL')}] Prompt: ${prompt.substring(0, 50)}...`);

    const promptOptimizado = `[INSTRUCCIÓN CLAVE: Responde de forma concisa y directa, sin preámbulos. Responde SIEMPRE en español.] Pregunta del usuario: ${prompt}`;
    
    const tiempoInicio = performance.now();

    res.setHeader('Content-Type', 'text/plain; charset=utf-8'); 
    res.setHeader('Transfer-Encoding', 'chunked');
    res.status(200);

    try {
        const streamRespuesta = await ollama.generate({
            model: NOMBRE_MODELO,
            prompt: promptOptimizado,
            stream: true, 
            host: HOST_OLLAMA, // Usa el nombre de servicio de Docker Compose
            options: { mirostat: 1, stop: ["<|im_start|>", "<|im_end|>"] }
        });

        for await (const chunk of streamRespuesta) {
            res.write(chunk.response);
        }

        const tiempoFin = performance.now();
        const duracion = (tiempoFin - tiempoInicio).toFixed(2);
        
        const reporteTiempo = `\n\n--- LATENCIA TOTAL: ${duracion} ms ---`;
        res.write(reporteTiempo);
        
        res.end();
        console.log(`[${new Date().toLocaleTimeString('es-CL')}] Respuesta completa enviada. Latencia: ${duracion} ms.`);

    } catch (error) {
        console.error(`Error en la comunicación con Ollama:`, error.message);
        
        if (!res.headersSent) {
            res.status(500).end(`\nERROR al conectar con Ollama: ${error.message}. Verifique el servicio 'ollama' en Docker Compose.`);
        } else {
            res.end(); 
        }
    }
});

// Escucha en '0.0.0.0' (obligatorio dentro de un contenedor)
app.listen(PUERTO, '0.0.0.0', () => { 
    console.log(`\n🚀 Servidor Express (SOLO TEXTO) escuchando en http://0.0.0.0:${PUERTO}`);
    console.log(`   - Modelo: ${NOMBRE_MODELO}`);
    console.log(`   - Ollama Host Interno: ${HOST_OLLAMA}`);
});
