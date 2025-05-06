document.addEventListener('DOMContentLoaded', () => {
    const checkDependencies = setInterval(() => {
        if (window.editor && window.compilerAPI) {
            clearInterval(checkDependencies);
            setupCompiler();
        } else {
            console.log('Esperando dependencias...', {
                editor: !!window.editor, 
                compilerAPI: !!window.compilerAPI
            });
        }
    }, 100);
});

function setupCompiler() {
    const compileBtn = document.getElementById('compilar-btn');
    if (!compileBtn) {
        console.error('Botón de compilación no encontrado');
        return;
    }

    let isCompiling = false;

    compileBtn.addEventListener('click', async () => {
        if (isCompiling) {
            console.warn('Compilación en curso, ignorando click');
            return;
        }

        isCompiling = true;
        const code = window.editor.getValue();
        const loadingElement = document.getElementById('loading-indicator');
        const lexicoOutput = document.getElementById('output-lexicos');
        const resultadosOutput = document.getElementById('output-resultados');
        
        if (!code.trim()) {
            lexicoOutput.textContent = "Error: El editor está vacío";
            isCompiling = false;
            return;
        }

        loadingElement.style.display = 'block';
        lexicoOutput.textContent = "Compilando...";
        console.log('Iniciando compilación...');
        
        try {
            const result = await window.compilerAPI.compile(code);
            console.log('Resultado compilación:', result);

            if(window.colorearEditorConTokens){
                window.colorearEditorConTokens(result.tokens);
            }
            
            if (result.error) {
                throw new Error(result.error);
            }
        
            // Mostrar tokens
            if (result.tokens) {
                document.getElementById('lexico').innerHTML = result.tokens.map(token => `
                    <div class="token">
                        <span class="token-type">${token.type}</span>
                        <span class="token-value">${token.value}</span>
                        <span class="token-position">Línea ${token.line}, Col ${token.column}</span>
                    </div>
                `).join('');
                
                
                if(window.colorearEditorConTokens){
                    window.colorearEditorConTokens(result.tokens);
                }
        
            }
            
            // Mostrar errores
            lexicoOutput.textContent = result.errores?.join('\n') || "No se encontraron errores léxicos";
            
            // Mostrar código coloreado
            if (result.html_coloreado) {
                resultadosOutput.innerHTML = result.html_coloreado;
            }
        
        } catch (error) {
            console.error('Error en compilación:', error);
            lexicoOutput.textContent = `Error: ${error.message}`;
        } finally {
            loadingElement.style.display = 'none';
            isCompiling = false;
            console.log('Compilación finalizada');
        }
    });
}