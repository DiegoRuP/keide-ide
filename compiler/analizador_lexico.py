import re
from enum import Enum, auto

class TokenType(Enum):
    NUMBER = auto()
    IDENTIFIER = auto()
    COMMENT = auto()
    KEYWORD = auto()
    ARITHMETIC_OP = auto()
    RELATIONAL_OP = auto()
    LOGICAL_OP = auto()
    SYMBOL = auto()
    ASSIGNMENT = auto()
    ERROR = auto()
    WHITESPACE = auto()

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
            'if', 'else', 'end', 'do', 'while', 'switch', 'case',
            'int', 'float', 'main', 'cin', 'cout', 'then', 'until', 'real'
        }

        self.patterns = [
            (r'\/\/.*?$', TokenType.COMMENT),
            (r'\/\*[\s\S]*?\*\/', TokenType.COMMENT),
            (r'\b(?:' + '|'.join(self.keywords) + r')\b', TokenType.KEYWORD),
            (r'[+-]?\d+\.\d+', TokenType.NUMBER),
            (r'[+-]?\d+', TokenType.NUMBER),
            (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
            (r'\+\+|--|[\+\-\*\/\%\^]', TokenType.ARITHMETIC_OP),
            (r'==|!=|<=|>=|<|>', TokenType.RELATIONAL_OP),
            (r'&&|\|\|', TokenType.LOGICAL_OP),
            (r'[(){},;]', TokenType.SYMBOL),
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
            match = None
            for regex, token_type in self.regex_patterns:
                match = regex.match(code, i)
                if match:
                    value = match.group(0)
                    column = i - line_start + 1

                    if token_type != TokenType.WHITESPACE:
                        tokens.append(Token(token_type, value, line_num, column))

                    newlines = value.count('\n')
                    if newlines > 0:
                        line_num += newlines
                        line_start = i + match.end() - 1 - value.rfind('\n')

                    i = match.end()
                    break

            if not match:
                if code[i] == '\n':
                    line_num += 1
                    line_start = i + 1
                elif code[i] not in {' ', '\t'}:
                    tokens.append(Token(TokenType.ERROR, code[i], line_num, i - line_start + 1))
                i += 1

        return tokens

    def analyze(self, code):
        tokens = self.tokenize(code)
        errors = [token for token in tokens if token.type == TokenType.ERROR]
        return tokens, errors

    def get_token_color(self, token_type):
        return {
            TokenType.NUMBER: 'color1',
            TokenType.IDENTIFIER: 'color2',
            TokenType.COMMENT: 'color3',
            TokenType.KEYWORD: 'color4',
            TokenType.ARITHMETIC_OP: 'color5',
            TokenType.RELATIONAL_OP: 'color6',
            TokenType.LOGICAL_OP: 'color6',
            TokenType.ERROR: 'error',
        }.get(token_type, 'default')

    def colorize_code(self, code):
        tokens = self.tokenize(code)
        result = []
        current_pos = 0

        for token in tokens:
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
        return [f"Error léxico en línea {e.line}, columna {e.column}: Carácter no reconocido '{e.value}'" for e in errors]

if __name__ == "__main__":
    analyzer = LexicalAnalyzer()

    with open("entrada.txt", "r") as f:
        test_code = f.read()

    tokens, errors = analyzer.analyze(test_code)

    with open("tokens.txt", "w") as f:
        for token in tokens:
            f.write(str(token) + "\n")

    with open("errores.txt", "w") as f:
        for error in errors:
            f.write(f"Error en línea {error.line}, columna {error.column}: '{error.value}'\n")

    with open("salida.html", "w") as f:
        f.write(analyzer.generate_html(test_code))
