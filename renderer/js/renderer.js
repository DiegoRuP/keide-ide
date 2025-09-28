document.addEventListener('DOMContentLoaded', () => {

    const editorElement = document.getElementById('editor');
    if (!editorElement) {
        console.error('Elemento del editor no encontrado');
        return;
    }

    const resizeHandle = document.querySelector('.resize-handle');
    const leftPanel = document.querySelector('.col-md-9');
    const rightPanel = document.querySelector('.col-md-3');
    let isResizing = false;

    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.classList.add('resizing');
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const container = leftPanel.parentElement;
        const containerRect = container.getBoundingClientRect();
        const percent = (e.clientX - containerRect.left) / containerRect.width * 100;
        
        leftPanel.style.width = `calc(${percent}% - 4px)`;
        rightPanel.style.width = `calc(${100 - percent}% - 4px)`;
    });

    document.addEventListener('mouseup', () => {
        isResizing = false;
        document.body.classList.remove('resizing');
    });

    // Resize horizontal para los logs
    const hResizeHandle = document.querySelector('.resize-handle-horizontal');
    const editorAnalysisContainer = document.querySelector('.row.flex-nowrap');
    const logsContainer = document.querySelector('.resize-container-vertical');
    let isHResizing = false;

    hResizeHandle.addEventListener('mousedown', (e) => {
        isHResizing = true;
        document.body.classList.add('resizing-horizontal');
    });

    document.addEventListener('mousemove', (e) => {
        if (!isHResizing) return;
        
        const container = document.querySelector('main');
        const containerRect = container.getBoundingClientRect();
        const newHeight = containerRect.bottom - e.clientY;

        const minHeight = 80; // Altura mínima para los logs
        const maxHeight = containerRect.height - 150; // Altura máxima para los logs
        
        const constrainedHeight = Math.min(Math.max(newHeight, minHeight), maxHeight);

        logsContainer.style.height = `${constrainedHeight}px`;
        editorAnalysisContainer.style.height = `calc(100% - ${constrainedHeight}px)`;
        editor.refresh();
    });

    document.addEventListener('mouseup', () => {
        isHResizing = false;
        document.body.classList.remove('resizing-horizontal');
    });

    // Handle editor resize
    window.addEventListener('resize', () => {
        editor?.refresh();
    });

    // Cambiar entre modo oscuro y claro
    document.getElementById('toggle-dark-mode').addEventListener('click', async () => {
        const isDarkMode = await window.darkMode.toggle();
        document.body.classList.toggle('dark-mode', isDarkMode);
        const icon = document.querySelector('#toggle-dark-mode i');
        icon.classList.toggle('fa-moon', !isDarkMode);
        icon.classList.toggle('fa-sun', isDarkMode);
        setCodeMirrorTheme(isDarkMode); // Cambiar el tema de CodeMirror
    });

    // Activar tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Variables para almacenar la ruta del archivo actual
    let currentFilePath = null;

    // Inicializar CodeMirror
    const editor = CodeMirror(editorElement, {
        lineNumbers: true, // Mostrar números de línea
        mode: "javascript", // Modo de sintaxis (puedes cambiarlo según el lenguaje)
        theme: "default", // Tema inicial (claro)
        lineWrapping: false, // Ajuste de líneas
        indentUnit: 4, // Tabulación de 4 espacios
        tabSize: 4,
        autofocus: true, // Enfocar automáticamente
        scrollbarStyle: "native", // Usar scrollbars nativos
        autorefresh: true, // Refrescar automáticamente
    });

    window.editor = editor; // Exponer el editor a la ventana global

    // Función para cambiar el tema de CodeMirror
    function setCodeMirrorTheme(isDarkMode) {
        if (isDarkMode) {
            editor.setOption("theme", "material-ocean"); // Tema oscuro
        } else {
            editor.setOption("theme", "default"); // Tema claro
        }
    }

    // Exponer también algunas funciones útiles
    window.editorFunctions = {
        getEditorContent: () => editor.getValue(),
        setEditorContent: (content) => editor.setValue(content),
        setTheme: setCodeMirrorTheme
    };

    console.log('Editor de código inicializado y expuesto como window.editor');

    // Función para abrir el archivo
    const setEditorContent = (content) => {
        editor.setValue(content);
    }

    // Botón: Abrir archivo del menú
    document.getElementById('btn-open-menu').addEventListener('click', async () => {
        try {
            const result = await window.fileAPI.openFile();
            if (result) {
                currentFilePath = result.filePath;
                setEditorContent(result.content); // Usar CodeMirror para establecer el contenido
            }
        } catch (error) {
            console.error('Error al abrir el archivo:', error);
        }
    });

    // Botón: Abrir archivo
    document.getElementById('btn-open').addEventListener('click', async () => {
        try {
            const result = await window.fileAPI.openFile();
            if (result) {
                currentFilePath = result.filePath;
                setEditorContent(result.content); // Usar CodeMirror para establecer el contenido
            }
        } catch (error) {
            console.error('Error al abrir el archivo:', error);
        }
    });

    // Botón: Guardar archivo del menú
    document.getElementById('btn-save-menu').addEventListener('click', async () => {
        try {
            const content = window.editorFunctions.getEditorContent(); // Usar CodeMirror para obtener el contenido
            if (!currentFilePath) {
                const newFilePath = await window.fileAPI.saveFile(content);
                if (newFilePath) {
                    currentFilePath = newFilePath;
                }
            } else {
                await window.fileAPI.saveFile(content, currentFilePath);
            }
        } catch (error) {
            console.error('Error al guardar el archivo:', error);
        }
    });

    // Botón: Guardar archivo
    document.getElementById('btn-save').addEventListener('click', async () => {
        try {
            const content = window.editorFunctions.getEditorContent(); // Usar CodeMirror para obtener el contenido
            if (!currentFilePath) {
                const newFilePath = await window.fileAPI.saveFile(content);
                if (newFilePath) {
                    currentFilePath = newFilePath;
                }
            } else {
                await window.fileAPI.saveFile(content, currentFilePath);
            }
        } catch (error) {
            console.error('Error al guardar el archivo:', error);
        }
    });

    // Botón: Guardar como del menú
    document.getElementById('btn-save-as-menu').addEventListener('click', async () => {
        try {
            const content = window.editorFunctions.getEditorContent(); // Usar CodeMirror para obtener el contenido
            const newFilePath = await window.fileAPI.saveFileAs(content);
            if (newFilePath) {
                currentFilePath = newFilePath;
            }
        } catch (error) {
            console.error('Error al guardar como:', error);
        }
    });

    // Botón: Guardar como
    document.getElementById('btn-save-as').addEventListener('click', async () => {
        try {
            const content = window.editorFunctions.getEditorContent(); // Usar CodeMirror para obtener el contenido
            const newFilePath = await window.fileAPI.saveFileAs(content);
            if (newFilePath) {
                currentFilePath = newFilePath;
            }
        } catch (error) {
            console.error('Error al guardar como:', error);
        }
    });

    // Botón: Nuevo archivo
    document.getElementById('btn-blank').addEventListener('click', () => {
        currentFilePath = null;
        setEditorContent('');
    });

    // Botón: Nuevo archivo del menú
    document.getElementById('btn-blank-menu').addEventListener('click', () => {
        currentFilePath = null;
        setEditorContent('');
    });

    //Botón: Cerrar archivo
    document.getElementById('btn-close').addEventListener('click', () => {
        currentFilePath = null;
        setEditorContent('');
    });

    // Botón: Cerrar archivo del menú
    document.getElementById('btn-close-menu').addEventListener('click', () => {
        currentFilePath = null;
        setEditorContent('');
    });

    // Cambiar el tema de CodeMirror al cargar la página
    window.darkMode.toggle().then((isDarkMode) => {
        setCodeMirrorTheme(isDarkMode);
    });

    // Deshacer
    document.getElementById('btn-undo').addEventListener('click', () => {
        editor.undo();
    });

    // Rehacer
    document.getElementById('btn-redo').addEventListener('click', () => {
        editor.redo();
    });

    // Actualizar la posición del cursor y el número de líneas
    editor.on('cursorActivity', () => {
        const cursor = editor.getCursor();
        document.getElementById('cursor-position').textContent = `Línea: ${cursor.line + 1}, Columna: ${cursor.ch + 1}`;
        document.getElementById('line-count').textContent = `Líneas: ${editor.lineCount()}`;
    });


    window.activeMarks = [];

    function colorearEditorConTokens(tokens) {
    // Borra highlights anteriores
    if(window.activeMarks){
        window.activeMarks.forEach(mark => mark.clear());
        window.activeMarks = [];
    }
    
    tokens.forEach(token => {
        // Mapear el tipo de token a clase cm
        let cmClass = 'cm-default';
        switch(token.type) {
            case 'NUMBER':           cmClass = 'cm-color1'; break;
            case 'IDENTIFIER':       cmClass = 'cm-color2'; break;
            case 'COMMENT':          cmClass = 'cm-color3'; break; // Comentarios normales
            case 'UNCLOSED_COMMENT': cmClass = 'cm-color3'; break; // Comentarios sin cerrar (podrías usar un estilo diferente)
            case 'KEYWORD':          cmClass = 'cm-color4'; break;
            case 'ARITHMETIC_OP':
            case 'BITWISE_OP':       cmClass = 'cm-color5'; break;
            case 'RELATIONAL_OP':
            case 'LOGICAL_OP':       cmClass = 'cm-color6'; break;
            case 'ERROR':            cmClass = 'cm-error'; break;
            case 'STRING':           cmClass = 'cm-color7'; break;
            case 'UNCLOSED_STRING':  cmClass = 'cm-error'; break;
            // Otros casos según tus tipos de token
        }

        // Omitir espacios en blanco
        if(token.type === 'WHITESPACE') return;

        try {
            // Convertir línea y columna (base 1 a base 0)
            const from = {line: token.line - 1, ch: token.column - 1};
            
            // Para comentarios multilínea, debemos calcular correctamente la posición final
            let to;
            if (token.type === 'COMMENT' && token.value.includes('\n')) {
                // Calcula la posición final para comentarios multilínea
                const lines = token.value.split('\n');
                const lastLine = lines[lines.length - 1];
                to = {
                    line: token.line + lines.length - 2, // -2 porque ya contamos desde 0 y porque queremos el índice
                    ch: lastLine.length
                };
            } else {
                // Para tokens de una sola línea
                to = {line: token.line - 1, ch: token.column - 1 + (token.value || '').length};
            }

            // Evita rangos negativos/invertidos
            if(to.ch < from.ch && to.line === from.line) return;
            
            // Asegúrate de que las líneas estén dentro del rango del documento
            const docLineCount = editor.lineCount();
            if (from.line >= docLineCount || to.line >= docLineCount) return;

            // CodeMirror limita a fin de línea (no marca varios saltos de línea de una vez)
            const mark = editor.markText(from, to, {className: cmClass});
            window.activeMarks.push(mark);
        } catch (e) {
            console.error('Error al marcar token:', token, e);
        }
    });
}


    // Colorea cada vez que el usuario edita
    editor.on('change', async () => {
        // Debounce - un solo análisis cada 500ms sin tecleo
        clearTimeout(window.highlightTimeout);
        window.highlightTimeout = setTimeout(async () => {
            const code = editor.getValue();
            const result = await window.compilerAPI.compile(code);
            if(result.tokens) colorearEditorConTokens(result.tokens);
        }, 500);
    });

});