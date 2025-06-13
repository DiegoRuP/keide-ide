import re
from enum import Enum, auto

class TokenType(Enum):
    NUMBER = auto()
    IDENTIFIER = auto()
    COMMENT = auto()
    UNCLOSED_COMMENT = auto()
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
    UNCLOSED_STRING = auto()

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
        self.keywords = {
            'if', 'else', 'end', 'do', 'while', 'cin', 'cout', 'main', 'int', 'float', 'then', 'until'
        }

        self.patterns = [
            (r'\/\/.*?(?:\n|$)', TokenType.COMMENT),
            (r'"[^"\n]*"', TokenType.STRING),
            (r'"[^"\n]*$', TokenType.UNCLOSED_STRING),
            (r'"[^"\n]*\n', TokenType.UNCLOSED_STRING),
            (r'\b(?:' + '|'.join(self.keywords) + r')\b', TokenType.KEYWORD),
            (r'\d+\.(?!\d)', TokenType.ERROR),
            (r'\d+\.\d+', TokenType.NUMBER),
            (r'\d+', TokenType.NUMBER),
            (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
            (r'<<|>>', TokenType.BITWISE_OP),
            (r'\+\+|--|[\+\-\*\/\%\^]', TokenType.ARITHMETIC_OP),
            (r'==|!=|<=|>=|<|>', TokenType.RELATIONAL_OP),
            (r'&&|\|\||!', TokenType.LOGICAL_OP),
            (r'[$$$$\{\}$$$$:,;]', TokenType.SYMBOL),
            (r'=', TokenType.ASSIGNMENT),
            (r'\s+', TokenType.WHITESPACE),
        ]

        self.regex_patterns = [(re.compile(pattern), token_type) for pattern, token_type in self.patterns]

    def tokenize(self, code):
        tokens = []
        line_num = 1
        line_start = 0
        i = 0

        while i < len(code):
            if i + 1 < len(code) and code[i:i+2] == '/*':
                comment_start_line = line_num
                comment_start_col = i - line_start + 1
                comment_start_pos = i
                i += 2
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
                    preview = comment_content[:30] + "..." if len(comment_content) > 30 else comment_content
                    tokens.append(Token(TokenType.UNCLOSED_COMMENT, preview, comment_start_line, comment_start_col))
                    tokens.append(Token(TokenType.ERROR, "Comentario multilínea sin cerrar", comment_start_line, comment_start_col))
                continue

            if code[i] == '"':
                string_start_line = line_num
                string_start_col = i - line_start + 1
                string_start_pos = i
                i += 1
                found_closing = False
                string_content = '"'

                while i < len(code) and not found_closing:
                    if code[i] == '"':
                        string_content += '"'
                        found_closing = True
                        i += 1
                    elif code[i] == '\n':
                        string_content += code[i]
                        line_num += 1
                        line_start = i + 1
                        i += 1
                        break
                    else:
                        string_content += code[i]
                        i += 1
                        if i >= len(code):
                            break

                if found_closing:
                    tokens.append(Token(TokenType.STRING, string_content, string_start_line, string_start_col))
                else:
                    preview = string_content[:30] + "..." if len(string_content) > 30 else string_content
                    tokens.append(Token(TokenType.UNCLOSED_STRING, preview, string_start_line, string_start_col))
                    tokens.append(Token(TokenType.ERROR, "Cadena sin cerrar", string_start_line, string_start_col))
                continue

            match = None
            for regex, token_type in self.regex_patterns:
                match = regex.match(code, i)
                if match:
                    value = match.group(0)
                    column = i - line_start + 1
                    if column <= 0:
                        column = 1

                    if token_type != TokenType.WHITESPACE:
                        tokens.append(Token(token_type, value, line_num, column))

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
                    column = i - line_start + 1
                    if column <= 0:
                        column = 1
                    tokens.append(Token(TokenType.ERROR, code[i], line_num, column))
                i += 1

        return tokens

    def analyze(self, code):
        tokens = self.tokenize(code)
        errors = [token for token in tokens if token.type in {TokenType.ERROR, TokenType.UNCLOSED_COMMENT, TokenType.UNCLOSED_STRING}]
        valid_tokens = [token for token in tokens if token.type not in {TokenType.ERROR, TokenType.UNCLOSED_COMMENT, TokenType.UNCLOSED_STRING}]
        return valid_tokens, errors

    def get_token_color(self, token_type):
        return {
            TokenType.NUMBER: 'color1',
            TokenType.IDENTIFIER: 'color2',
            TokenType.COMMENT: 'color3',
            TokenType.UNCLOSED_COMMENT: 'error',
            TokenType.KEYWORD: 'color4',
            TokenType.ARITHMETIC_OP: 'color5',
            TokenType.RELATIONAL_OP: 'color6',
            TokenType.LOGICAL_OP: 'color6',
            TokenType.BITWISE_OP: 'color5',
            TokenType.STRING: 'color7',
            TokenType.UNCLOSED_STRING: 'error',
            TokenType.SYMBOL: 'default',
            TokenType.ASSIGNMENT: 'default',
            TokenType.ERROR: 'error',
        }.get(token_type, 'default')

    def colorize_code(self, code):
        tokens = self.tokenize(code)
        result = []
        current_pos = 0

        for token in tokens:
            if token.type == TokenType.ERROR and (token.value == "Comentario multilínea sin cerrar" or token.value == "Cadena sin cerrar"):
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
            if e.value == "Comentario multilínea sin cerrar":
                error_messages.append(f"Error léxico en línea {e.line}, columna {e.column}: Comentario multilínea sin cerrar")
            elif e.value == "Cadena sin cerrar":
                error_messages.append(f"Error léxico en línea {e.line}, columna {e.column}: Cadena sin cerrar")
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

        with open("tokensLexicos.txt", "w") as f:
            for token in tokens:
                f.write(str(token) + "\n")

        with open("erroresLexicos.txt", "w") as f:
            for token in tokens:
                if token.type == TokenType.ERROR:
                    if token.value == "Comentario multilínea sin cerrar":
                        f.write(f"Error en línea {token.line}, columna {token.column}: Comentario multilínea sin cerrar\n")
                    elif token.value == "Cadena sin cerrar":
                        f.write(f"Error en línea {token.line}, columna {token.column}: Cadena sin cerrar\n")
                    else:
                        f.write(f"Error en línea {token.line}, columna {token.column}: Carácter no reconocido '{token.value}'\n")

    except Exception as e:
        print(f"Error: {e}")