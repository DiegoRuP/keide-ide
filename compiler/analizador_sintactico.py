import re
from enum import Enum, auto
from analizador_lexico import Token, TokenType
from graphviz import Digraph
import json


class ASTNodeType(Enum):
    PROGRAM = auto()
    MAIN = auto()
    DECLARATION = auto()
    ASSIGNMENT = auto()
    IF_STATEMENT = auto()
    WHILE_STATEMENT = auto()
    DO_UNTIL_STATEMENT = auto()
    EXPRESSION = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    BLOCK = auto()
    INPUT_STATEMENT = auto()
    OUTPUT_STATEMENT = auto()
    BOOLEAN = auto()

class ASTNode:
    def __init__(self, node_type, value=None, children=None, line=None, column=None):
        self.type = node_type
        self.value = value
        self.children = children if children else []
        self.line = line
        self.column = column
    
    def to_dict(self):
        return {
            'type': self.type.name,
            'value': self.value,
            'line': self.line,
            'column': self.column,
            'children': [child.to_dict() if child else None for child in self.children]
        }

class SyntaxError:
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Error sintáctico en línea {self.line}, columna {self.column}: {self.message}"

class SyntacticAnalyzer:
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.type not in {TokenType.COMMENT, TokenType.WHITESPACE}]
        self.current = 0
        self.errors = []
        # Para rastrear si estamos dentro de un do-until
        self.in_do_until = False
        
    def parse(self):
        """Punto de entrada del parser"""
        ast = ASTNode(ASTNodeType.PROGRAM, line=1, column=1)  # Crear nodo raíz siempre
        
        try:
            # Intentar parsear el programa completo
            ast = self.program()
            
            # Verificar si quedan tokens sin procesar
            if self.current < len(self.tokens):
                remaining_tokens = len(self.tokens) - self.current
                # Mostrar los tokens que no se procesaron para debug
                unprocessed = []
                for i in range(self.current, min(self.current + 5, len(self.tokens))):
                    unprocessed.append(f"{self.tokens[i].type.name}: '{self.tokens[i].value}'")
                self.error(f"Quedan {remaining_tokens} token(s) sin procesar. Primeros tokens: {', '.join(unprocessed)}")
                
        except Exception as e:
            # En caso de error catastrófico, mantener el AST parcial
            if self.current < len(self.tokens):
                token = self.tokens[self.current]
                self.errors.append(SyntaxError(f"Error inesperado: {str(e)}", token.line, token.column))
            else:
                self.errors.append(SyntaxError(f"Error inesperado: {str(e)}", -1, -1))
        
        # Siempre retornar el AST (completo o parcial) y los errores
        return ast, self.errors
    
    def current_token(self):
        """Obtiene el token actual sin consumirlo"""
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return None
    
    def peek(self, offset=1):
        """Mira el siguiente token sin consumirlo"""
        pos = self.current + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def consume(self, expected_type=None, expected_value=None):
        """Consume el token actual si coincide con lo esperado"""
        token = self.current_token()
        if not token:
            self.error("Fin inesperado del archivo")
            return None
            
        if expected_type and token.type != expected_type:
            self.error(f"Se esperaba {expected_type.name}, se encontró {token.type.name} '{token.value}'")
            # Avanzar de todos modos para intentar recuperarse
            self.current += 1
            return None
            
        if expected_value and token.value != expected_value:
            self.error(f"Se esperaba '{expected_value}', se encontró '{token.value}'")
            # Avanzar de todos modos para intentar recuperarse
            self.current += 1
            return None
            
        self.current += 1
        return token
    
    def error(self, message):
        """Registra un error sintáctico"""
        if self.current < len(self.tokens):
            token = self.tokens[self.current]
            error = SyntaxError(message, token.line, token.column)
        else:
            # Si estamos al final del archivo
            if self.tokens:
                last_token = self.tokens[-1]
                error = SyntaxError(message, last_token.line, last_token.column + len(last_token.value))
            else:
                error = SyntaxError(message, 1, 1)
        self.errors.append(error)
    
    def match(self, token_type=None, value=None):
        """Verifica si el token actual coincide sin consumirlo"""
        token = self.current_token()
        if not token:
            return False
        if token_type and token.type != token_type:
            return False
        if value and token.value != value:
            return False
        return True
    
    def sync_to_semicolon(self):
        """Sincroniza hasta encontrar un punto y coma para recuperación de errores"""
        while self.current_token() and not self.match(TokenType.SYMBOL, ";"):
            self.current += 1
        if self.match(TokenType.SYMBOL, ";"):
            self.consume()
    
    # REGLAS GRAMATICALES - SIN VERIFICACIÓN SEMÁNTICA
    
    def program(self):
        """program -> main { statement* }"""
        first_token = self.current_token()
        node = ASTNode(ASTNodeType.PROGRAM, line=first_token.line if first_token else 1, 
                      column=first_token.column if first_token else 1)
        
        # main
        main_token = self.consume(TokenType.KEYWORD, "main")
        if not main_token:
            return node
            
        main_node = ASTNode(ASTNodeType.MAIN, "main", [], main_token.line, main_token.column)
        
        # {
        brace_token = self.consume(TokenType.SYMBOL, "{")
        if not brace_token:
            # Intentar continuar de todos modos
            pass
        
        # statements
        while self.current_token() and not self.match(TokenType.SYMBOL, "}"):
            stmt = self.statement()
            if stmt:
                main_node.children.append(stmt)
        
        # }
        closing_brace = self.consume(TokenType.SYMBOL, "}")
        if not closing_brace:
            self.error("Se esperaba '}' para cerrar el bloque main")
        
        node.children.append(main_node)
        return node
    
    def statement(self):
        """statement -> declaration | assignment | if_statement | while_statement | 
                       do_until_statement | input_statement | output_statement | 
                       increment_decrement"""
        
        token = self.current_token()
        if not token:
            return None
        
        # Skip any extra semicolons
        if token.type == TokenType.SYMBOL and token.value == ";":
            self.consume()
            return self.statement()
            
        # Declaraciones
        if token.type == TokenType.KEYWORD and token.value in ["int", "float", "string"]:
            return self.declaration()
            
        # Estructuras de control
        elif token.type == TokenType.KEYWORD:
            if token.value == "if":
                return self.if_statement()
            elif token.value == "while":
                return self.while_statement()
            elif token.value == "do":
                return self.do_until_statement()
            elif token.value == "cin":
                return self.input_statement()
            elif token.value == "cout":
                return self.output_statement()
                
        # Asignación o expresión
        elif token.type == TokenType.IDENTIFIER:
            # NO verificar si la variable está declarada - eso es semántico
            
            # Mirar adelante para ver si es asignación o incremento/decremento
            next_token = self.peek()
            if next_token and next_token.type == TokenType.ASSIGNMENT:
                return self.assignment()
            elif next_token and next_token.type == TokenType.ARITHMETIC_OP and next_token.value in ["++", "--"]:
                return self.increment_decrement()
            else:
                # Si no es asignación ni incremento, es un error sintáctico
                self.error(f"Sentencia inválida comenzando con '{token.value}'")
                self.sync_to_semicolon()
                return None
                
        else:
            self.error(f"Token inesperado al inicio de sentencia: {token.value}")
            self.current += 1
            return None
    
    def declaration(self):
        """declaration -> type identifier (, identifier)* ;"""
        type_token = self.consume()
        if not type_token:
            return None
            
        node = ASTNode(ASTNodeType.DECLARATION, type_token.value, [], type_token.line, type_token.column)
        
        # Primera variable
        id_token = self.consume(TokenType.IDENTIFIER)
        if id_token:
            var_node = ASTNode(ASTNodeType.IDENTIFIER, id_token.value, [], id_token.line, id_token.column)
            node.children.append(var_node)
        else:
            self.sync_to_semicolon()
            return node
        
        # Variables adicionales
        while self.match(TokenType.SYMBOL, ","):
            comma_token = self.consume()  # Consumir ,
            id_token = self.consume(TokenType.IDENTIFIER)
            if id_token:
                var_node = ASTNode(ASTNodeType.IDENTIFIER, id_token.value, [], id_token.line, id_token.column)
                node.children.append(var_node)
        
        if not self.consume(TokenType.SYMBOL, ";"):
            self.error("Falta ';' al final de la declaración")
        
        return node
    
    def assignment(self):
        """assignment -> identifier = expression ;"""
        id_token = self.consume(TokenType.IDENTIFIER)
        if not id_token:
            return None
            
        eq_token = self.consume(TokenType.ASSIGNMENT)
        if not eq_token:
            self.sync_to_semicolon()
            return None
            
        node = ASTNode(ASTNodeType.ASSIGNMENT, "=", [], eq_token.line, eq_token.column)
        id_node = ASTNode(ASTNodeType.IDENTIFIER, id_token.value, [], id_token.line, id_token.column)
        node.children.append(id_node)
        
        expr = self.expression()
        if expr:
            node.children.append(expr)
            
        if not self.consume(TokenType.SYMBOL, ";"):
            self.error("Falta ';' al final de la asignación")
        
        return node
    
    def increment_decrement(self):
        """increment_decrement -> identifier (++ | --) ;"""
        id_token = self.consume(TokenType.IDENTIFIER)
        if not id_token:
            return None
            
        op_token = self.consume(TokenType.ARITHMETIC_OP)
        if not op_token or op_token.value not in ["++", "--"]:
            self.error("Se esperaba '++' o '--'")
            return None
            
        node = ASTNode(ASTNodeType.UNARY_OP, op_token.value, [], op_token.line, op_token.column)
        id_node = ASTNode(ASTNodeType.IDENTIFIER, id_token.value, [], id_token.line, id_token.column)
        node.children.append(id_node)
        
        if not self.consume(TokenType.SYMBOL, ";"):
            self.error("Falta ';' después del incremento/decremento")
        
        return node
    
    def if_statement(self):
        """if_statement -> if expression then statement* (else statement*)? end"""
        if_token = self.consume(TokenType.KEYWORD, "if")
        if not if_token:
            return None
            
        node = ASTNode(ASTNodeType.IF_STATEMENT, "if", [], if_token.line, if_token.column)
        
        # Verificar si la condición tiene paréntesis (advertencia)
        has_parens = self.match(TokenType.SYMBOL, "(")
        if has_parens:
            self.consume()  # Consumir (
            condition = self.expression()
            if not self.consume(TokenType.SYMBOL, ")"):
                self.error("Falta ')' para cerrar la condición")
        else:
            # Sin paréntesis - generar advertencia pero continuar
            self.error("La condición del if debería estar entre paréntesis")
            condition = self.expression()
        
        if condition:
            node.children.append(condition)
            
        # then
        then_token = self.current_token()
        if not self.match(TokenType.IDENTIFIER, "then"):
            self.error("Se esperaba 'then' después de la condición del if")
        else:
            self.consume()
        
        # Bloque then
        then_block = ASTNode(ASTNodeType.BLOCK, "then", [], 
                            then_token.line if then_token else if_token.line, 
                            then_token.column if then_token else if_token.column)
        while self.current_token() and not self.match(TokenType.KEYWORD, "else") and not self.match(TokenType.KEYWORD, "end"):
            stmt = self.statement()
            if stmt:
                then_block.children.append(stmt)
        node.children.append(then_block)
        
        # else opcional
        if self.match(TokenType.KEYWORD, "else"):
            else_token = self.consume()
            else_block = ASTNode(ASTNodeType.BLOCK, "else", [], else_token.line, else_token.column)
            
            while self.current_token() and not self.match(TokenType.KEYWORD, "end"):
                stmt = self.statement()
                if stmt:
                    else_block.children.append(stmt)
            node.children.append(else_block)
        
        # end
        if not self.consume(TokenType.KEYWORD, "end"):
            self.error("Falta 'end' para cerrar el bloque if")
        
        return node
    
    def while_statement(self):
        """while_statement -> while expression statement* end"""
        while_token = self.consume(TokenType.KEYWORD, "while")
        if not while_token:
            return None
            
        node = ASTNode(ASTNodeType.WHILE_STATEMENT, "while", [], while_token.line, while_token.column)
        
        # Verificar si la condición tiene paréntesis (advertencia)
        has_parens = self.match(TokenType.SYMBOL, "(")
        if has_parens:
            self.consume()  # Consumir (
            condition = self.expression()
            if not self.consume(TokenType.SYMBOL, ")"):
                self.error("Falta ')' para cerrar la condición")
        else:
            # Sin paréntesis - generar advertencia pero continuar
            self.error("La condición del while debería estar entre paréntesis")
            condition = self.expression()
        
        if condition:
            node.children.append(condition)
        
        # Cuerpo
        body_block = ASTNode(ASTNodeType.BLOCK, "body", [], while_token.line, while_token.column)
        while self.current_token() and not self.match(TokenType.KEYWORD, "end"):
            stmt = self.statement()
            if stmt:
                body_block.children.append(stmt)
        
        node.children.append(body_block)
        
        # end
        if not self.consume(TokenType.KEYWORD, "end"):
            self.error("Falta 'end' para cerrar el bloque while")
        
        return node
    
    def do_until_statement(self):
        """do_until_statement -> do statement* until expression ;?"""
        do_token = self.consume(TokenType.KEYWORD, "do")
        if not do_token:
            return None
            
        node = ASTNode(ASTNodeType.DO_UNTIL_STATEMENT, "do-until", [], do_token.line, do_token.column)
        
        # Marcar que estamos dentro de un do-until
        self.in_do_until = True
        
        # Cuerpo
        body_block = ASTNode(ASTNodeType.BLOCK, "body", [], do_token.line, do_token.column)
        while self.current_token() and not self.match(TokenType.IDENTIFIER, "until"):
            stmt = self.statement()
            if stmt:
                body_block.children.append(stmt)
        
        node.children.append(body_block)
        
        # until
        until_token = self.current_token()
        if not self.match(TokenType.IDENTIFIER, "until"):
            self.error("Se esperaba 'until' para cerrar el bloque do")
            # Salir del modo do-until
            self.in_do_until = False
            return node
        else:
            until_token = self.consume()
        
        # Salir del modo do-until
        self.in_do_until = False
        
        # Verificar si la condición tiene paréntesis (advertencia)
        has_parens = self.match(TokenType.SYMBOL, "(")
        if has_parens:
            self.consume()  # Consumir (
            condition = self.expression()
            if not self.consume(TokenType.SYMBOL, ")"):
                self.error("Falta ')' para cerrar la condición")
        else:
            # Sin paréntesis - generar advertencia pero continuar
            self.error("La condición del until debería estar entre paréntesis")
            condition = self.expression()
        
        if condition:
            node.children.append(condition)
        
        # El punto y coma después de until es opcional en tu gramática
        if self.match(TokenType.SYMBOL, ";"):
            self.consume()
            
        return node
    
    def input_statement(self):
        """input_statement -> cin >> identifier ;"""
        cin_token = self.consume(TokenType.KEYWORD, "cin")
        if not cin_token:
            return None
            
        node = ASTNode(ASTNodeType.INPUT_STATEMENT, "cin", [], cin_token.line, cin_token.column)
        
        if not self.consume(TokenType.BITWISE_OP, ">>"):
            self.sync_to_semicolon()
            return node
        
        id_token = self.consume(TokenType.IDENTIFIER)
        if id_token:
            id_node = ASTNode(ASTNodeType.IDENTIFIER, id_token.value, [], id_token.line, id_token.column)
            node.children.append(id_node)
        
        if not self.consume(TokenType.SYMBOL, ";"):
            self.error("Falta ';' al final de la sentencia cin")
        
        return node
    
    def output_statement(self):
        """output_statement -> cout << expression ;"""
        cout_token = self.consume(TokenType.KEYWORD, "cout")
        if not cout_token:
            return None
            
        node = ASTNode(ASTNodeType.OUTPUT_STATEMENT, "cout", [], cout_token.line, cout_token.column)
        
        if not self.consume(TokenType.BITWISE_OP, "<<"):
            self.sync_to_semicolon()
            return node
        
        expr = self.expression()
        if expr:
            node.children.append(expr)
        
        if not self.consume(TokenType.SYMBOL, ";"):
            self.error("Falta ';' al final de la sentencia cout")
        
        return node
    
    def expression(self):
        """expression -> logical_or_expression"""
        return self.logical_or_expression()
    
    def logical_or_expression(self):
        """logical_or_expression -> logical_and_expression (|| logical_and_expression)*"""
        left = self.logical_and_expression()
        
        while self.match(TokenType.LOGICAL_OP, "||"):
            op_token = self.consume()
            right = self.logical_and_expression()
            if right:
                left = ASTNode(ASTNodeType.BINARY_OP, op_token.value, [left, right], op_token.line, op_token.column)
                
        return left
    
    def logical_and_expression(self):
        """logical_and_expression -> relational_expression (&& relational_expression)*"""
        left = self.relational_expression()
        
        while self.match(TokenType.LOGICAL_OP, "&&"):
            op_token = self.consume()
            right = self.relational_expression()
            if right:
                left = ASTNode(ASTNodeType.BINARY_OP, op_token.value, [left, right], op_token.line, op_token.column)
                
        return left
    
    def relational_expression(self):
        """relational_expression -> additive_expression ((< | <= | > | >= | == | !=) additive_expression)*"""
        left = self.additive_expression()
        
        while self.match(TokenType.RELATIONAL_OP):
            op_token = self.consume()
            right = self.additive_expression()
            if right:
                left = ASTNode(ASTNodeType.BINARY_OP, op_token.value, [left, right], op_token.line, op_token.column)
                
        return left
    
    def additive_expression(self):
        """additive_expression -> multiplicative_expression ((+ | -) multiplicative_expression)*"""
        left = self.multiplicative_expression()
        
        while self.current_token() and self.current_token().type == TokenType.ARITHMETIC_OP and self.current_token().value in ["+", "-"]:
            op_token = self.consume()
            right = self.multiplicative_expression()
            if right:
                left = ASTNode(ASTNodeType.BINARY_OP, op_token.value, [left, right], op_token.line, op_token.column)
                
        return left
    
    def multiplicative_expression(self):
        """multiplicative_expression -> unary_expression ((* | / | %) unary_expression)*"""
        left = self.unary_expression()
        
        while self.current_token() and self.current_token().type == TokenType.ARITHMETIC_OP and self.current_token().value in ["*", "/", "%"]:
            op_token = self.consume()
            right = self.unary_expression()
            if right:
                left = ASTNode(ASTNodeType.BINARY_OP, op_token.value, [left, right], op_token.line, op_token.column)
                
        return left
    
    def unary_expression(self):
        """unary_expression -> (! | -) unary_expression | primary_expression"""
        token = self.current_token()
        
        if token and ((token.type == TokenType.LOGICAL_OP and token.value == "!") or 
                     (token.type == TokenType.ARITHMETIC_OP and token.value == "-")):
            op_token = self.consume()
            expr = self.unary_expression()
            if expr:
                return ASTNode(ASTNodeType.UNARY_OP, op_token.value, [expr], op_token.line, op_token.column)
        
        return self.primary_expression()
    
    def primary_expression(self):
        """primary_expression -> identifier | number | string | true | false | ( expression )"""
        token = self.current_token()
        
        if not token:
            self.error("Se esperaba una expresión")
            return None
            
        # Identificador
        if token.type == TokenType.IDENTIFIER:
            # Verificar si es un valor booleano
            if token.value in ["true", "false"]:
                bool_token = self.consume()
                return ASTNode(ASTNodeType.BOOLEAN, bool_token.value, [], bool_token.line, bool_token.column)
            else:
                id_token = self.consume()
                return ASTNode(ASTNodeType.IDENTIFIER, id_token.value, [], id_token.line, id_token.column)
        
        # Número
        elif token.type == TokenType.NUMBER:
            num_token = self.consume()
            return ASTNode(ASTNodeType.NUMBER, num_token.value, [], num_token.line, num_token.column)
        
        # String
        elif token.type == TokenType.STRING:
            str_token = self.consume()
            return ASTNode(ASTNodeType.STRING, str_token.value, [], str_token.line, str_token.column)
        
        # Expresión entre paréntesis
        elif token.type == TokenType.SYMBOL and token.value == "(":
            lparen = self.consume()
            expr = self.expression()
            if not self.consume(TokenType.SYMBOL, ")"):
                self.error("Falta ')' para cerrar la expresión")
            return expr
        
        else:
            self.error(f"Token inesperado en expresión: '{token.value}'")
            self.current += 1
            return None

