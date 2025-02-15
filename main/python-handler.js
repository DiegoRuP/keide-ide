const { exec } = require('child_process');
const path = require('path');

function compilar(codigo, callback) {
    const compiladorPath = path.join(__dirname, '../compiler/compilador.py');
    const proceso = exec(`python ${compiladorPath}`, (error, stdout, stderr) => {
        if (error) {
            callback(`Error: ${stderr}`);
        } else {
            callback(stdout);
        }
    });

    proceso.stdin.write(codigo);
    proceso.stdin.end();
}

module.exports = compilar;