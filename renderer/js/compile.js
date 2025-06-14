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
        const sintacticoOutput = document.getElementById('output-sintacticos');
        const resultadosOutput = document.getElementById('output-resultados');
        
        if (!code.trim()) {
            lexicoOutput.textContent = "Error: El editor está vacío";
            isCompiling = false;
            return;
        }

        loadingElement.style.display = 'block';
        lexicoOutput.textContent = "Compilando...";
        sintacticoOutput.textContent = "Analizando sintaxis...";
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
        
            // Mostrar tokens en el panel léxico
            if (result.tokens) {
                const tokensParaPanel = result.tokens.filter(token => 
                    !['ERROR', 'UNCLOSED_COMMENT', 'UNCLOSED_STRING', 'COMMENT'].includes(token.type)
                );
                
                document.getElementById('lexico').innerHTML = tokensParaPanel.map(token => `
                    <div class="token">
                        <span class="token-type">${token.type}</span>
                        <span class="token-value">${token.value}</span>
                        <span class="token-position">Línea ${token.line}, Col ${token.column}</span>
                    </div>
                `).join('');
            }
            
            // Mostrar AST en el panel sintáctico
            // Mostrar AST en el panel sintáctico
if (result.ast || result.ast_html) {
    let astContent = '';
    
    // Si hay AST, mostrarlo siempre
    if (result.ast_html) {
        astContent = `
            <div class="ast-container">
                ${result.ast_html}
            </div>
        `;
    } else if (result.ast) {
        astContent = `
            <div class="ast-container">
                ${formatASTNode(result.ast)}
            </div>
        `;
    }
    
    // Si hay errores, agregar un mensaje al principio
    if (result.errores_sintacticos && result.errores_sintacticos.length > 0) {
        document.getElementById('sintactico').innerHTML = `
            <div class="ast-section">
                <h6>Árbol Sintáctico Parcial:</h6>
                ${astContent}
            </div>
        `;
    } else {
        // Sin errores, mostrar solo el AST
        document.getElementById('sintactico').innerHTML = `
            <div class="ast-section">
                <h6>Árbol Sintáctico Abstracto:</h6>
                ${astContent}
            </div>
        `;
    }
    } else if (result.errores_lexicos && result.errores_lexicos.length > 0) {
        // No hay AST debido a errores léxicos
        document.getElementById('sintactico').innerHTML = `
            <div class="info-message">
                <i class="fas fa-info-circle"></i>
                No se pudo generar el AST debido a errores léxicos.
            </div>
        `;
    } else {
        // No hay AST por alguna otra razón
        document.getElementById('sintactico').innerHTML = `
            <div class="info-message">
                <i class="fas fa-info-circle"></i>
                No se generó árbol sintáctico.
            </div>
        `;
    }
            
            // Mostrar errores léxicos
            lexicoOutput.textContent = result.errores_lexicos?.join('\n') || "No se encontraron errores léxicos";
            
            // Mostrar errores sintácticos
            if (result.errores_sintacticos && result.errores_sintacticos.length > 0) {
                sintacticoOutput.innerHTML = result.errores_sintacticos.map(error => {
                    return `<div class="error-item">${error}</div>`;
                }).join('');
            } else {
                sintacticoOutput.innerHTML = '<div style="color: green; padding: 10px;">✓ No se encontraron errores sintácticos</div>';
            }
            
            // Mostrar resultado general
            if (!result.errores_lexicos?.length && !result.errores_sintacticos?.length) {
                resultadosOutput.textContent = "Compilación exitosa: Análisis léxico y sintáctico completados sin errores";
            } else {
                const totalErrores = (result.errores_lexicos?.length || 0) + (result.errores_sintacticos?.length || 0);
                resultadosOutput.textContent = `Compilación completada con ${totalErrores} error(es)`;
            }
        
        } catch (error) {
            console.error('Error en compilación:', error);
            lexicoOutput.textContent = `Error: ${error.message}`;
            sintacticoOutput.textContent = `Error: ${error.message}`;
            resultadosOutput.textContent = `Error durante la compilación: ${error.message}`;
        } finally {
            loadingElement.style.display = 'none';
            isCompiling = false;
            console.log('Compilación finalizada');
        }
    });
}

// Función auxiliar para formatear el AST si no viene el HTML
function formatASTNode(node, indent = 0) {
    if (!node) return '';
    
    let html = '<div class="ast-node" style="margin-left: ' + (indent * 20) + 'px;">';
    html += `<span class="node-type">${node.type}</span>`;
    
    if (node.value) {
        html += ` <span class="node-value">[${node.value}]</span>`;
    }
    
    if (node.line) {
        html += ` <span class="node-position">(línea ${node.line})</span>`;
    }
    
    html += '</div>';
    
    if (node.children && node.children.length > 0) {
        for (const child of node.children) {
            if (child) {
                html += formatASTNode(child, indent + 1);
            }
        }
    }
    
    return html;
}