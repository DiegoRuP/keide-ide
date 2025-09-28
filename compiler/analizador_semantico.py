# analizador_semantico.py
from analizador_sintactico import ASTNodeType

class SymbolTable:
    """
    Tabla de símbolos para rastrear variables y sus tipos.
    asumimos un único ámbito global dentro de 'main'.
    """
    def __init__(self):
        # La pila de ámbitos. El primero es siempre el ámbito global.
        self.scopes = [{'__name__': 'global'}]
        
    def enter_scope(self, name):
        """Entra en un nuevo ámbito (ej. al entrar a una función)."""
        self.scopes.append({'__name__': name})

    def exit_scope(self):
        """Sale del ámbito actual."""
        if len(self.scopes) > 1:
            self.scopes.pop()


    def define(self, name, symbol_type, line, column):
        """Define un nuevo símbolo en el ámbito ACTUAL."""
        current_scope = self.scopes[-1]
        if name in current_scope:
            return (f"Error Semántico en línea {line}, columna {column}: "
                    f"La variable '{name}' ya ha sido declarada en el ámbito '{current_scope['__name__']}'.")
        current_scope[name] = {'type': symbol_type, 'line': line, 'column': column}
        return None

    def lookup(self, name):
        """Busca un símbolo desde el ámbito actual hacia el global."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def to_dict(self):
        """Convierte la tabla de símbolos a un diccionario para fácil visualización."""
        return self.scopes

class SemanticAnalyzer:
    """
    Recorre el AST para realizar el análisis semántico Y
    ANOTAR los nodos con información semántica.
    """
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.memory_counter = 1000

    def analyze(self, node):
        self.visit(node)
        return self.errors, self.symbol_table.to_dict()

    def get_current_scope_name(self):
        return self.symbol_table.scopes[-1]['__name__']

    def visit(self, node):
        if not node:
            return None
        method_name = f'visit_{node.type.name.lower()}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for child in node.children:
            self.visit(child)
        return None

    def visit_program(self, node):
        for child in node.children:
            self.visit(child)

    def visit_main(self, node):
        self.symbol_table.enter_scope('main')
        node.scope = self.get_current_scope_name()
        for statement in node.children:
            self.visit(statement)
        self.symbol_table.exit_scope()

    def visit_function_declaration(self, node):
        func_name = node.value
        return_type = node.children[0].value
        error = self.symbol_table.define(func_name, f"function(returns {return_type})", node.line, node.column)
        if error:
            self.errors.append(error)
        
        node.scope = self.get_current_scope_name()
        node.data_type = f"function(returns {return_type})"
        node.state = 'declarado'
        node.memory_address = f"@{self.memory_counter}"
        self.memory_counter += 4

    def visit_declaration(self, node):
        var_type = node.value
        current_scope = self.get_current_scope_name()
        node.scope = current_scope
        
        for child in node.children:
            var_node = child.children[0] if child.type == ASTNodeType.ASSIGNMENT else child
            var_name = var_node.value
            error = self.symbol_table.define(var_name, var_type, var_node.line, var_node.column)
            if error:
                self.errors.append(error)
            else:
                var_node.scope = current_scope
                var_node.data_type = var_type
                var_node.state = 'declarado'
                var_node.memory_address = f"@{self.memory_counter}"
                self.memory_counter += 4
            
            if child.type == ASTNodeType.ASSIGNMENT:
                child.scope = current_scope
                self.visit_assignment(child)

    def visit_assignment(self, node):
        var_node = node.children[0]
        var_name = var_node.value
        var_info = self.symbol_table.lookup(var_name)

        if not var_info:
            self.errors.append(f"Error Semántico en línea {var_node.line}, columna {var_node.column}: La variable '{var_name}' no ha sido declarada.")
            return

        node.scope = self.get_current_scope_name()
        var_node.scope = self.get_current_scope_name()
        var_node.data_type = var_info['type']
        var_node.state = 'modificado'

        expr_type = self.visit(node.children[1])
        expected_type = var_info['type']

        if expr_type and expr_type != "error_type":
            if expected_type == 'float' and expr_type not in ['float', 'int']:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se puede asignar un tipo '{expr_type}' a una variable de tipo 'float'.")
            elif expected_type == 'int' and expr_type not in ['int']:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se puede asignar un tipo '{expr_type}' a una variable de tipo 'int'.")
            elif expected_type == 'string' and expr_type not in ['string']:
                 self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se puede asignar un tipo '{expr_type}' a una variable de tipo 'string'.")

    def visit_identifier(self, node):
        var_name = node.value
        var_info = self.symbol_table.lookup(var_name)
        if not var_info:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: La variable '{var_name}' no ha sido declarada.")
            return "error_type"
        
        node.scope = self.get_current_scope_name()
        node.data_type = var_info['type']
        node.state = 'utilizado'
        
        return var_info['type']

    def visit_number(self, node):
        node.data_type = 'float' if '.' in node.value else 'int'
        return node.data_type

    def visit_string(self, node):
        node.data_type = 'string'
        return node.data_type
    
    def visit_boolean(self, node):
        node.data_type = 'boolean'
        return node.data_type

    def visit_binary_op(self, node):
        left_type = self.visit(node.children[0])
        right_type = self.visit(node.children[1])
        op = node.value

        if left_type == "error_type" or right_type == "error_type":
            return "error_type"

        result_type = "error_type"
        if op in ['+', '-', '*', '/', '%']:
            if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                result_type = 'float' if 'float' in [left_type, right_type] else 'int'
            elif op == '+' and left_type == 'string' and right_type == 'string':
                result_type = 'string'
            else:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: Operador '{op}' no compatible entre tipos '{left_type}' y '{right_type}'.")
        
        elif op in ['<', '<=', '>', '>=', '==', '!=']:
            if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                result_type = 'boolean'
            else:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se pueden comparar los tipos '{left_type}' y '{right_type}'.")
        
        elif op in ['&&', '||']:
            if left_type in ['int', 'float', 'boolean'] and right_type in ['int', 'float', 'boolean']:
                result_type = 'boolean'
            else:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: Operador lógico '{op}' requiere operandos booleanos o numéricos.")

        node.data_type = result_type
        return result_type

    def visit_unary_op(self, node):
        expr_type = self.visit(node.children[0])
        if expr_type == "error_type":
            return "error_type"
        
        if node.value == '!' and expr_type in ['int', 'float', 'boolean']:
            node.data_type = 'boolean'
        elif node.value == '-' and expr_type in ['int', 'float']:
            node.data_type = expr_type
        else:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: Operador unario '{node.value}' inválido para el tipo '{expr_type}'.")
            node.data_type = "error_type"
        
        return node.data_type

    def check_condition(self, node, construct_name):
        condition_type = self.visit(node)
        if condition_type not in ['int', 'float', 'boolean']:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: La condición de un '{construct_name}' debe ser evaluable a booleano, pero se encontró '{condition_type}'.")

    def visit_if_statement(self, node):
        self.check_condition(node.children[0], "if")
        self.visit(node.children[1]) # Bloque then
        if len(node.children) > 2:
            self.visit(node.children[2]) # Bloque else

    def visit_while_statement(self, node):
        self.check_condition(node.children[0], "while")
        self.visit(node.children[1])

    def visit_do_until_statement(self, node):
        self.visit(node.children[0])
        self.check_condition(node.children[1], "do-until")

    def visit_input_statement(self, node):
        var_node = node.children[0]
        var_info = self.symbol_table.lookup(var_node.value)
        if not var_info:
            self.errors.append(f"Error Semántico en línea {var_node.line}, columna {var_node.column}: La variable '{var_node.value}' no ha sido declarada para 'cin'.")

    def visit_output_statement(self, node):
        self.visit(node.children[0])

        
def semantic_tree_to_html(node):
    if not node:
        return ""

    html = '<div class="ast-node">'
    html += '<div class="ast-label">'
    
    html += f'<span class="node-type">{node.type.name}</span>'
    if node.value:
        html += f' <span class="node-value">[{node.value}]</span>'

    sem_info = []
    if node.data_type:
        sem_info.append(f'Tipo: {node.data_type}')
    if node.scope:
        sem_info.append(f'Ámbito: {node.scope}')
    if node.state:
        sem_info.append(f'Estado: {node.state}')
    if node.memory_address:
        sem_info.append(f'Mem: {node.memory_address}')

    if sem_info:
        html += f' <span class="sem-info">({", ".join(sem_info)})</span>'

    html += '</div>'  

    if node.children:
        html += '<div class="ast-children">'
        for child in node.children:
            html += semantic_tree_to_html(child)
        html += '</div>'

    html += '</div>'
    return html