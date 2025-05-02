# compilador.py
import sys
import json
from analizador_lexico import LexicalAnalyzer
import traceback

def main():
    try:
        # Verificar argumentos
        if len(sys.argv) < 2:
            print(json.dumps({'error': 'No se proporcionó archivo de entrada'}))
            return 1

        # Leer el archivo de entrada
        with open(sys.argv[1], 'r') as f:
            codigo = f.read()

        # Procesar el código
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
    
    tokens_serializados = [
        {
            'type': token.type.name,
            'value': token.value,
            'line': token.line,
            'column': token.column
        } for token in tokens
    ]
    
    mensajes_error = [
        f"Error léxico en línea {error.line}, columna {error.column}: Carácter no reconocido '{error.value}'"
        for error in errores
    ]
    
    return json.dumps({
        'tokens': tokens_serializados,
        'errores': mensajes_error,
        'html_coloreado': analizador.generate_html(codigo)
    })

if __name__ == "__main__":
    sys.exit(main())