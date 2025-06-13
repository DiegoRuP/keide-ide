import sys
import json
import os
import traceback
from analizador_lexico import LexicalAnalyzer, TokenType
from analizador_sintactico import Parser

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
    
    # Filtrar comentarios para el parser
    tokens_validos = [token for token in tokens if token.type != TokenType.COMMENT]

    # Guardar tokens léxicos
    with open(os.path.join(BASE_DIR, "tokensLexicos.txt"), "w", encoding="utf-8") as f:
        for token in tokens:
            f.write(str(token) + "\n")

    # Guardar errores léxicos
    with open(os.path.join(BASE_DIR, "erroresLexicos.txt"), "w", encoding="utf-8") as f:
        for error in errores_lexicos:
            f.write(f"Error en línea {error.line}, columna {error.column}: '{error.value}'\n")

    # Análisis sintáctico solo si no hay errores léxicos
    errores_sintacticos = []
    if not errores_lexicos:
        parser = Parser(tokens_validos)
        errores_sintacticos = parser.parse()

    # Guardar errores sintácticos
    with open(os.path.join(BASE_DIR, "erroresSintacticos.txt"), "w", encoding="utf-8") as f:
        if errores_sintacticos:
            for error in errores_sintacticos:
                f.write(error + "\n")
        else:
            f.write("No se encontraron errores sintácticos.\n")

    # Salida JSON unificada
    return json.dumps({
        'tokens': [
            {
                'type': token.type.name,
                'value': token.value,
                'line': token.line,
                'column': token.column
            } for token in tokens
        ],
        'errores_lexicos': [
            f"Error léxico en línea {e.line}, columna {e.column}: '{e.value}'"
            for e in errores_lexicos
        ],
        'errores_sintacticos': errores_sintacticos
    })

if __name__ == "__main__":
    sys.exit(main())