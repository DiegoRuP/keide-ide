const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

function compilar(codigo, runMode, callback) {
    const compiladorPath = path.join(__dirname, '..', '..', 'compiler', 'compilador.py');
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
    const tempFile = path.join(os.tmpdir(), `keide_temp_${Date.now()}.txt`);

    // Escribir archivo temporal
    fs.writeFile(tempFile, codigo, (writeErr) => {
        if (writeErr) {
            console.error('Error al crear archivo temporal:', writeErr);
            return callback({ 
                error: `Error al crear archivo temporal: ${writeErr.message}`
            });
        }

        let comando = `${pythonCommand} "${compiladorPath}" "${tempFile}"`;

        if (runMode) {
            comando += " --run";
        }

        console.log('Ejecutando:', comando);

        // Configurar timeout (10 segundos)
        const timeout = setTimeout(() => {
            proceso.kill();
            callback({ error: "Timeout: El compilador tardó demasiado en responder" });
        }, 10000);

        const proceso = exec(comando, { maxBuffer: 1024 * 1024 * 5 }, (error, stdout, stderr) => {
            clearTimeout(timeout);
            
            // Limpiar archivo temporal
            fs.unlink(tempFile, (unlinkErr) => {
                if (unlinkErr) console.error('Error eliminando temporal:', unlinkErr);
            });

            if (error) {
                console.error('Error ejecución Python:', { error, stderr });
                return callback({ 
                    error: stderr || `Error ejecutando Python: ${error.message}`,
                    raw: stdout 
                });
            }

            try {
                const resultado = stdout ? JSON.parse(stdout) : { error: "No hubo salida del compilador" };
                callback(resultado);
            } catch (parseError) {
                console.error('Error parseando JSON:', { parseError, stdout });
                callback({ 
                    error: `Error parseando salida: ${parseError.message}`,
                    raw: stdout 
                });
            }
        });

        // Manejar cierre inesperado
        proceso.on('close', (code) => {
            if (code !== 0) {
                console.error('Proceso Python cerró con código:', code);
            }
        });
    });
}

module.exports = { compilar };