def format_ast_tree(node, indent=0):
    """Formatea el AST para impresión legible - INCLUYE COLUMNAS"""
    if not node:
        return ""
    
    result = "  " * indent + f"{node.type.name}"
    if node.value:
        result += f" [{node.value}]"
    if node.line and node.column:
        result += f" (línea {node.line}, col {node.column})"
    elif node.line:
        result += f" (línea {node.line})"
    result += "\n"
    
    for child in node.children:
        if child:  # Saltar nodos None
            result += format_ast_tree(child, indent + 1)
    
    return result

def ast_to_html(node):
    """Convierte el AST a HTML colapsable"""
    if not node:
        return ""

    html = '<div class="ast-node">'  # nodo completo

    # Etiqueta clickeable
    html += '<div class="ast-label">'
    html += f'<span class="node-type">{node.type.name}</span>'
    
    if node.value:
        html += f' <span class="node-value">[{node.value}]</span>'

    if node.line is not None and node.column is not None:
        html += f' <span class="node-position">(línea {node.line}, col {node.column})</span>'
    elif node.line:
        html += f' <span class="node-position">(línea {node.line})</span>'

    html += '</div>'  # cierra ast-label

    # Hijos
    if node.children:
        html += '<div class="ast-children">'
        for child in node.children:
            html += ast_to_html(child)
        html += '</div>'  # cierra ast-children

    html += '</div>'  # cierra ast-node
    return html

def export_ast_graphviz(ast, filename="ast", output_format="png"):
    dot = Digraph(comment="AST", format=output_format)
    counter = [0]

    def add_nodes_edges(node, parent_id=None):
        if node is None:
            return

        node_id = f"node{counter[0]}"
        counter[0] += 1

        label = node.type.name
        if node.value:
            label += f"\\n[{node.value}]"
        if node.line is not None and node.column is not None:
            label += f"\\n(línea {node.line}, col {node.column})"

        dot.node(node_id, label)

        if parent_id:
            dot.edge(parent_id, node_id)

        for child in node.children:
            add_nodes_edges(child, node_id)

    add_nodes_edges(ast)
    dot.render(filename=filename, view=False, cleanup=True)
    return f"{filename}.{output_format}"



# Función principal para análisis sintáctico
def analyze_syntax(tokens):
    """Analiza sintácticamente una lista de tokens"""
    analyzer = SyntacticAnalyzer(tokens)
    ast, errors = analyzer.parse()
    
    return ast, errors

