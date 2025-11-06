# compilador.py
import sys
import json
import traceback
import os
import subprocess
import stat

from analizador_lexico import LexicalAnalyzer, TokenType
from analizador_sintactico import analyze_syntax, format_ast_tree, ast_to_html
from analizador_sintactico import export_ast_graphviz
from analizador_semantico import SemanticAnalyzer, semantic_tree_to_html
from tabla_hash import populate_hash_table_from_symbol_table, hash_table_to_html
from generador_llvm import CodeGenerator

# Directorio donde se encuentra este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    try:
        if len(sys.argv) < 2:
            print(json.dumps({'error': 'No se proporcionó archivo de entrada'}))
            return 1
        
        input_file = sys.argv[1]
        
        run_mode = False
        
        # Si hay un segundo argumento y es '--run', activamos el modo ejecución
        if len(sys.argv) > 2 and sys.argv[2] == '--run':
            run_mode = True

        with open(input_file, 'r') as f:
            codigo = f.read()

        resultado = compilar(codigo, run_mode)
        print(resultado)
        return 0

    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(json.dumps(error_info))
        return 1

def run_llvm_compiler(ll_filename, output_exe_name):
    """
    Ejecuta la cadena de comandos de LLVM
    """
    opt_file = os.path.join(BASE_DIR, "programa_opt.ll")
    asm_file = os.path.join(BASE_DIR, "programa.s")
    exe_file = os.path.join(BASE_DIR, output_exe_name)

    try:
        # 1. opt -O2 programa.ll -S -o programa_opt.ll
        print("Optimizando LLVM IR...", file=sys.stderr)
        subprocess.run(["opt", "-O2", ll_filename, "-S", "-o", opt_file], check=True, capture_output=True, text=True)

        # 2. llc programa_opt.ll -o programa.s
        print("Compilando IR a ensamblador...", file=sys.stderr)
        subprocess.run(["llc", opt_file, "-filetype=asm", "-o", asm_file], check=True, capture_output=True, text=True)

        # 3. clang programa.s -o programa
        print("Compilando ensamblador a ejecutable...", file=sys.stderr)
        subprocess.run(["clang", asm_file, "-o", exe_file], check=True, capture_output=True, text=True)

        print(f"\n¡Compilación exitosa! Ejecutable creado en: {exe_file}", file=sys.stderr)
        
        # 1. Definir el nombre del script y su contenido
        script_name = os.path.join(BASE_DIR, "run.command")
        script_content = f"""#!/bin/bash
            # Obtener el directorio donde se encuentra este script
            DIR=$(cd "$(dirname "$0")" && pwd)

            # Ejecutar el programa compilado
            # Ahora 'cin' y 'cout' funcionarán en esta ventana
            "$DIR/{output_exe_name}"

            # Mantener la ventana abierta
            echo
            echo "---"
            echo "El programa ha finalizado. Presiona Enter para cerrar esta ventana."
            read
            """
            
        # 2. Escribir el script en el disco
        with open(script_name, "w") as f:
            f.write(script_content)
            
        # 3. Darle permisos de ejecución (¡Muy importante en macOS!)
        st = os.stat(script_name)
        os.chmod(script_name, st.st_mode | stat.S_IEXEC)
        
        # 4. Abrir el script (esto lanzará la Terminal.app)
        print(f"Abriendo script interactivo: {script_name}", file=sys.stderr)
        subprocess.run(["open", script_name], check=True)

        return {
            "success": True,
            "output_exe": exe_file,
            "opt_file": opt_file,
            "asm_file": asm_file,
            "program_output": "(Ejecutado en terminal interactiva)" 
        }
        
    except subprocess.CalledProcessError as e:
        print(f"Error durante la compilación LLVM: {e}", file=sys.stderr)
        print(f"STDOUT de Subprocess: {e.stdout}", file=sys.stderr)
        print(f"STDERR de Subprocess: {e.stderr}", file=sys.stderr)
        return {"success": False, "error": str(e), "details": e.stderr}
    
    except FileNotFoundError as e:
        print(f"Error: No se encontró un comando (¿LLVM no está en el PATH?): {e}", file=sys.stderr)
        return {"success": False, "error": f"Comando no encontrado: {e.filename}. Asegúrate de que LLVM esté instalado y en tu PATH."}

