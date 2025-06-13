from analizador_lexico import TokenType, Token

class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if self.tokens else None
        self.errors = []

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None

    def match(self, expected_type):
        if self.current_token and self.current_token.type == expected_type:
            self.advance()
        else:
            self.errors.append(f"Se esperaba {expected_type.name} en línea {self.current_token.line if self.current_token else 'EOF'}")

    def match_keyword(self, expected_value):
        if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value == expected_value:
            self.advance()
        else:
            self.errors.append(f"Se esperaba {expected_value} en línea {self.current_token.line if self.current_token else 'EOF'}")

    def parse(self):
        self.program()
        return self.errors

    def program(self):
        self.match_keyword('main')
        self.match(TokenType.SYMBOL)  # '{'
        while self.current_token and self.current_token.type != TokenType.SYMBOL:  # '}'
            self.statement()
        self.match(TokenType.SYMBOL)  # '}'

    # Continúa el resto de métodos de tu parser

    def statement(self):
        if self.current_token.type in [TokenType.INT, TokenType.FLOAT]:
            self.declaration()
        elif self.current_token.type == TokenType.IDENTIFIER:
            self.assignment()
        elif self.current_token.type == TokenType.IF:
            self.if_statement()
        elif self.current_token.type == TokenType.DO:
            self.do_until_loop()
        elif self.current_token.type == TokenType.WHILE:
            self.while_loop()
        elif self.current_token.type == TokenType.CIN:
            self.input_stmt()
        elif self.current_token.type == TokenType.COUT:
            self.output_stmt()
        else:
            self.errors.append(f"Sentencia no válida en línea {self.current_token.line}")
            self.advance()

    def declaration(self):
        self.advance()  # Tipo
        self.match(TokenType.IDENTIFIER)
        while self.current_token and self.current_token.type == TokenType.COMMA:
            self.advance()
            self.match(TokenType.IDENTIFIER)
        self.match(TokenType.SEMICOLON)

    def assignment(self):
        self.match(TokenType.IDENTIFIER)
        if self.current_token and self.current_token.type in [TokenType.INCREMENT, TokenType.DECREMENT]:
            self.advance()
            self.match(TokenType.SEMICOLON)
        else:
            self.match(TokenType.ASSIGN)
            self.expression()
            self.match(TokenType.SEMICOLON)

    def expression(self):
        self.logical_or()

    def logical_or(self):
        self.logical_and()
        while self.current_token and self.current_token.type == TokenType.OR:
            self.advance()
            self.logical_and()

    def logical_and(self):
        self.equality()
        while self.current_token and self.current_token.type == TokenType.AND:
            self.advance()
            self.equality()

    def equality(self):
        self.relational()
        while self.current_token and self.current_token.type in [TokenType.EQUAL_EQUAL, TokenType.NOT_EQUAL]:
            self.advance()
            self.relational()

    def relational(self):
        self.additive()
        while self.current_token and self.current_token.type in [TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL]:
            self.advance()
            self.additive()

    def additive(self):
        self.term()
        while self.current_token and self.current_token.type in [TokenType.PLUS, TokenType.MINUS]:
            self.advance()
            self.term()

    def term(self):
        self.factor()
        while self.current_token and self.current_token.type in [TokenType.MULTIPLY, TokenType.DIVIDE]:
            self.advance()
            self.factor()

    def factor(self):
        if self.current_token.type in [TokenType.NUMBER, TokenType.IDENTIFIER, TokenType.TRUE, TokenType.FALSE]:
            self.advance()
        elif self.current_token.type == TokenType.LEFT_PAREN:
            self.advance()
            self.expression()
            self.match(TokenType.RIGHT_PAREN)
        else:
            self.errors.append(f"Factor inválido en línea {self.current_token.line}")
            self.advance()

    def if_statement(self):
        self.match(TokenType.IF)
        self.expression()
        self.match(TokenType.THEN)
        self.statement_block()
        if self.current_token and self.current_token.type == TokenType.ELSE:
            self.advance()
            self.statement_block()
        self.match(TokenType.END)

    def statement_block(self):
        while self.current_token and self.current_token.type not in [TokenType.END, TokenType.ELSE, TokenType.UNTIL]:
            self.statement()

    def do_until_loop(self):
        self.match(TokenType.DO)
        while self.current_token and self.current_token.type != TokenType.UNTIL:
            self.statement()
        self.match(TokenType.UNTIL)
        self.expression()

    def while_loop(self):
        self.match(TokenType.WHILE)
        self.expression()
        while self.current_token and self.current_token.type != TokenType.END:
            self.statement()
        self.match(TokenType.END)

    def input_stmt(self):
        self.match(TokenType.CIN)
        self.match(TokenType.SHIFT_RIGHT)
        self.match(TokenType.IDENTIFIER)
        self.match(TokenType.SEMICOLON)

    def output_stmt(self):
        self.match(TokenType.COUT)
        self.match(TokenType.SHIFT_LEFT)
        self.match(TokenType.IDENTIFIER)
        self.match(TokenType.SEMICOLON)
