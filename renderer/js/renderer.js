document.addEventListener('DOMContentLoaded', () => {
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
    const editor = CodeMirror(document.getElementById('editor'), {
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

    // Función para cambiar el tema de CodeMirror
    function setCodeMirrorTheme(isDarkMode) {
        if (isDarkMode) {
            editor.setOption("theme", "dracula"); // Tema oscuro
        } else {
            editor.setOption("theme", "default"); // Tema claro
        }
    }

    // Obtener el contenido del editor
    function getEditorContent() {
        return editor.getValue();
    }

    // Establecer el contenido del editor
    function setEditorContent(content) {
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
            const content = getEditorContent(); // Usar CodeMirror para obtener el contenido
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
            const content = getEditorContent(); // Usar CodeMirror para obtener el contenido
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
            const content = getEditorContent(); // Usar CodeMirror para obtener el contenido
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
            const content = getEditorContent(); // Usar CodeMirror para obtener el contenido
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
        document.getElementById('total-lines').textContent = `Total líneas: ${editor.lineCount()}`;
    });
});

document.addEventListener("DOMContentLoaded", () => {
    let tabCount = 1; // Contador de pestañas

    const tabList = document.getElementById("tab-list");
    const tabContent = document.getElementById("tab-content");
    const btnNew = document.getElementById("btn-blank"); // Botón de nueva pestaña

    // Crear nueva pestaña
    btnNew.addEventListener("click", () => {
        tabCount++;
        const tabId = `tab-${tabCount}`;
        const editorId = `editor-${tabCount}`;

        // Crear pestaña
        const newTab = document.createElement("li");
        newTab.className = "nav-item";
        newTab.innerHTML = `
            <button class="nav-link" id="${tabId}" data-bs-toggle="tab" data-bs-target="#${editorId}" type="button" role="tab">
                Sin título ${tabCount} <span class="close-tab" data-id="${tabCount}">&times;</span>
            </button>
        `;
        tabList.appendChild(newTab);

        // Activar nueva pestaña
        document.getElementById(tabId).click();
        addCloseEvent();
    });

    addCloseEvent();
});
