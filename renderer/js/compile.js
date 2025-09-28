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
        const semanticoOutput = document.getElementById('output-semanticos');
        const resultadosOutput = document.getElementById('output-resultados');
        const panelTokens = document.getElementById('lexico'); // El panel de la lista de tokens
        const panelAST = document.getElementById('sintactico'); // El panel del AST
        
        if (!code.trim()) {
            lexicoOutput.textContent = "Error: El editor está vacío";
            isCompiling = false;
            return;
        }

        loadingElement.style.display = 'block';
        // Limpiar paneles
        lexicoOutput.innerHTML = "Compilando...";
        sintacticoOutput.innerHTML = "Analizando sintaxis...";
        semanticoOutput.innerHTML = "Analizando semántica...";
        resultadosOutput.innerHTML = "Procesando...";
        
        try {
          const result = await window.compilerAPI.compile(code);
          console.log("Resultado compilación:", result);

          if (window.colorearEditorConTokens) {
              window.colorearEditorConTokens(result.tokens);
          }

          if (result.error) {
              throw new Error(result.error);
          }

          if (result.tokens) {
              const tokensParaPanel = result.tokens.filter(
                  (token) => !["WHITESPACE", "COMMENT", "ERROR", "UNCLOSED_COMMENT", "UNCLOSED_STRING"].includes(token.type)
              );
              panelTokens.innerHTML = tokensParaPanel.map(
                  (token) => `
                      <div class="token">
                          <span class="token-type">${token.type}</span>
                          <span class="token-value">${token.value}</span>
                          <span class="token-position">Línea ${token.line}, Col ${token.column}</span>
                      </div>
                  `
              ).join("");
          }
          
          // Mostrar AST en el panel sintáctico
          if (result.ast_html) {
              panelAST.innerHTML = `<div class="ast-container">${result.ast_html}</div>`;

              document.querySelectorAll(".ast-label").forEach((label) => {
                  label.addEventListener("click", function (e) {
                      e.stopPropagation();
                      const parent = label.parentElement;
                      if (parent.classList.contains("ast-node")) {
                          parent.classList.toggle("collapsed");
                      }
                  });
              });
          } else if (result.errores_lexicos?.length > 0) {
              panelAST.innerHTML = `<div class="info-message">No se generó el AST por errores en el análisis léxico.</div>`;
          } else {
              panelAST.innerHTML = `<div class="info-message">No se generó el árbol sintáctico.</div>`;
          }

        // Mostrar errores léxicos
          lexicoOutput.innerHTML = result.errores_lexicos?.length
              ? result.errores_lexicos.map(e => `<div class="error-item">${e}</div>`).join('')
              : '<div class="success-message">✓ No se encontraron errores léxicos</div>';

          // Mostrar errores sintácticos
          sintacticoOutput.innerHTML = result.errores_sintacticos?.length
              ? result.errores_sintacticos.map(e => `<div class="error-item">${e}</div>`).join('')
              : '<div class="success-message">✓ No se encontraron errores sintácticos</div>';

          // Mostrar errores semánticos
          const semanticoErrorsExist = result.errores_lexicos?.length || result.errores_sintacticos?.length;
          semanticoOutput.innerHTML = result.errores_semanticos?.length
              ? result.errores_semanticos.map(e => `<div class="error-item">${e}</div>`).join('')
              : (semanticoErrorsExist 
                  ? '<div class="info-message">El análisis no se ejecutó debido a errores previos.</div>'
                  : '<div class="success-message">✓ No se encontraron errores semánticos</div>');
          
          // Mostrar resumen en Resultados
          const totalErrores = (result.errores_lexicos?.length || 0) + (result.errores_sintacticos?.length || 0) + (result.errores_semanticos?.length || 0);
          if (totalErrores > 0) {
            resultadosOutput.innerHTML = `<div class="warning-message">Compilación completada con ${totalErrores} error(es).</div>`;
          } else {
            resultadosOutput.innerHTML = '<div class="success-message">¡Compilación exitosa! Análisis completados sin errores.</div>';
          }

        } catch (error) {
            console.error('Error en compilación:', error);
            const errorMessage = `Error: ${error.message}`;
            lexicoOutput.innerHTML = `<div class="error-item">${errorMessage}</div>`;
            sintacticoOutput.innerHTML = `<div class="error-item">${errorMessage}</div>`;
            semanticoOutput.innerHTML = `<div class="error-item">${errorMessage}</div>`;
            resultadosOutput.innerHTML = `<div class="error-item">Error durante la compilación: ${error.message}</div>`;
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