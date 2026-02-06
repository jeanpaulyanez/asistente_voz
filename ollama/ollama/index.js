import ollama from 'ollama';

const host = 'http://0.0.0.0:11434';
const modelName = 'deepseek-r1:7b';

async function interactuarConOllama() {
    try {
        console.log(`Enviando solicitud a ${modelName}... (Usando streaming)`);
        
        // ** CAMBIO CLAVE: Usar stream: true **
        const responseStream = await ollama.generate({
            model: modelName,
            prompt: 'dime cual es la mejor empresa de chile? en español',
            stream: true, // Ahora esperamos un stream de datos
            host: host
        });

        process.stdout.write('Respuesta de DeepSeek-R1:\n----------------------------\n');

        // Procesar y mostrar el stream de datos
        for await (const chunk of responseStream) {
            process.stdout.write(chunk.response); // Escribir cada token inmediatamente
        }
        
        process.stdout.write('\n----------------------------\n');

    } catch (error) {
        console.error('❌ Error al interactuar con Ollama. Verifica la conexión y los recursos:', error.message);
    }
}

interactuarConOllama();
