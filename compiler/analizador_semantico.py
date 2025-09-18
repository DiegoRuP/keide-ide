# analizador_semantico.py
from analizador_sintactico import ASTNodeType

class SymbolTable:
    """
    Tabla de símbolos para rastrear variables y sus tipos.
    asumimos un único ámbito global dentro de 'main'.
    """
    def __init__(self):
        self.symbols = {}

    def define(self, name, symbol_type, line, column):
        """Define una nueva variable. Devuelve un error si ya existe."""
        if name in self.symbols:
            return f"Error Semántico en línea {line}, columna {column}: La variable '{name}' ya ha sido declarada."
        self.symbols[name] = {'type': symbol_type, 'line': line, 'column': column}
        return None

    def lookup(self, name):
        """Busca una variable en la tabla. Devuelve su información si la encuentra."""
        return self.symbols.get(name)

class SemanticAnalyzer:
    """
    Recorre el AST para realizar el análisis semántico.
    """
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []

    def analyze(self, node):
        """Punto de entrada para el análisis del AST."""
        self.visit(node)
        return self.errors

    def visit(self, node):
        """
        Método 'visit' genérico que delega al método específico del tipo de nodo.
        Este método también debe devolver el TIPO de la expresión que analiza.
        """
        if not node:
            return None

        method_name = f'visit_{node.type.name.lower()}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Visita genérica para nodos que no tienen una lógica específica pero tienen hijos."""
        node_type = None
        for child in node.children:
            node_type = self.visit(child)
        return node_type

    def visit_program(self, node):
        self.visit(node.children[0])

    def visit_main(self, node):
        for statement in node.children:
            self.visit(statement)

    def visit_declaration(self, node):
        var_type = node.value  # 'int', 'float', 'string'
        for var_node in node.children:
            var_name = var_node.value
            error = self.symbol_table.define(var_name, var_type, var_node.line, var_node.column)
            if error:
                self.errors.append(error)
    
    def visit_assignment(self, node):
        var_name = node.children[0].value
        var_info = self.symbol_table.lookup(var_name)

        if not var_info:
            self.errors.append(f"Error Semántico en línea {node.children[0].line}, columna {node.children[0].column}: La variable '{var_name}' no ha sido declarada.")
            return

        expected_type = var_info['type']
        expr_type = self.visit(node.children[1])

        if expr_type:
            # Reglas de compatibilidad de tipos en asignación
            if expected_type == 'float' and expr_type not in ['float', 'int']:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se puede asignar un tipo '{expr_type}' a una variable de tipo 'float'.")
            elif expected_type == 'int' and expr_type not in ['int']:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se puede asignar un tipo '{expr_type}' a una variable de tipo 'int'. Se requiere conversión explícita.")
            elif expected_type == 'string' and expr_type not in ['string']:
                 self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se puede asignar un tipo '{expr_type}' a una variable de tipo 'string'.")

    def visit_identifier(self, node):
        var_name = node.value
        var_info = self.symbol_table.lookup(var_name)
        if not var_info:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: La variable '{var_name}' no ha sido declarada.")
            return "error_type"
        return var_info['type']

    def visit_number(self, node):
        if '.' in node.value:
            return 'float'
        return 'int'

    def visit_string(self, node):
        return 'string'
    
    def visit_boolean(self, node):
        return 'boolean'

    def visit_binary_op(self, node):
        left_type = self.visit(node.children[0])
        right_type = self.visit(node.children[1])
        op = node.value

        if left_type == "error_type" or right_type == "error_type":
            return "error_type"

        # Operadores aritméticos
        if op in ['-', '*', '/', '%']:
            if left_type not in ['int', 'float'] or right_type not in ['int', 'float']:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: El operador '{op}' solo se puede usar con tipos numéricos. Se encontraron '{left_type}' y '{right_type}'.")
                return "error_type"
            if left_type == 'float' or right_type == 'float':
                return 'float'
            return 'int'
        
        # Operador de suma (aritmético o concatenación)
        if op == '+':
            if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                if left_type == 'float' or right_type == 'float':
                    return 'float'
                return 'int'
            elif left_type == 'string' and right_type == 'string':
                return 'string'
            else:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: El operador '+' no es compatible entre los tipos '{left_type}' y '{right_type}'.")
                return "error_type"

        # Operadores relacionales
        if op in ['<', '<=', '>', '>=', '==', '!=']:
            if left_type not in ['int', 'float'] or right_type not in ['int', 'float']:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se pueden comparar los tipos '{left_type}' y '{right_type}' con el operador '{op}'.")
                return "error_type"
            return 'boolean' 

        # Operadores lógicos
        if op in ['&&', '||']:
            if left_type not in ['int', 'float', 'boolean'] or right_type not in ['int', 'float', 'boolean']:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: El operador lógico '{op}' requiere operandos que se puedan evaluar como booleanos. Se encontraron '{left_type}' y '{right_type}'.")
                return "error_type"
            return 'boolean'
        
        return "error_type"

    def visit_unary_op(self, node):
        op = node.value
        expr_type = self.visit(node.children[0])

        if expr_type == "error_type":
            return "error_type"
            
        if op == '!' and expr_type not in ['int', 'float', 'boolean']:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: El operador '!' solo puede aplicarse a expresiones booleanas o numéricas.")
            return "error_type"
        
        if op == '-' and expr_type not in ['int', 'float']:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: El operador unario '-' solo puede aplicarse a números.")
            return "error_type"
        
        return expr_type

    def check_condition(self, node, construct_name):
        """Función auxiliar para verificar condiciones en if/while/until."""
        condition_type = self.visit(node)
        if condition_type not in ['int', 'float', 'boolean']:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: La condición de un '{construct_name}' debe ser de tipo numérico o booleano, pero se encontró '{condition_type}'.")

    def visit_if_statement(self, node):
        condition_node = node.children[0]
        self.check_condition(condition_node, "if")
        
        # Visitar el bloque 'then'
        self.visit(node.children[1])
        
        # Si hay un bloque 'else', visitarlo
        if len(node.children) > 2:
            self.visit(node.children[2])

    def visit_while_statement(self, node):
        condition_node = node.children[0]
        self.check_condition(condition_node, "while")
        self.visit(node.children[1]) # Visitar el cuerpo del bucle

    def visit_do_until_statement(self, node):
        self.visit(node.children[0]) # Visitar el cuerpo del bucle
        condition_node = node.children[1]
        self.check_condition(condition_node, "do-until")

    def visit_input_statement(self, node):
        var_node = node.children[0]
        var_info = self.symbol_table.lookup(var_node.value)
        if not var_info:
            self.errors.append(f"Error Semántico en línea {var_node.line}, columna {var_node.column}: La variable '{var_node.value}' no ha sido declarada y no se puede usar en 'cin'.")

    def visit_output_statement(self, node):
        # La expresión en cout puede ser de cualquier tipo, solo necesitamos verificar que sea válida.
        # Al visitarla, se agregarán errores si la expresión es incorrecta.
        self.visit(node.children[0])