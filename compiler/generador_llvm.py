# generador_llvm.py
from llvmlite import ir
from analizador_sintactico import ASTNodeType
from llvmlite import binding as llvm
import sys
import traceback

class CodeGenerator:
    """
    Esta clase recorre el Árbol de Sintaxis Abstracta (AST) que nos dio
    el analizador sintáctico y lo traduce a Código Intermedio de LLVM (LLVM IR).
    """
    
    def __init__(self):
        
        # --- Configuración Inicial de LLVM ---
        target_triple = llvm.get_default_triple()
        self.module = ir.Module(name="mi_programa")
        self.module.triple = target_triple
        
        # --- Estado de generación ---
        self.builder = None
        self.local_symbol_table = {}
        self.current_function = None 
        
        self.function_symbol_table = {}
        
        self.string_counter = 0 

        # --- Declaración de Funciones Externas (de C) ---
        printf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")
        
        scanf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_type, name="scanf")
        
        # --- Variables Globales (para las cadenas de formato) ---
        fmt_int_val = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray("%d\n\00".encode("utf8")))
        self.format_int = ir.GlobalVariable(self.module, fmt_int_val.type, name="fmt_int")
        self.format_int.initializer = fmt_int_val
        self.format_int.global_constant = True
        
        fmt_float_val = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray("%f\n\00".encode("utf8")))
        self.format_float = ir.GlobalVariable(self.module, fmt_float_val.type, name="fmt_float")
        self.format_float.initializer = fmt_float_val
        self.format_float.global_constant = True
        
        fmt_str_val = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray("%s\n\00".encode("utf8")))
        self.format_str = ir.GlobalVariable(self.module, fmt_str_val.type, name="fmt_str")
        self.format_str.initializer = fmt_str_val
        self.format_str.global_constant = True
        
        scan_int_val = ir.Constant(ir.ArrayType(ir.IntType(8), 3), bytearray("%d\00".encode("utf8")))
        self.scan_int = ir.GlobalVariable(self.module, scan_int_val.type, name="scan_int")
        self.scan_int.initializer = scan_int_val
        self.scan_int.global_constant = True

        scan_float_val = ir.Constant(ir.ArrayType(ir.IntType(8), 3), bytearray("%f\00".encode("utf8")))
        self.scan_float = ir.GlobalVariable(self.module, scan_float_val.type, name="scan_float")
        self.scan_float.initializer = scan_float_val
        self.scan_float.global_constant = True
        
        # --- Tipos LLVM ---
        self.types = {
            'int': ir.IntType(32),
            'float': ir.FloatType(),
            'string': ir.IntType(8).as_pointer(),
            'boolean': ir.IntType(1),
            'void': ir.VoidType()
        }

    def get_llvm_type(self, type_str):
        """Función auxiliar para mapear tipos de nuestro lenguaje a tipos de LLVM."""
        return self.types.get(type_str, ir.VoidType())

    def generate(self, node):
        """Punto de entrada principal. Inicia el recorrido del AST."""
        module_str = ""
        try:
            self.visit(node)
            module_str = str(self.module)
            
            llvm.initialize_native_target()
            llvm.initialize_native_asmprinter()
            
            llvm_module = llvm.parse_assembly(module_str)
            llvm_module.verify()
            
            return module_str
            
        except Exception as e:
            print("--- ERROR DE VERIFICACIÓN DE LLVM ---", file=sys.stderr)
            print(f"Error: {str(e)}", file=sys.stderr)
            
            print("\n--- TRACEBACK DE PYTHON ---", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            
            print("\n--- CÓDIGO LLVM GENERADO (CON ERROR) ---", file=sys.stderr)
            print(module_str, file=sys.stderr)
            print("---------------------------------------", file=sys.stderr)
            
            raise e

    # --- Motor del Patrón Visitor ---
    
    def visit(self, node):
        if not node:
            return None
        
        method_name = f'visit_{node.type.name.lower()}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Visitante genérico: solo visita a todos los hijos del nodo."""
        for child in node.children:
            self.visit(child)
        # No debe devolver nada

    # --- Funciones Auxiliares de Conversión ---

    def _to_boolean(self, value):
        """Convierte un valor (int, float) a un booleano LLVM (i1)."""
        if isinstance(value.type, ir.FloatType):
            return self.builder.fcmp_ordered('!=', value, ir.Constant(ir.FloatType(), 0.0), name="float_to_bool")
        elif isinstance(value.type, ir.IntType):
            return self.builder.icmp_signed('!=', value, ir.Constant(value.type, 0), name="int_to_bool")
        elif value.type == self.types['boolean']:
            return value
        
        raise TypeError(f"No se puede convertir {value.type} a booleano")

    def _promote_types(self, left_val, right_val):
        """
        Promueve int a float si uno de los operandos es float.
        Retorna (left, right, is_float)
        """
        is_float = False
        
        if isinstance(left_val.type, ir.FloatType) and isinstance(right_val.type, ir.IntType):
            right_val = self.builder.sitofp(right_val, ir.FloatType(), name="int_to_float")
            is_float = True
        elif isinstance(left_val.type, ir.IntType) and isinstance(right_val.type, ir.FloatType):
            left_val = self.builder.sitofp(left_val, ir.FloatType(), name="int_to_float")
            is_float = True
        elif isinstance(left_val.type, ir.FloatType) and isinstance(right_val.type, ir.FloatType):
            is_float = True
        
        return left_val, right_val, is_float
    
    def _cast_to_type(self, value, target_type):
        """Convierte 'value' al 'target_type' de LLVM si es necesario."""
        
        if value is None:
             raise ValueError("Error del generador: Se intentó usar 'None' (probablemente una función void) en una expresión.")

        if value.type == target_type:
            return value
        
        if isinstance(target_type, ir.FloatType) and isinstance(value.type, ir.IntType):
            return self.builder.sitofp(value, target_type, name="sitofp_cast")
        if isinstance(target_type, ir.IntType) and isinstance(value.type, ir.FloatType):
            return self.builder.fptosi(value, target_type, name="fptosi_cast")
        
        if isinstance(value.type, ir.VoidType) and not isinstance(target_type, ir.VoidType):
             raise ValueError(f"Error del generador: Se intentó asignar una función 'void' a una variable de tipo '{target_type}'.")

        raise TypeError(f"No se puede convertir {value.type} a {target_type}")

    # --- Visitantes de Nodos AST ---

    def visit_program(self, node):
        """Visitante para el nodo raíz del programa."""
        for child in node.children:
            if child.type == ASTNodeType.FUNCTION_DECLARATION:
                self.visit(child)
        
        for child in node.children:
            if child.type == ASTNodeType.MAIN:
                self.visit(child)

    def visit_main(self, node):
        """Define la función 'main' en el código LLVM."""
        main_type = ir.FunctionType(ir.IntType(32), [])
        main_func = ir.Function(self.module, main_type, name='main')
        
        entry_block = main_func.append_basic_block(name='entry')
        
        self.current_function = main_func
        self.builder = ir.IRBuilder(entry_block)
        self.local_symbol_table = {}

        for statement in node.children:
            self.visit(statement)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ir.IntType(32), 0))
            
        self.current_function = None
        self.builder = None
        self.local_symbol_table = {}

    def visit_function_declaration(self, node):
        """Define una nueva función en el módulo LLVM."""
        func_name = node.value
        return_type_str = node.children[0].value
        param_list_node = node.children[1]
        body_node = node.children[2]

        return_type = self.get_llvm_type(return_type_str)
        param_types = [self.get_llvm_type(p.children[0].value) for p in param_list_node.children]

        func_type = ir.FunctionType(return_type, param_types)
        func = ir.Function(self.module, func_type, name=func_name)

        self.function_symbol_table[func_name] = func

        self.current_function = func
        entry_block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)
        self.local_symbol_table = {}

        for i, arg in enumerate(func.args):
            param_node = param_list_node.children[i]
            param_name = param_node.value
            arg.name = param_name
            
            ptr = self.builder.alloca(arg.type, name=f"{param_name}_ptr")
            self.builder.store(arg, ptr) 
            self.local_symbol_table[param_name] = ptr 

        self.visit(body_node)

        if not self.builder.block.is_terminated:
            if return_type == ir.VoidType():
                self.builder.ret_void()
            else:
                default_ret_val = ir.Constant(return_type, 0)
                self.builder.ret(default_ret_val)

        self.current_function = None
        self.builder = None
        self.local_symbol_table = {}

    def visit_declaration(self, node):
        """Maneja la declaración de variables (ej: 'int a;')."""
        var_type = self.get_llvm_type(node.value)

        for child in node.children:
            if child.type == ASTNodeType.ASSIGNMENT:
                var_name = child.children[0].value
                ptr = self.builder.alloca(var_type, name=var_name)
                self.local_symbol_table[var_name] = ptr
                self.visit(child)
            else:
                var_name = child.value
                ptr = self.builder.alloca(var_type, name=var_name)
                self.local_symbol_table[var_name] = ptr

    def visit_assignment(self, node):
        """Maneja la asignación (ej: 'a = 10;')."""
        var_name = node.children[0].value
        
        ptr = self.local_symbol_table.get(var_name)
        if not ptr:
            raise ValueError(f"Variable '{var_name}' no definida para el generador")

        value_to_store = self.visit(node.children[1])
        
        target_type = ptr.type.pointee
        value_to_store = self._cast_to_type(value_to_store, target_type)
        
        self.builder.store(value_to_store, ptr)

    def visit_identifier(self, node):
        """Maneja el uso de una variable en una expresión (ej: '... = a + 5;')."""
        var_name = node.value
        
        ptr = self.local_symbol_table.get(var_name)
        if not ptr:
            raise ValueError(f"Variable '{var_name}' no definida para el generador")
        
        return self.builder.load(ptr, name=var_name)

    def visit_number(self, node):
        """Maneja un número literal (ej: 10 o 5.5)."""
        if node.data_type == 'float':
            val = float(node.value)
            return ir.Constant(ir.FloatType(), val)
        else: # int
            val = int(node.value)
            return ir.Constant(ir.IntType(32), val)
        
    def visit_string(self, node):
        """Maneja un string literal (ej: "hola")."""
        raw_val = node.value[1:-1]
        c_str_val = raw_val + "\00"
        byte_val = bytearray(c_str_val.encode("utf8"))
        str_type = ir.ArrayType(ir.IntType(8), len(byte_val))
        str_const = ir.Constant(str_type, byte_val)
        
        str_name = f".str.{self.string_counter}"
        self.string_counter += 1
        
        g_str = ir.GlobalVariable(self.module, str_type, name=str_name)
        g_str.initializer = str_const
        g_str.global_constant = True
        g_str.unnamed_addr = True
        g_str.linkage = 'internal'

        zero = ir.Constant(ir.IntType(32), 0)
        gep_ptr = self.builder.gep(g_str, [zero, zero], inbounds=True, name=f"{str_name}_ptr")
        return gep_ptr

    def visit_boolean(self, node):
        """Maneja un booleano literal (true o false)"""
        val = 1 if node.value == 'true' else 0
        return ir.Constant(self.types['boolean'], val)

    def visit_binary_op(self, node):
        """Maneja operaciones binarias (aritméticas, relacionales y lógicas)."""
        
        left_val = self.visit(node.children[0])
        right_val = self.visit(node.children[1])
        
        op = node.value
        
        left_val, right_val, is_float = self._promote_types(left_val, right_val)

        if op == '+':
            return self.builder.fadd(left_val, right_val, name='fadd') if is_float else self.builder.add(left_val, right_val, name='add')
        elif op == '-':
            return self.builder.fsub(left_val, right_val, name='fsub') if is_float else self.builder.sub(left_val, right_val, name='sub')
        elif op == '*':
            return self.builder.fmul(left_val, right_val, name='fmul') if is_float else self.builder.mul(left_val, right_val, name='mul')
        elif op == '/':
            return self.builder.fdiv(left_val, right_val, name='fdiv') if is_float else self.builder.sdiv(left_val, right_val, name='sdiv')
        elif op == '%':
            return self.builder.srem(left_val, right_val, name='srem')

        if op == '<':
            return self.builder.fcmp_ordered('<', left_val, right_val, name='fcmp_lt') if is_float else self.builder.icmp_signed('<', left_val, right_val, name='icmp_lt')
        elif op == '<=':
            return self.builder.fcmp_ordered('<=', left_val, right_val, name='fcmp_le') if is_float else self.builder.icmp_signed('<=', left_val, right_val, name='icmp_le')
        elif op == '>':
            return self.builder.fcmp_ordered('>', left_val, right_val, name='fcmp_gt') if is_float else self.builder.icmp_signed('>', left_val, right_val, name='icmp_gt')
        elif op == '>=':
            return self.builder.fcmp_ordered('>=', left_val, right_val, name='fcmp_ge') if is_float else self.builder.icmp_signed('>=', left_val, right_val, name='icmp_ge')
        elif op == '==':
            return self.builder.fcmp_ordered('==', left_val, right_val, name='fcmp_eq') if is_float else self.builder.icmp_signed('==', left_val, right_val, name='icmp_eq')
        elif op == '!=':
            return self.builder.fcmp_ordered('!=', left_val, right_val, name='fcmp_ne') if is_float else self.builder.icmp_signed('!=', left_val, right_val, name='icmp_ne')

        bool_left = self._to_boolean(left_val)
        bool_right = self._to_boolean(right_val)
        
        if op == '&&':
            return self.builder.and_(bool_left, bool_right, name='and')
        elif op == '||':
            return self.builder.or_(bool_left, bool_right, name='or')
            
        raise ValueError(f"Operador binario desconocido: {op}")

    def visit_unary_op(self, node):
        """Maneja operadores unarios ('-' y '!')."""
        op = node.value
        expr_val = self.visit(node.children[0])
        
        if op == '-':
            if isinstance(expr_val.type, ir.FloatType):
                return self.builder.fneg(expr_val, name='fneg')
            else: # int
                return self.builder.sub(ir.Constant(ir.IntType(32), 0), expr_val, name='ineg')
        
        elif op == '!':
            bool_val = self._to_boolean(expr_val)
            return self.builder.xor(bool_val, ir.Constant(self.types['boolean'], 1), name='not')
            
        raise ValueError(f"Operador unario desconocido: {op}")

    def visit_if_statement(self, node):
        """Maneja 'if (cond) then ... else ... end'."""
        
        condition_node = node.children[0]
        condition_val = self.visit(condition_node)
        condition_bool = self._to_boolean(condition_val)

        then_block = self.current_function.append_basic_block('if_then')
        
        has_else = len(node.children) > 2
        
        if has_else:
            else_block = self.current_function.append_basic_block('if_else')
        
        endif_block = self.current_function.append_basic_block('if_end')
        
        if has_else:
            self.builder.cbranch(condition_bool, then_block, else_block)
        else:
            self.builder.cbranch(condition_bool, then_block, endif_block)
            
        self.builder.position_at_start(then_block)
        self.visit(node.children[1]) # Visita el ASTNode.BLOCK del 'then'
        if not self.builder.block.is_terminated:
            # --- CORRECCIÓN ---
            self.builder.branch(endif_block)
            # --- FIN CORRECCIÓN ---
            
        if has_else:
            self.builder.position_at_start(else_block)
            self.visit(node.children[2]) # Visita el ASTNode.BLOCK del 'else'
            if not self.builder.block.is_terminated:
                # --- CORRECCIÓN ---
                self.builder.branch(endif_block)
                # --- FIN CORRECCIÓN ---
        
        self.builder.position_at_start(endif_block)

    def visit_while_statement(self, node):
        """Maneja 'while (cond) ... end'."""
        
        loop_header = self.current_function.append_basic_block('while_header')
        loop_body = self.current_function.append_basic_block('while_body')
        loop_end = self.current_function.append_basic_block('while_end')
        
        # --- CORRECCIÓN ---
        self.builder.branch(loop_header)
        # --- FIN CORRECCIÓN ---
        
        self.builder.position_at_start(loop_header)
        condition_node = node.children[0]
        condition_val = self.visit(condition_node)
        condition_bool = self._to_boolean(condition_val)
        self.builder.cbranch(condition_bool, loop_body, loop_end)
        
        self.builder.position_at_start(loop_body)
        self.visit(node.children[1]) 
        if not self.builder.block.is_terminated:
            # --- CORRECCIÓN ---
            self.builder.branch(loop_header)
            # --- FIN CORRECCIÓN ---
            
        self.builder.position_at_start(loop_end)
    
    def visit_do_until_statement(self, node):
        """Maneja 'do ... until (cond)'."""
        
        loop_body = self.current_function.append_basic_block('do_body')
        loop_end = self.current_function.append_basic_block('do_end')

        # --- CORRECCIÓN ---
        self.builder.branch(loop_body)
        # --- FIN CORRECCIÓN ---
        
        self.builder.position_at_start(loop_body)
        self.visit(node.children[0]) 
        
        condition_node = node.children[1]
        condition_val = self.visit(condition_node)
        condition_bool = self._to_boolean(condition_val)
        
        if not self.builder.block.is_terminated:
            self.builder.cbranch(condition_bool, loop_end, loop_body)
            
        self.builder.position_at_start(loop_end)
    
    def visit_for_statement(self, node):
        """Maneja 'for (init; cond; inc) ... end'."""
        
        loop_header = self.current_function.append_basic_block('for_header')
        loop_body = self.current_function.append_basic_block('for_body')
        loop_inc = self.current_function.append_basic_block('for_inc')
        loop_end = self.current_function.append_basic_block('for_end')

        self.visit(node.children[0])
        
        # --- CORRECCIÓN ---
        self.builder.branch(loop_header)
        # --- FIN CORRECCIÓN ---

        self.builder.position_at_start(loop_header)
        condition_val = self.visit(node.children[1])
        condition_bool = self._to_boolean(condition_val)
        self.builder.cbranch(condition_bool, loop_body, loop_end)
        
        self.builder.position_at_start(loop_body)
        self.visit(node.children[3])
        if not self.builder.block.is_terminated:
            # --- CORRECCIÓN ---
            self.builder.branch(loop_inc) 
            # --- FIN CORRECCIÓN ---
            
        self.builder.position_at_start(loop_inc)
        self.visit(node.children[2])
        if not self.builder.block.is_terminated:
            # --- CORRECCIÓN ---
            self.builder.branch(loop_header) 
            # --- FIN CORRECCIÓN ---

        self.builder.position_at_start(loop_end)
        
    def visit_switch_statement(self, node):
        """Maneja 'switch (val) case ... default ... end'."""
        
        switch_val = self.visit(node.children[0])
        
        default_block = self.current_function.append_basic_block('switch_default')
        switch_end = self.current_function.append_basic_block('switch_end')
        
        switch_inst = self.builder.switch(switch_val, default_block)
        
        case_blocks = []
        for i in range(1, len(node.children)):
            case_node = node.children[i]
            
            if case_node.type == ASTNodeType.CASE_BLOCK:
                case_val = int(case_node.value)
                llvm_val = ir.Constant(self.types['int'], case_val)
                llvm_block = self.current_function.append_basic_block(f'switch_case_{case_val}')
                
                switch_inst.add_case(llvm_val, llvm_block)
                case_blocks.append((llvm_block, case_node.children[0])) 
            
            elif case_node.type == ASTNodeType.DEFAULT_BLOCK:
                case_blocks.append((default_block, case_node.children[0]))

        for block, body_node in case_blocks:
            self.builder.position_at_start(block)
            self.visit(body_node)
            if not self.builder.block.is_terminated:
                # --- CORRECCIÓN ---
                self.builder.branch(switch_end) 
                # --- FIN CORRECCIÓN ---
        
        if not default_block.instructions:
            self.builder.position_at_start(default_block)
            # --- CORRECCIÓN ---
            self.builder.branch(switch_end)
            # --- FIN CORRECCIÓN ---
            
        self.builder.position_at_start(switch_end)

    def visit_return_statement(self, node):
        """Maneja 'return ...;'."""
        
        if node.value == "void_return":
            self.builder.ret_void()
            return

        return_val = self.visit(node.children[0])
        
        target_type = self.current_function.return_value.type
        return_val = self._cast_to_type(return_val, target_type)
        
        self.builder.ret(return_val)

    def visit_function_call(self, node):
        """Maneja 'mi_funcion(...)'."""
        
        func_name = node.value
        
        func = self.function_symbol_table.get(func_name)
        if not func:
            raise ValueError(f"Generador de código no encontró la función: {func_name}")
            
        arg_values = []
        for i, arg_node in enumerate(node.children):
            arg_val = self.visit(arg_node)
            
            target_param_type = func.args[i].type
            arg_val = self._cast_to_type(arg_val, target_param_type)
            arg_values.append(arg_val)
            
        call_name = f"{func_name}_call" if func.return_value.type != ir.VoidType() else ""
        
        call_instruction = self.builder.call(func, arg_values, name=call_name)
        
        if func.return_value.type == ir.VoidType():
            return call_instruction 
        else:
            return call_instruction
    
    def visit_output_statement(self, node):
        """Maneja 'cout << ...'."""
        
        expr_node = node.children[0]
        value_to_print = self.visit(expr_node)
        expr_type = expr_node.data_type
        
        format_str_ptr = None
        if expr_type == 'int':
            format_str_ptr = self.format_int
        elif expr_type == 'float':
            format_str_ptr = self.format_float
            value_to_print = self.builder.fpext(value_to_print, ir.DoubleType(), name="float_to_double")
        elif expr_type == 'string':
            format_str_ptr = self.format_str
        else:
            return 
        
        zero = ir.Constant(ir.IntType(32), 0)
        gep_ptr = self.builder.gep(format_str_ptr, [zero, zero], inbounds=True, name="fmt_ptr")
        self.builder.call(self.printf, [gep_ptr, value_to_print])
    
    def visit_input_statement(self, node):
        """Maneja 'cin >> ...'."""

        var_name = node.children[0].value
        var_ptr = self.local_symbol_table.get(var_name)
        if not var_ptr:
            raise ValueError(f"Variable '{var_name}' no definida para 'cin'")

        var_type = var_ptr.type.pointee
        
        format_str_ptr = None
        if isinstance(var_type, ir.IntType):
            format_str_ptr = self.scan_int
        elif isinstance(var_type, ir.FloatType):
            format_str_ptr = self.scan_float
        else:
            return 

        zero = ir.Constant(ir.IntType(32), 0)
        gep_ptr = self.builder.gep(format_str_ptr, [zero, zero], inbounds=True, name="scanfmt_ptr")
        self.builder.call(self.scanf, [gep_ptr, var_ptr])

    # --- VISITANTES DE BLOQUES ---

    def visit_block(self, node):
        """Visita un bloque de sentencias (ej. cuerpo de 'if', 'while', 'for')."""
        for statement in node.children:
            self.visit(statement)
            if self.builder.block.is_terminated:
                break
                
    def visit_case_block(self, node):
        """Visita un bloque 'case' (solo visita su cuerpo)."""
        self.visit(node.children[0])

    def visit_default_block(self, node):
        """Visita un bloque 'default' (solo visita su cuerpo)."""
        self.visit(node.children[0])