document.addEventListener('DOMContentLoaded', () => {

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
        const newHeight = containerRect.bottom - e.clientY - 60; /* Ajuste para el header */
        
        logsContainer.style.height = `${newHeight}px`;
        editorAnalysisContainer.style.height = `calc(100% - ${newHeight}px)`;
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

    let tabCount = 1; // Contador de pestañas
    const tabList = document.getElementById("tab-list");
    const editorContainer = document.getElementById("editor");
    const btnNew = document.getElementById("btn-blank"); // Botón de nueva pestaña

    // Objeto para almacenar las instancias de CodeMirror y su contenido
    const editors = {};

    // Función para inicializar CodeMirror en un contenedor específico
    function initializeCodeMirror(container) {
        return CodeMirror(container, {
            lineNumbers: true,
            theme: "dracula",
            value: "// Escribe tu código aquí"
        });
    }

    // Crear la primera pestaña y su CodeMirror
    const firstTabId = `tab-1`;
    const firstEditorId = `editor-1`;

    const firstTab = document.createElement("li");
    firstTab.className = "nav-item";
    tabList.appendChild(firstTab);

    const firstEditorWrapper = document.createElement("div");
    firstEditorWrapper.id = firstEditorId;
    firstEditorWrapper.classList.add("code-container");
    editorContainer.appendChild(firstEditorWrapper);

    const firstEditor = initializeCodeMirror(firstEditorWrapper);
    editors[firstEditorId] = firstEditor;

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

        // Crear un nuevo contenedor para CodeMirror
        const newEditorWrapper = document.createElement("div");
        newEditorWrapper.id = editorId;
        newEditorWrapper.classList.add("code-container");
        editorContainer.appendChild(newEditorWrapper);

        // Inicializar CodeMirror en el nuevo contenedor
        const newEditor = initializeCodeMirror(newEditorWrapper);
        editors[editorId] = newEditor;

        // Ocultar todos los contenedores de CodeMirror
        document.querySelectorAll(".code-container").forEach(container => {
            container.style.display = "none";
        });

        // Mostrar el contenedor de CodeMirror correspondiente a la pestaña activa
        newEditorWrapper.style.display = "block";

        // Activar nueva pestaña
        document.getElementById(tabId).click();
        addCloseEvent();
    });

    // Manejar el cambio de pestañas
    tabList.addEventListener("click", (event) => {
        const tabButton = event.target.closest(".nav-link");
        if (tabButton) {
            const editorId = tabButton.getAttribute("data-bs-target").replace("#", "");
            // Ocultar todos los contenedores de CodeMirror
            document.querySelectorAll(".code-container").forEach(container => {
                container.style.display = "none";
            });
            // Mostrar el contenedor de CodeMirror correspondiente a la pestaña activa
            const activeEditorWrapper = document.getElementById(editorId);
            if (activeEditorWrapper) {
                activeEditorWrapper.style.display = "block";
            }
        }
    });

    // Función para agregar el evento de cerrar pestaña
    function addCloseEvent() {
        document.querySelectorAll(".close-tab").forEach(closeButton => {
            closeButton.addEventListener("click", (event) => {
                event.stopPropagation();
                const tabId = closeButton.getAttribute("data-id");
                const tabButton = document.getElementById(`tab-${tabId}`);
                const editorId = `editor-${tabId}`;

                // Verificar si el botón de la pestaña existe antes de intentar eliminarlo
                if (tabButton) {
                    // Eliminar la pestaña
                    tabButton.closest(".nav-item").remove();
                }

                // Eliminar el contenedor de CodeMirror
                const editorWrapperToRemove = document.getElementById(editorId);
                if (editorWrapperToRemove) {
                    editorWrapperToRemove.remove();
                }

                // Eliminar la instancia de CodeMirror del objeto `editors`
                delete editors[editorId];

                // Si no hay más pestañas, crear una nueva
                if (tabList.children.length === 0) {
                    btnNew.click();
                }
            });
        });
    }

    addCloseEvent();

});

