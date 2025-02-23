const { compilar } = require('../../main/python-handler');

document.getElementById('compilar-btn').addEventListener('click', () => {
    const codigo = document.getElementById('editor').value;
    compilar(codigo, (resultado) => {
        document.getElementById('output').textContent = resultado;
    });
});