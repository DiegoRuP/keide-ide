import re
from enum import Enum, auto

class TokenType(Enum):
    NUMBER = auto()
    IDENTIFIER = auto()
    COMMENT = auto()
    UNCLOSED_COMMENT = auto()  # Nuevo tipo para comentarios sin cerrar
    KEYWORD = auto()
    ARITHMETIC_OP = auto()
    RELATIONAL_OP = auto()
    LOGICAL_OP = auto()
    BITWISE_OP = auto()
    SYMBOL = auto()
    ASSIGNMENT = auto()
    ERROR = auto()
    WHITESPACE = auto()
    STRING = auto()
    UNCLOSED_STRING = auto()  # Nuevo tipo para cadenas sin cerrar

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __str__(self):
        return f"Token({self.type.name}, '{self.value}', line {self.line}, col {self.column})"

class LexicalAnalyzer:
    def __init__(self):
        # Actualizada la lista de palabras reservadas según los requisitos
        self.keywords = {
            'if', 'else', 'end', 'do', 'while', 'switch', 'case',
            'int', 'float', 'main', 'cin', 'cout', 'break', 'default', 'return', 'for'
        }

        # Patrones actualizados incluyendo operadores de desplazamiento
        self.patterns = [
            # Comentarios de una línea
            (r'\/\/.*?(?:\n|$)', TokenType.COMMENT),
            
            # Comentarios multilínea se manejarán de forma especial
            
            # Cadenas de texto (entre comillas)
            (r'"[^"\n]*"', TokenType.STRING),  # Cadenas completas
            (r'"[^"\n]*$', TokenType.UNCLOSED_STRING),  # Cadenas sin cerrar hasta el final de línea
            (r'"[^"\n]*\n', TokenType.UNCLOSED_STRING),  # Cadenas sin cerrar con salto de línea
            
            # Palabras reservadas
            (r'\b(?:' + '|'.join(self.keywords) + r')\b', TokenType.KEYWORD),
            
            # Números (enteros y reales, con o sin signo)
            (r'[+-]?\d+\.\d+', TokenType.NUMBER),  # Números reales
            (r'[+-]?\d+', TokenType.NUMBER),       # Números enteros
            
            # Identificadores (letras y dígitos, no comienzan con dígito)
            (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
            
            # Operadores de desplazamiento: <<, >>
            (r'<<|>>', TokenType.BITWISE_OP),
            
            # Operadores aritméticos: +, -, *, /, %, ^, ++, --
            (r'\+\+|--|[\+\-\*\/\%\^]', TokenType.ARITHMETIC_OP),
            
            # Operadores relacionales: <, <=, >, >=, !=, ==
            (r'==|!=|<=|>=|<|>', TokenType.RELATIONAL_OP),
            
            # Operadores lógicos: && (and), || (or), ! (not)
            (r'&&|\|\||!', TokenType.LOGICAL_OP),
            
            # Símbolos: (, ), {, }, [, ], :, coma, punto y coma
            (r'[\(\)\{\}\[\]:,;]', TokenType.SYMBOL),
            
            # Asignación: =
            (r'=', TokenType.ASSIGNMENT),
            
            # Espacios en blanco
            (r'\s+', TokenType.WHITESPACE),
        ]

        self.regex_patterns = [(re.compile(pattern), token_type) for pattern, token_type in self.patterns]

    def tokenize(self, code):
        tokens = []
        line_num = 1
        line_start = 0
        i = 0

        while i < len(code):
            # Verificar primero si estamos al inicio de un comentario multilínea
            if i + 1 < len(code) and code[i:i+2] == '/*':
                comment_start_line = line_num
                comment_start_col = i - line_start + 1
                comment_start_pos = i
                i += 2
                
                # Buscar el token de cierre */
                found_closing = False
                comment_content = '/*'
                
                while i < len(code) and not found_closing:
                    if i + 1 < len(code) and code[i:i+2] == '*/':
                        comment_content += '*/'
                        found_closing = True
                        i += 2
                    else:
                        comment_content += code[i]
                        if code[i] == '\n':
                            line_num += 1
                            line_start = i + 1
                        i += 1
                
                if found_closing:
                    tokens.append(Token(TokenType.COMMENT, comment_content, comment_start_line, comment_start_col))
                else:
                    # Comentario sin cerrar - error léxico
                    tokens.append(Token(TokenType.UNCLOSED_COMMENT, comment_content, comment_start_line, comment_start_col))
                    # También lo añadimos como error para ser consistentes
                    tokens.append(Token(TokenType.ERROR, "Comentario multilínea sin cerrar", comment_start_line, comment_start_col))
                
                continue

            match = None
            for regex, token_type in self.regex_patterns:
                match = regex.match(code, i)
                if match:
                    value = match.group(0)
                    
                    # Corrección para el cálculo de columnas - usando posición absoluta
                    column = i - line_start + 1
                    
                    # Asegurarse de que la columna sea siempre positiva
                    if column <= 0:
                        column = 1

                    if token_type != TokenType.WHITESPACE:
                        tokens.append(Token(token_type, value, line_num, column))
                        
                        # Si encontramos una cadena sin cerrar, también la marcamos como error
                        if token_type == TokenType.UNCLOSED_STRING:
                            tokens.append(Token(TokenType.ERROR, "Cadena sin cerrar", line_num, column))

                    # Manejo de saltos de línea para contar líneas correctamente
                    newlines = value.count('\n')
                    if newlines > 0:
                        line_num += newlines
                        last_newline_pos = value.rfind('\n')
                        line_start = i + last_newline_pos + 1

                    i = match.end()
                    break

            if not match:
                # Si no se encuentra coincidencia, avanzar un carácter
                if code[i] == '\n':
                    line_num += 1
                    line_start = i + 1
                elif code[i] not in {' ', '\t'}:
                    # Usar posición absoluta para la columna
                    column = i - line_start + 1
                    if column <= 0:
                        column = 1
                    tokens.append(Token(TokenType.ERROR, code[i], line_num, column))
                i += 1

        return tokens

    def analyze(self, code):
        tokens = self.tokenize(code)
        # Recopilar todos los tokens de error, incluyendo comentarios sin cerrar y cadenas sin cerrar
        errors = [token for token in tokens if token.type in {TokenType.ERROR, TokenType.UNCLOSED_COMMENT, TokenType.UNCLOSED_STRING}]
        return tokens, errors

    def get_token_color(self, token_type):
        return {
            TokenType.NUMBER: 'color1',
            TokenType.IDENTIFIER: 'color2',
            TokenType.COMMENT: 'color3',
            TokenType.UNCLOSED_COMMENT: 'error',  # Los comentarios sin cerrar se marcan como error
            TokenType.KEYWORD: 'color4',
            TokenType.ARITHMETIC_OP: 'color5',
            TokenType.RELATIONAL_OP: 'color6',
            TokenType.LOGICAL_OP: 'color6',
            TokenType.BITWISE_OP: 'color5',
            TokenType.STRING: 'color7',
            TokenType.UNCLOSED_STRING: 'error',  # Las cadenas sin cerrar se marcan como error
            TokenType.SYMBOL: 'default',
            TokenType.ASSIGNMENT: 'default',
            TokenType.ERROR: 'error',
        }.get(token_type, 'default')

    def colorize_code(self, code):
        tokens = self.tokenize(code)
        result = []
        current_pos = 0

        for token in tokens:
            # Necesitamos manejar tokens especiales que pueden no estar en el texto original
            if token.type in {TokenType.UNCLOSED_COMMENT, TokenType.UNCLOSED_STRING, TokenType.ERROR} and token.value.startswith("Comentario") or token.value.startswith("Cadena"):
                continue
                
            token_pos = code.find(token.value, current_pos)
            if token_pos > current_pos:
                result.append({'text': code[current_pos:token_pos], 'class': 'default'})

            result.append({
                'text': token.value,
                'class': self.get_token_color(token.type)
            })
            current_pos = token_pos + len(token.value)

        if current_pos < len(code):
            result.append({'text': code[current_pos:], 'class': 'default'})

        return result

    def generate_html(self, code):
        colored_segments = self.colorize_code(code)
        html = []

        for segment in colored_segments:
            text = segment['text'].replace('\n', '<br>').replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
            html.append(f'<span class="{segment["class"]}">{text}</span>')

        return ''.join(html)

    def check_syntax(self, code):
        tokens, errors = self.analyze(code)
        error_messages = []
        
        for e in errors:
            if e.type == TokenType.UNCLOSED_COMMENT:
                error_messages.append(f"Error léxico en línea {e.line}, columna {e.column}: Comentario multilínea sin cerrar")
            elif e.type == TokenType.UNCLOSED_STRING:
                error_messages.append(f"Error léxico en línea {e.line}, columna {e.column}: Cadena sin cerrar")
            elif e.type == TokenType.ERROR and (e.value.startswith("Comentario") or e.value.startswith("Cadena")):
                error_messages.append(f"Error léxico en línea {e.line}, columna {e.column}: {e.value}")
            else:
                error_messages.append(f"Error léxico en línea {e.line}, columna {e.column}: Carácter no reconocido '{e.value}'")
                
        return error_messages

if __name__ == "__main__":
    analyzer = LexicalAnalyzer()

    try:
        with open("entrada.txt", "r") as f:
            test_code = f.read()

        tokens, errors = analyzer.analyze(test_code)

        print(f"Se encontraron {len(tokens)} tokens")
        print(f"Se encontraron {len(errors)} errores")

        with open("tokens.txt", "w") as f:
            for token in tokens:
                f.write(str(token) + "\n")

        with open("errores.txt", "w") as f:
            for error in errors:
                if error.type == TokenType.UNCLOSED_COMMENT:
                    f.write(f"Error en línea {error.line}, columna {error.column}: Comentario multilínea sin cerrar\n")
                elif error.type == TokenType.UNCLOSED_STRING:
                    f.write(f"Error en línea {error.line}, columna {error.column}: Cadena sin cerrar\n")
                elif error.type == TokenType.ERROR and (error.value.startswith("Comentario") or error.value.startswith("Cadena")):
                    f.write(f"Error en línea {error.line}, columna {error.column}: {error.value}\n")
                else:
                    f.write(f"Error en línea {error.line}, columna {error.column}: '{error.value}'\n")

        with open("salida.html", "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Análisis Léxico</title>
    <style>
        body { font-family: monospace; background-color: #f5f5f5; }
        .color1 { color: blue; }         /* Números */
        .color2 { color: green; }        /* Identificadores */
        .color3 { color: gray; }         /* Comentarios */
        .color4 { color: purple; }       /* Palabras reservadas */
        .color5 { color: red; }          /* Operadores aritméticos y bit */
        .color6 { color: brown; }        /* Operadores relacionales y lógicos */
        .color7 { color: darkgreen; }    /* Cadenas */
        .default { color: black; }       /* Otros tokens */
        .error { color: red; background-color: yellow; }
    </style>
</head>
<body>
""")
            f.write(analyzer.generate_html(test_code))
            f.write("""
</body>
</html>
""")
    except Exception as e:
        print(f"Error: {e}")