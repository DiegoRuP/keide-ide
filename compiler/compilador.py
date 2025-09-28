# compilador.py
import sys
import json
from analizador_lexico import LexicalAnalyzer, TokenType
from analizador_sintactico import analyze_syntax, format_ast_tree, ast_to_html
from analizador_sintactico import export_ast_graphviz
from analizador_semantico import SemanticAnalyzer, semantic_tree_to_html
import traceback
import os

# Directorio donde se encuentra este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    try:
        if len(sys.argv) < 2:
            print(json.dumps({'error': 'No se proporcionó archivo de entrada'}))
            return 1

        with open(sys.argv[1], 'r') as f:
            codigo = f.read()

        resultado = compilar(codigo)
        print(resultado)
        return 0

    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(json.dumps(error_info))
        return 1

def compilar(codigo):
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
    if not errores_lexicos and not errores_sintacticos:
        sem_analyzer = SemanticAnalyzer()
        errores_semanticos, tabla_de_simbolos = sem_analyzer.analyze(ast)

        semantic_tree_html = semantic_tree_to_html(ast)

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
        'errores_sintacticos': [str(e) for e in errores_sintacticos],
        'errores_semanticos': [str(e) for e in errores_semanticos],
        'tabla_de_simbolos': tabla_de_simbolos, #Incluir la tabla en la salida
        'html_coloreado': html_coloreado
    })

if __name__ == "__main__":
    sys.exit(main())