def compilar(codigo, run_mode=False):
    # Análisis léxico
    analizador = LexicalAnalyzer()
    tokens, errores_lexicos = analizador.analyze(codigo)
    
    # Filtrar los tokens para la escritura en archivo
    tokens_filtrados = [token for token in tokens if token.type != TokenType.COMMENT]

    # Guardar tokens en archivo
    with open(os.path.join(BASE_DIR, "tokens.txt"), "w", encoding="utf-8") as f:
        for token in tokens_filtrados:
            f.write(str(token) + "\n")

    # Guardar errores léxicos en archivo
    with open(os.path.join(BASE_DIR, "errores_lexicos.txt"), "w", encoding="utf-8") as f:
        for error in errores_lexicos:
            f.write(f"Error léxico en línea {error.line}, columna {error.column}: '{error.value}'\n")
    
    # Análisis sintáctico (solo si no hay errores léxicos)
    ast = None
    errores_sintacticos = []
    ast_text = ""
    ast_html = ""
    semantic_tree_html = ""
    
    if not errores_lexicos:
        ast, errores_sintacticos = analyze_syntax(tokens)
        
        # Guardar AST en archivo
        if ast:
            ast_text = format_ast_tree(ast)
            with open(os.path.join(BASE_DIR, "ast.txt"), "w", encoding="utf-8") as f:
                f.write(ast_text)
            
            # Generar HTML del AST
            ast_html = ast_to_html(ast)

            # Exportar imagen del AST
            graphviz_path = export_ast_graphviz(ast, filename=os.path.join(BASE_DIR, "ast_visual"))
        
        # Guardar errores sintácticos en archivo
        with open(os.path.join(BASE_DIR, "errores_sintacticos.txt"), "w", encoding="utf-8") as f:
            for error in errores_sintacticos:
                f.write(str(error) + "\n")

    # Análisis semántico 
    errores_semanticos = []
    tabla_de_simbolos = {}  # Inicializamos la tabla
    hash_table_html = "" # Inicializamos el HTML de la tabla hash
    
    if not errores_lexicos and not errores_sintacticos:
        sem_analyzer = SemanticAnalyzer()
        errores_semanticos, tabla_de_simbolos = sem_analyzer.analyze(ast)

        semantic_tree_html = semantic_tree_to_html(ast)
        
        # Crear y poblar la tabla hash desde la tabla de símbolos
        populated_hash_table = populate_hash_table_from_symbol_table(tabla_de_simbolos, hash_table_size=16)
        # Generar HTML de la tabla hash
        hash_table_html = hash_table_to_html(populated_hash_table)
        
        # Guardar errores semánticos en archivo
        with open(os.path.join(BASE_DIR, "errores_semanticos.txt"), "w", encoding="utf-8") as f:
            for error in errores_semanticos:
                f.write(error + "\n")

        # Guardar tabla de símbolos en archivo
        with open(os.path.join(BASE_DIR, "tabla_de_simbolos.json"), "w", encoding="utf-8") as f:
            json.dump(tabla_de_simbolos, f, indent=4)
    
    # Guardar HTML coloreado
    html_coloreado = analizador.generate_html(codigo)
    with open(os.path.join(BASE_DIR, "salida.html"), "w", encoding="utf-8") as f:
        f.write(html_coloreado)

    # Incluir tanto tokens válidos como errores para el coloreado
    todos_los_tokens = tokens + errores_lexicos
    
    # --- Generación de Código LLVM ---
    llvm_ir = ""
    compilacion_llvm_log = {"success": False}
    program_output = ""
    
    if not errores_lexicos and not errores_sintacticos and not errores_semanticos and run_mode:
        
        print("--- MODO RUN ACTIVADO: Iniciando compilación LLVM ---", file=sys.stderr)
        
        try:
            # 1. Generar el LLVM IR
            code_gen = CodeGenerator()
            llvm_ir = code_gen.generate(ast)
            
            # 2. Guardar el archivo .ll
            ll_filename = os.path.join(BASE_DIR, "programa.ll")
            with open(ll_filename, "w", encoding="utf-8") as f:
                f.write(llvm_ir)

            # 3. Ejecutar la cadena de compilación (opt, llc, clang)
            nombre_ejecutable = "programa"
            compilacion_llvm_log = run_llvm_compiler(ll_filename, nombre_ejecutable)
            
            if compilacion_llvm_log.get("success"):
                program_output = compilacion_llvm_log.get("program_output", "")

        except Exception as e:
            # Capturar errores del *generador de código*
            errores_semanticos.append(f"Error de Generación de Código: {e}\n{traceback.format_exc()}")

    return json.dumps({
        'tokens': [
            {
                'type': token.type.name,
                'value': token.value,
                'line': token.line,
                'column': token.column
            } for token in todos_los_tokens
        ],
        'errores_lexicos': [
            f"Error léxico en línea {e.line}, columna {e.column}: Carácter no reconocido '{e.value}'"
            for e in errores_lexicos
        ],
        'ast': ast.to_dict() if ast else None,
        'ast_text': ast_text,
        'ast_html': ast_html,
        'semantic_tree_html': semantic_tree_html,
        'hash_table_html': hash_table_html,
        'errores_sintacticos': [str(e) for e in errores_sintacticos],
        'errores_semanticos': [str(e) for e in errores_semanticos],
        'tabla_de_simbolos': tabla_de_simbolos, #Incluir la tabla en la salida
        'llvm_ir': llvm_ir,  # <-- Nuevo
        'compilacion_llvm': compilacion_llvm_log, # <-- Nuevo
        'html_coloreado': html_coloreado
    })

if __name__ == "__main__":
    sys.exit(main())