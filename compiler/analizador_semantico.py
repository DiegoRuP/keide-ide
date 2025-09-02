# analizador_semantico.py
from enum import Enum, auto
from analizador_sintactico import ASTNodeType

# --- Paso 1: Definir los Tipos de Datos del Lenguaje ---
# Usamos un Enum para evitar errores de tipeo con strings.
class Tipo(Enum):
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()
    VOID = auto()      # Para sentencias que no devuelven valor
    ERROR = auto()     # Para representar un error de tipo

# --- Paso 2: Crear una Clase para los Errores Semánticos ---
class SemanticError(Exception):
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
    
    def __str__(self):
        if self.line and self.column:
            return f"Error Semántico en línea {self.line}, columna {self.column}: {self.message}"
        return f"Error Semántico: {self.message}"

# --- Paso 3: Implementar la Tabla de Símbolos ---
class SymbolTable:
    """
    Gestiona los ámbitos (scopes) y los símbolos (variables).
    Usa una pila de diccionarios para manejar los ámbitos.
    """
    def __init__(self):
        self.scope_stack = [{}]  # Inicia con el ámbito global

    def enter_scope(self):
        """Entra a un nuevo ámbito (ej. un bloque if, while, o función)."""
        self.scope_stack.append({})

    def exit_scope(self):
        """Sale del ámbito actual."""
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def insert(self, name, symbol_type):
        """
        Inserta un nuevo símbolo en el ámbito actual.
        Lanza un error si el símbolo ya existe en este ámbito.
        """
        current_scope = self.scope_stack[-1]
        if name in current_scope:
            raise SemanticError(f"La variable '{name}' ya ha sido declarada en este ámbito.")
        current_scope[name] = symbol_type

    def lookup(self, name):
        """
        Busca un símbolo desde el ámbito actual hacia afuera.
        Devuelve el tipo del símbolo si lo encuentra, de lo contrario None.
        """
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

