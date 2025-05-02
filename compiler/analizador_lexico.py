import re
from enum import Enum, auto

class TokenType(Enum):
    NUMBER = auto()          # Números enteros y reales
    IDENTIFIER = auto()      # Identificadores
    COMMENT = auto()         # Comentarios
    KEYWORD = auto()         # Palabras reservadas
    ARITHMETIC_OP = auto()   # Operadores aritméticos
    RELATIONAL_OP = auto()   # Operadores relacionales
    LOGICAL_OP = auto()      # Operadores lógicos
    SYMBOL = auto()          # Símbolos como (, ), {, }, etc.
    ASSIGNMENT = auto()      # Operador de asignación
    ERROR = auto()           # Errores léxicos
    WHITESPACE = auto()      # Espacios en blanco (no se cuenta como token pero es útil para el análisis)

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Token({self.type}, '{self.value}', line {self.line}, col {self.column})"

class LexicalAnalyzer:
    def __init__(self):
        # Palabras reservadas
        self.keywords = {
            'if', 'else', 'end', 'do', 'while', 'switch', 'case', 
            'int', 'float', 'main', 'cin', 'cout', 'then', 'until', 'real'
        }
        
        # Definición de patrones para cada tipo de token
        self.patterns = [
            (r'\/\/.*?$', TokenType.COMMENT),                    # Comentarios de una línea
            (r'\/\*[\s\S]*?\*\/', TokenType.COMMENT),            # Comentarios multilinea
            (r'\b(?:if|else|end|do|while|switch|case|int|float|main|cin|cout|then|until|real)\b', TokenType.KEYWORD),  # Palabras reservadas
            (r'[+-]?\d+\.\d+', TokenType.NUMBER),                # Números reales (con punto decimal)
            (r'[+-]?\d+', TokenType.NUMBER),                     # Números enteros
            (r'[a-zA-Z][a-zA-Z0-9_]*', TokenType.IDENTIFIER),    # Identificadores
            (r'[\+\-\*\/\%\^\+\+\-\-]', TokenType.ARITHMETIC_OP), # Operadores aritméticos
            (r'[<>]=?|==|!=', TokenType.RELATIONAL_OP),          # Operadores relacionales
            (r'&&|\|\||!=', TokenType.LOGICAL_OP),               # Operadores lógicos
            (r'[(){},;]', TokenType.SYMBOL),                     # Símbolos
            (r'=', TokenType.ASSIGNMENT),                        # Asignación
            (r'\s+', TokenType.WHITESPACE),                      # Espacios en blanco
        ]
        
        # Compilar las expresiones regulares para mejor rendimiento
        self.regex_patterns = [(re.compile(pattern), token_type) for pattern, token_type in self.patterns]
        
    def tokenize(self, code):
        tokens = []
        line_num = 1
        line_start = 0
        i = 0
        
        while i < len(code):
            # Buscar coincidencias con los patrones en la posición actual
            match = None
            for regex, token_type in self.regex_patterns:
                match = regex.match(code, i)
                if match:
                    value = match.group(0)
                    column = i - line_start + 1
                    
                    # No agregar tokens para espacios en blanco
                    if token_type != TokenType.WHITESPACE:
                        tokens.append(Token(token_type, value, line_num, column))
                    
                    # Actualizar el número de línea para saltos de línea
                    newlines = value.count('\n')
                    if newlines > 0:
                        line_num += newlines
                        line_start = i + match.end() - 1 - value.rfind('\n')
                    
                    # Mover el índice después del token coincidente
                    i = match.end()
                    break
            
            # Si no se encontraron coincidencias, reportar como error
            if not match:
                # Comprobar si es un carácter de nueva línea
                if code[i] == '\n':
                    line_num += 1
                    line_start = i + 1
                elif code[i] != ' ' and code[i] != '\t':
                    tokens.append(Token(TokenType.ERROR, code[i], line_num, i - line_start + 1))
                i += 1
        
        return tokens

    def analyze(self, code):
        """Analizar el código y devolver tokens y errores"""
        tokens = self.tokenize(code)
        errors = [token for token in tokens if token.type == TokenType.ERROR]
        return tokens, errors

    def get_token_color(self, token_type):
        """Devuelve el color asociado a cada tipo de token"""
        if token_type == TokenType.NUMBER:
            return 'color1'  # Números
        elif token_type == TokenType.IDENTIFIER:
            return 'color2'  # Identificadores
        elif token_type == TokenType.COMMENT:
            return 'color3'  # Comentarios
        elif token_type == TokenType.KEYWORD:
            return 'color4'  # Palabras reservadas
        elif token_type == TokenType.ARITHMETIC_OP:
            return 'color5'  # Operadores aritméticos
        elif token_type == TokenType.RELATIONAL_OP or token_type == TokenType.LOGICAL_OP:
            return 'color6'  # Operadores relacionales y lógicos
        elif token_type == TokenType.ERROR:
            return 'error'   # Errores
        else:
            return 'default' # Otros tokens

    def colorize_code(self, code):
        """Devuelve un array de objetos que contienen el texto y su clase de color"""
        tokens = self.tokenize(code)
        result = []
        
        # Mantener un seguimiento de la posición actual en el código
        current_pos = 0
        
        for token in tokens:
            # Calcular la posición del token en el código
            token_pos = -1
            search_start = current_pos
            
            # Encontrar la posición exacta del token en el código
            while token_pos == -1 and search_start < len(code):
                token_pos = code.find(token.value, search_start)
                search_start += 1
            
            # Si no se encontró el token (no debería ocurrir), continuar
            if token_pos == -1:
                continue
            
            # Agregar cualquier texto entre la posición actual y el inicio del token
            if token_pos > current_pos:
                whitespace = code[current_pos:token_pos]
                if whitespace:
                    result.append({'text': whitespace, 'class': 'default'})
            
            # Agregar el token con su clase de color correspondiente
            result.append({
                'text': token.value,
                'class': self.get_token_color(token.type)
            })
            
            # Actualizar la posición actual
            current_pos = token_pos + len(token.value)
        
        # Agregar cualquier texto restante después del último token
        if current_pos < len(code):
            result.append({'text': code[current_pos:], 'class': 'default'})
        
        return result

    def generate_html(self, code):
        """Genera HTML coloreado para el código"""
        colored_segments = self.colorize_code(code)
        html = []
        
        for segment in colored_segments:
            text = segment['text'].replace('\n', '<br>').replace(' ', '&nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
            html.append(f'<span class="{segment["class"]}">{text}</span>')
        
        return ''.join(html)

    def check_syntax(self, code):
        """Analiza el código y devuelve los errores encontrados"""
        tokens, errors = self.analyze(code)
        error_messages = []
        
        for error in errors:
            error_messages.append(f"Error léxico en línea {error.line}, columna {error.column}: Carácter no reconocido '{error.value}'")
        
        return error_messages

if __name__ == "__main__":
    # Ejemplo de uso
    analyzer = LexicalAnalyzer()
    
    # Código de ejemplo
    test_code = """
    int main() {
        float x = 3.14;
        // Este es un comentario
        /* Este es un
           comentario multilínea */
        if (x > 2.0) {
            return x + 1;
        } else {
            return x - 1;
        }
    }
    """
    
    tokens, errors = analyzer.analyze(test_code)
    
    print("Tokens encontrados:")
    for token in tokens:
        print(token)
    
    print("\nErrores encontrados:")
    for error in errors:
        print(f"Error en línea {error.line}, columna {error.column}: Carácter no reconocido '{error.value}'")
    
    print("\nCódigo HTML coloreado:")
    print(analyzer.generate_html(test_code))