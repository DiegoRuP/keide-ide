# compilador.py
import sys
import json
from analizador_lexico import LexicalAnalyzer
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
    analizador = LexicalAnalyzer()
    tokens, errores = analizador.analyze(codigo)

    # Guardar tokens en archivo
    with open(os.path.join(BASE_DIR, "tokens.txt"), "w", encoding="utf-8") as f:
        for token in tokens:
            f.write(str(token) + "\n")

    # Guardar errores en archivo
    with open(os.path.join(BASE_DIR, "errores.txt"), "w", encoding="utf-8") as f:
        for error in errores:
            f.write(f"Error en línea {error.line}, columna {error.column}: '{error.value}'\n")

    # Guardar HTML coloreado
    html_coloreado = analizador.generate_html(codigo)
    with open(os.path.join(BASE_DIR, "salida.html"), "w", encoding="utf-8") as f:
        f.write(html_coloreado)

    # Incluir tanto tokens válidos como errores para el coloreado
    todos_los_tokens = tokens + errores

    return json.dumps({
        'tokens': [
            {
                'type': token.type.name,
                'value': token.value,
                'line': token.line,
                'column': token.column
            } for token in todos_los_tokens
        ],
        'errores': [
            f"Error léxico en línea {e.line}, columna {e.column}: Carácter no reconocido '{e.value}'"
            for e in errores
        ],
        'html_coloreado': html_coloreado
    })

if __name__ == "__main__":
    sys.exit(main())