# --- Paso 4: Crear el Analizador Semántico con el Patrón Visitante ---
class SemanticAnalyzer:
    """
    Recorre el AST generado por el analizador sintáctico y verifica las reglas semánticas.
    """
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []

    def analyze(self, ast):
        """Punto de entrada para el análisis."""
        try:
            self.visit(ast)
        except Exception as e:
            self.errors.append(str(e))
        return self.errors

    def visit(self, node):
        """Método despachador que llama al visitante correcto según el tipo de nodo."""
        method_name = f'visit_{node.type.name}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Visitante genérico para nodos que no necesitan lógica especial."""
        for child in node.children:
            self.visit(child)
        return Tipo.VOID # Las sentencias no devuelven valor

    # --- Visitantes para Nodos Específicos del AST ---

    def visit_MAIN(self, node):
        self.symbol_table.enter_scope()
        self.visit(node.children[0]) # Visita el bloque de sentencias
        self.symbol_table.exit_scope()

    def visit_BLOCK(self, node):
        for statement in node.children:
            self.visit(statement)

    def visit_DECLARATION(self, node):
        # El valor del nodo es el tipo ej int
        var_type_str = node.value
        
        # Mapeamos el string del tipo a nuestro Enum
        type_map = {"int": Tipo.INT, "float": Tipo.FLOAT, "string": Tipo.STRING}
        var_type = type_map.get(var_type_str)

        for var_node in node.children:
            var_name = var_node.value
            try:
                self.symbol_table.insert(var_name, var_type)
                # anotar el tipo en el nodo del AST
                var_node.data_type = var_type 
            except SemanticError as e:
                self.errors.append(str(SemanticError(e.message, var_node.line, var_node.column)))

    def visit_ASSIGNMENT(self, node):
        var_node = node.children[0]
        expr_node = node.children[1]
        var_name = var_node.value

        # 1. Verificar que la variable esté declarada
        var_type = self.symbol_table.lookup(var_name)
        if not var_type:
            self.errors.append(str(SemanticError(f"Asignación a variable no declarada '{var_name}'.", var_node.line, var_node.column)))
            return

        # 2. Obtener el tipo de la expresión
        expr_type = self.visit(expr_node)
        
        # 3. Verificar la compatibilidad de tipos
        if var_type == expr_type:
            return # Tipos iguales, todo bien
        if var_type == Tipo.FLOAT and expr_type == Tipo.INT:
            return # Permitir promoción (asignar int a float)
        
        if expr_type != Tipo.ERROR: # No mostrar error de tipo si la expresión ya tuvo uno
            self.errors.append(str(SemanticError(f"Incompatibilidad de tipos en la asignación a '{var_name}'. Se esperaba '{var_type.name}' pero se obtuvo '{expr_type.name}'.", node.line, node.column)))

    def visit_BINARY_OP(self, node):
        left_type = self.visit(node.children[0])
        right_type = self.visit(node.children[1])
        op = node.value

        if op in ['+', '-', '*', '/']:
            if left_type in [Tipo.INT, Tipo.FLOAT] and right_type in [Tipo.INT, Tipo.FLOAT]:
                # Promoción de tipo: si uno es FLOAT, el resultado es FLOAT
                return Tipo.FLOAT if left_type == Tipo.FLOAT or right_type == Tipo.FLOAT else Tipo.INT
            else:
                self.errors.append(str(SemanticError(f"Operación aritmética '{op}' inválida entre los tipos '{left_type.name}' y '{right_type.name}'.", node.line, node.column)))
                return Tipo.ERROR

        if op == '%':
            if left_type == Tipo.INT and right_type == Tipo.INT:
                return Tipo.INT
            else:
                self.errors.append(str(SemanticError(f"Operador '%' solo es válido entre enteros.", node.line, node.column)))
                return Tipo.ERROR

        if op in ['<', '<=', '>', '>=', '==', '!=']:
            if (left_type in [Tipo.INT, Tipo.FLOAT] and right_type in [Tipo.INT, Tipo.FLOAT]) or (left_type == right_type):
                return Tipo.BOOLEAN
            else:
                self.errors.append(str(SemanticError(f"No se puede comparar '{left_type.name}' con '{right_type.name}'.", node.line, node.column)))
                return Tipo.ERROR

        if op in ['&&', '||']:
            if left_type == Tipo.BOOLEAN and right_type == Tipo.BOOLEAN:
                return Tipo.BOOLEAN
            else:
                self.errors.append(str(SemanticError(f"Operador lógico '{op}' requiere operandos booleanos.", node.line, node.column)))
                return Tipo.ERROR
        
        return Tipo.ERROR

    def visit_UNARY_OP(self, node):
        op = node.value
        expr_type = self.visit(node.children[0])

        if op == '-' and expr_type in [Tipo.INT, Tipo.FLOAT]:
            return expr_type
        if op == '!' and expr_type == Tipo.BOOLEAN:
            return Tipo.BOOLEAN
        
        self.errors.append(str(SemanticError(f"Operador unario '{op}' inválido para el tipo '{expr_type.name}'.", node.line, node.column)))
        return Tipo.ERROR

    def visit_IF_STATEMENT(self, node):
        condition_node = node.children[0]
        condition_type = self.visit(condition_node)

        if condition_type != Tipo.BOOLEAN:
            self.errors.append(str(SemanticError(f"La condición del 'if' debe ser booleana, no '{condition_type.name}'.", condition_node.line, condition_node.column)))
        
        # Visitar los bloques 'then' y 'else' (si existe)
        for block_node in node.children[1:]:
             self.visit(block_node)

    def visit_WHILE_STATEMENT(self, node):
        condition_node = node.children[0]
        condition_type = self.visit(condition_node)

        if condition_type != Tipo.BOOLEAN:
            self.errors.append(str(SemanticError(f"La condición del 'while' debe ser booleana, no '{condition_type.name}'.", condition_node.line, condition_node.column)))
        
        self.visit(node.children[1]) # Visitar el cuerpo del bucle

    def visit_DO_UNTIL_STATEMENT(self, node):
        self.visit(node.children[0]) # Visitar el cuerpo del bucle
        
        condition_node = node.children[1]
        condition_type = self.visit(condition_node)

        if condition_type != Tipo.BOOLEAN:
            self.errors.append(str(SemanticError(f"La condición del 'do-until' debe ser booleana, no '{condition_type.name}'.", condition_node.line, condition_node.column)))
            
    def visit_INPUT_STATEMENT(self, node):
        var_node = node.children[0]
        var_name = var_node.value
        var_type = self.symbol_table.lookup(var_name)
        if not var_type:
            self.errors.append(str(SemanticError(f"La variable '{var_name}' en 'cin' no ha sido declarada.", var_node.line, var_node.column)))

    def visit_OUTPUT_STATEMENT(self, node):
        # Simplemente visitamos la expresión para verificar que no tenga errores internos
        self.visit(node.children[0])

    def visit_IDENTIFIER(self, node):
        var_name = node.value
        var_type = self.symbol_table.lookup(var_name)
        if var_type is None:
            self.errors.append(str(SemanticError(f"Uso de la variable no declarada '{var_name}'.", node.line, node.column)))
            return Tipo.ERROR
        node.data_type = var_type # Anotamos el tipo en el nodo
        return var_type

    def visit_NUMBER(self, node):
        return Tipo.FLOAT if '.' in node.value else Tipo.INT

    def visit_STRING(self, node):
        return Tipo.STRING

    def visit_BOOLEAN(self, node):
        return Tipo.BOOLEAN