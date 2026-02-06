import { Ollama } from 'ollama';

// Usamos el host y puerto correctos de tu contenedor rocm
const ollama = new Ollama({ host: 'http://127.0.0.1:11435' });
const modelName = 'deepseek-r1:7b';

async function interactuarConOllama() {
    try {
        console.log(`--- Conectando a ${modelName} ---`);
        
        const responseStream = await ollama.generate({
            model: modelName,
            prompt: '¿Quién eres y cuál es tu especialidad?',
            stream: true,
        });

        console.log('Respuesta recibida:');

        for await (const chunk of responseStream) {
            // El modelo DeepSeek-R1 suele empezar con <think>
            process.stdout.write(chunk.response); 
        }
        
        process.stdout.write('\n--- Fin de la respuesta ---\n');

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

interactuarConOllama();
