# analizador_semantico.py
from platform import node
from analizador_sintactico import ASTNodeType

class SymbolTable:
    """
    Tabla de símbolos para rastrear variables y sus tipos.
    asumimos un único ámbito global dentro de 'main'.
    """
    def __init__(self):
        # La pila de ámbitos. El primero es siempre el ámbito global.
        self.scopes = [{'__name__': 'global'}]
        # Historial de ámbitos
        self.scope_history = [{'__name__': 'global'}]

    def enter_scope(self, base_name):
        parent_scope_name = self.scopes[-1]['__name__']
        
        if parent_scope_name == 'global':
            new_scope_name = base_name
        else:
            new_scope_name = f"{parent_scope_name},{base_name}"
        
        new_scope = {'__name__': new_scope_name}
        self.scopes.append(new_scope)
        self.scope_history.append(new_scope)

    def exit_scope(self):
        """Sale del ámbito actual."""
        if len(self.scopes) > 1:
            self.scopes.pop()


    def define(self, name, symbol_type, line, column, extra_info=None):
        """Define un nuevo símbolo en el ámbito ACTUAL."""
        current_scope_for_history = self.scope_history[-1]
        current_scope_for_lookup = self.scopes[-1]
        
        if name in current_scope_for_lookup:
            return (f"Error Semántico en línea {line}, columna {column}: "
                    f"El símbolo '{name}' ya ha sido declarado en el ámbito '{current_scope_for_lookup['__name__']}'.")
        
        symbol_info = {'type': symbol_type, 'line': line, 'column': column}
        
        if extra_info:
            symbol_info.update(extra_info) # Para 'value', 'param_types', etc.
        
        current_scope_for_lookup[name] = symbol_info
        current_scope_for_history[name] = symbol_info
        
        return None

    def lookup(self, name):
        """Busca un símbolo desde el ámbito actual hacia el global."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def to_dict(self):
        """Convierte la tabla de símbolos a un diccionario para fácil visualización."""
        return self.scope_history

class SemanticAnalyzer:
    """
    Recorre el AST para realizar el análisis semántico Y
    ANOTAR los nodos con información semántica.
    """
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        # Rastrear la función actual para validar 'return'
        self.current_function_return_type = None

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
        node_type = None
        for child in node.children:
            node_type = self.visit(child)
        return node_type

    def visit_program(self, node):
        for child in node.children:
            self.visit(child)

    def visit_main(self, node):
        # Main es como una función que retorna 'int'
        self.current_function_return_type = 'int'
        
        self.symbol_table.enter_scope('main')
        node.scope = self.get_current_scope_name()
        
        for statement in node.children:
            self.visit(statement)
        self.symbol_table.exit_scope()
        
        self.current_function_return_type = None # Salir de la "función" main
        
    def visit_function_declaration(self, node):
        func_name = node.value
        return_type_node = node.children[0]
        return_type = return_type_node.value

        # --- Preparar info de parámetros ANTES de definir la función ---
        param_list_node = node.children[1]
        param_types = []
        for param_node in param_list_node.children:
            # Anotamos el tipo del parámetro (ej. 'int')
            param_types.append(param_node.children[0].value)
        # --- FIN ---

        func_info = {
            'param_types': param_types,
            'return_type': return_type
        }
        
        # Definir la función en el ámbito actual (global)
        error = self.symbol_table.define(func_name, f"function", node.line, node.column, extra_info=func_info)
        if error:
            self.errors.append(error)

        node.scope = self.get_current_scope_name()
        node.data_type = return_type # El tipo del nodo es su tipo de retorno
        node.state = 'declarado'

        # Gestionar el 'return'
        self.current_function_return_type = return_type
        
        # Entrar en el ámbito de la función
        self.symbol_table.enter_scope(func_name)
        
        # Visitar (y definir) los parámetros dentro del nuevo ámbito
        self.visit(param_list_node)
        
        # Visitar el cuerpo
        if len(node.children) > 2:
            body_node = node.children[2]
            self.visit(body_node)

        self.symbol_table.exit_scope()
        
        self.current_function_return_type = None # Salir de la función
        
    def visit_parameter_list(self, node):
        """Recorre cada nodo de parámetro en la lista."""
        for param_node in node.children:
            self.visit(param_node)

    def visit_parameter(self, node):
        """Define un parámetro en la tabla de símbolos y lo anota."""
        param_name = node.value
        param_type_node = node.children[0]
        param_type = param_type_node.value
        
        error = self.symbol_table.define(param_name, param_type, node.line, node.column)
        if error:
            self.errors.append(error)
        else:
            node.scope = self.get_current_scope_name()
            node.data_type = param_type
            node.state = 'declarado'

    def visit_declaration(self, node):
        var_type = node.value
        current_scope = self.get_current_scope_name()
        node.scope = current_scope
        
        for child in node.children:
            
            initial_value = None
            
            var_node = child.children[0] if child.type == ASTNodeType.ASSIGNMENT else child
            var_name = var_node.value
            
            if child.type == ASTNodeType.ASSIGNMENT:
                expr_node = child.children[1]
                # Verificamos si el valor es una constante simple (número o string)
                if expr_node.type in [ASTNodeType.NUMBER, ASTNodeType.STRING]:
                    initial_value = expr_node.value
                
            error = self.symbol_table.define(var_name, var_type, var_node.line, var_node.column, extra_info={'value': initial_value})
                
            if error:
                self.errors.append(error)
            else:
                var_node.scope = current_scope
                var_node.data_type = var_type
                var_node.state = 'declarado'
                
            if child.type == ASTNodeType.ASSIGNMENT:
                child.scope = current_scope
                self.visit_assignment(child) # Visitar la asignación para comprobar tipos

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
            # Reglas de compatibilidad (int se puede asignar a float)
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
        
        # No anotar funciones como 'utilizadas' aquí
        if var_info['type'] == 'function':
            return "function_type"
        
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
            elif op == '+' and (left_type == 'string' and right_type in ['int', 'float']):
                result_type = 'string' # Permitir concatenación string + num
            elif op == '+' and (right_type == 'string' and left_type in ['int', 'float']):
                result_type = 'string' # Permitir concatenación num + string
            else:
                self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: Operador '{op}' no compatible entre tipos '{left_type}' y '{right_type}'.")
        
        elif op in ['<', '<=', '>', '>=', '==', '!=']:
            if left_type in ['int', 'float'] and right_type in ['int', 'float']:
                result_type = 'boolean'
            elif op in ['==', '!='] and left_type == 'string' and right_type == 'string':
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
        """Función auxiliar para verificar condiciones en if/while/until/for."""
        condition_type = self.visit(node)
        if condition_type not in ['int', 'float', 'boolean', 'error_type']:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: La condición de un '{construct_name}' debe ser evaluable a booleano, pero se encontró '{condition_type}'.")

    def visit_if_statement(self, node):
        self.check_condition(node.children[0], "if")
    
        self.symbol_table.enter_scope("if_block") 
        self.visit(node.children[1]) # Bloque 'then'
        self.symbol_table.exit_scope()

        if len(node.children) > 2:
            self.symbol_table.enter_scope("else_block")
            self.visit(node.children[2]) # Bloque 'else'
            self.symbol_table.exit_scope()

    def visit_while_statement(self, node):
        self.check_condition(node.children[0], "while")
        
        self.symbol_table.enter_scope("while_block")
        self.visit(node.children[1]) # Cuerpo del bucle
        self.symbol_table.exit_scope()

    def visit_do_until_statement(self, node):
        self.symbol_table.enter_scope("do_until_block")
        self.visit(node.children[0]) # Cuerpo del bucle
        self.symbol_table.exit_scope()
        
        self.check_condition(node.children[1], "do-until")

    def visit_input_statement(self, node):
        var_node = node.children[0]
        var_info = self.symbol_table.lookup(var_node.value)
        if not var_info:
            self.errors.append(f"Error Semántico en línea {var_node.line}, columna {var_node.column}: La variable '{var_node.value}' no ha sido declarada para 'cin'.")

    def visit_output_statement(self, node):
        # La expresión en cout puede ser de cualquier tipo, solo necesitamos verificar que sea válida.
        self.visit(node.children[0])
        
    def visit_switch_statement(self, node):
        condition_type = self.visit(node.children[0])
    
        if condition_type != 'int':
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: La expresión en un 'switch' debe ser de tipo 'int', no '{condition_type}'.")
            
        self.symbol_table.enter_scope('switch_block')
        
        case_labels = set()
        has_default = False
        
        for i in range(1, len(node.children)):
            case_node = node.children[i]
            
            if case_node.type == ASTNodeType.CASE_BLOCK:
                # El valor del 'case' es el 'value' del nodo CONSTANTE (número)
                case_val = case_node.value
                if case_val in case_labels:
                    self.errors.append(f"Error Semántico en línea {case_node.line}, columna {case_node.column}: Etiqueta 'case' duplicada con valor '{case_val}'.")
                case_labels.add(case_val)
            
            if case_node.type == ASTNodeType.DEFAULT_BLOCK:
                if has_default:
                    self.errors.append(f"Error Semántico en línea {case_node.line}, columna {case_node.column}: Múltiples bloques 'default' en 'switch'.")
                has_default = True

            self.visit(case_node) # Visitar el 'case' o 'default'
        
        self.symbol_table.exit_scope()

    def visit_case_block(self, node):
        # El 'case' tiene un hijo: el bloque de sentencias
        self.visit(node.children[0]) 

    def visit_default_block(self, node):
        # El 'default' tiene un hijo: el bloque de sentencias
        self.visit(node.children[0]) 
    
    def visit_for_statement(self, node):
        self.symbol_table.enter_scope('for_block')

        # Visitar nodos: 0=init, 1=condition, 2=increment, 3=body
        if node.children[0]:
            self.visit(node.children[0]) # Init (declaración o asignación)
        if node.children[1]:
            self.check_condition(node.children[1], "for") # Condición
        if node.children[2]:
            self.visit(node.children[2]) # Incremento (asignación)
        if node.children[3]:
            self.visit(node.children[3]) # Cuerpo (bloque)
            
        self.symbol_table.exit_scope()

    def visit_return_statement(self, node):
        if self.current_function_return_type is None:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: Sentencia 'return' fuera de una función.")
            return

        expected_type = self.current_function_return_type
        
        if node.value == "void_return":
             if expected_type != 'void': # Asumiendo que tendrías un tipo 'void'
                 self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: 'return' vacío en función que debe retornar '{expected_type}'.")
             return

        # Hay una expresión
        expr_type = self.visit(node.children[0])
        
        if expr_type == "error_type":
            return # Ya se reportó un error en la expresión

        # Comprobar compatibilidad
        if expected_type == 'float' and expr_type not in ['float', 'int']:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se puede retornar tipo '{expr_type}' de una función que retorna 'float'.")
        elif expected_type == 'int' and expr_type not in ['int']:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se puede retornar tipo '{expr_type}' de una función que retorna 'int'.")
        elif expected_type == 'string' and expr_type not in ['string']:
             self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: No se puede retornar tipo '{expr_type}' de una función que retorna 'string'.")

    def visit_function_call(self, node):
        func_name = node.value
        func_info = self.symbol_table.lookup(func_name)

        if not func_info:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: Intento de llamar a función no declarada '{func_name}'.")
            return "error_type"
        
        if func_info['type'] != 'function':
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: '{func_name}' no es una función, es un(a) '{func_info['type']}'.")
            return "error_type"

        # Comprobar número de argumentos (aridad)
        expected_args_count = len(func_info['param_types'])
        provided_args_count = len(node.children)

        if expected_args_count != provided_args_count:
            self.errors.append(f"Error Semántico en línea {node.line}, columna {node.column}: La función '{func_name}' esperaba {expected_args_count} argumentos, pero recibió {provided_args_count}.")
            return "error_type"
        
        # Comprobar tipos de argumentos
        for i, arg_node in enumerate(node.children):
            arg_type = self.visit(arg_node)
            expected_arg_type = func_info['param_types'][i]
            
            # Chequeo simple de compatibilidad
            if expected_arg_type == 'float' and arg_type not in ['float', 'int']:
                 self.errors.append(f"Error Semántico en línea {arg_node.line}, columna {arg_node.column}: Argumento {i+1} de '{func_name}' es '{arg_type}', se esperaba 'float' o 'int'.")
            elif expected_arg_type == 'int' and arg_type != 'int':
                 self.errors.append(f"Error Semántico en línea {arg_node.line}, columna {arg_node.column}: Argumento {i+1} de '{func_name}' es '{arg_type}', se esperaba 'int'.")
            elif expected_arg_type == 'string' and arg_type != 'string':
                 self.errors.append(f"Error Semántico en línea {arg_node.line}, columna {arg_node.column}: Argumento {i+1} de '{func_name}' es '{arg_type}', se esperaba 'string'.")

        # El tipo de la expresión 'function_call' es el tipo de retorno de la función
        node.data_type = func_info['return_type']
        return func_info['return_type']

# -----------------------------------------------------------------
# --- FUNCIÓN AUXILIAR (PARA CORREGIR EL IMPORT ERROR) ---
# -----------------------------------------------------------------
        
def semantic_tree_to_html(node):
    """
    Convierte el AST (después del análisis semántico) a HTML colapsable,
    incluyendo la información de tipos, ámbitos, etc.
    """
    if not node:
        return ""

    html = '<div class="ast-node">'
    html += '<div class="ast-label">'
    
    html += f'<span class="node-type">{node.type.name}</span>'
    if node.value:
        html += f' <span class="node-value">[{node.value}]</span>'

    # --- Añadir Información Semántica ---
    sem_info = []
    if node.data_type:
        sem_info.append(f'Tipo: {node.data_type}')
    if node.scope:
        sem_info.append(f'Ámbito: {node.scope}')
    if node.state:
        sem_info.append(f'Estado: {node.state}')
        
    if sem_info:
        html += f' <span class="sem-info">({", ".join(sem_info)})</span>'
    # --- Fin de Añadir Info Semántica ---

    html += '</div>'  # Cierra ast-label

    if node.children:
        html += '<div class="ast-children">'
        for child in node.children:
            html += semantic_tree_to_html(child)
        html += '</div>' # Cierra ast-children

    html += '</div>' # Cierra ast-node
    return html