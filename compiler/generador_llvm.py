from llvmlite import ir
from analizador_sintactico import ASTNodeType
from llvmlite import binding as llvm

class CodeGenerator:
    def __init__(self):
        
        # Inicializar LLVM
        target_triple = llvm.get_default_triple()
        
        # Módulo LLVM: contenedor principal de funciones y variables
        self.module = ir.Module(name="mi_programa")
        self.module.triple = target_triple

        # Crear el builder, que nos ayuda a construir instrucciones
        self.builder = None
        self.symbol_table = {}
        
        # Declaracion de funcion printf 
        printf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")
        
        # Declaracion de funcion scanf
        scanf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_type, name="scanf")
        
        # Crear cadenas de formato globales para printf
        fmt_int_val = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray("%d\n\00".encode("utf8")))
        self.format_int = ir.GlobalVariable(self.module, fmt_int_val.type, name="fmt_int")
        self.format_int.initializer = fmt_int_val
        self.format_int.global_constant = True
        
        # Crear flotantes 
        fmt_float_val = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray("%f\n\00".encode("utf8")))
        self.format_float = ir.GlobalVariable(self.module, fmt_float_val.type, name="fmt_float")
        self.format_float.initializer = fmt_float_val
        self.format_float.global_constant = True
        
        # "%d" para leer enteros
        scan_int_val = ir.Constant(ir.ArrayType(ir.IntType(8), 3), bytearray("%d\00".encode("utf8")))
        self.scan_int = ir.GlobalVariable(self.module, scan_int_val.type, name="scan_int")
        self.scan_int.initializer = scan_int_val
        self.scan_int.global_constant = True

        # "%f" para leer flotantes (se usa %f pero se pasa un puntero a float)
        scan_float_val = ir.Constant(ir.ArrayType(ir.IntType(8), 3), bytearray("%f\00".encode("utf8")))
        self.scan_float = ir.GlobalVariable(self.module, scan_float_val.type, name="scan_float")
        self.scan_float.initializer = scan_float_val
        self.scan_float.global_constant = True
        

    def get_llvm_type(self, type_str):
        """Convierte un string de tipo (de tu AST) a un tipo LLVM."""
        if type_str == 'int':
            return ir.IntType(32)
        if type_str == 'float':
            return ir.FloatType()
        if type_str == 'string':
            return ir.IntType(8).as_pointer()
        return ir.VoidType()

    def generate(self, node):
        """Punto de entrada principal para generar el código."""
        self.visit(node)
        return str(self.module)

    def visit(self, node):
        """Función visitante genérica."""
        if not node:
            return None
        
        method_name = f'visit_{node.type.name.lower()}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Visita todos los hijos de un nodo."""
        for child in node.children:
            self.visit(child)

    def visit_program(self, node):
        self.generic_visit(node)

    def visit_main(self, node):
        # El 'main' es la función 'main' en LLVM
        # Retorna int (código de salida) y no toma argumentos (de momento)
        main_type = ir.FunctionType(ir.IntType(32), [])
        main_func = ir.Function(self.module, main_type, name='main')
        
        # 'entry' es el bloque básico de inicio de la función
        entry_block = main_func.append_basic_block(name='entry')
        
        # Creamos el builder. Todas las instrucciones se insertarán en este bloque de entrada.
        self.builder = ir.IRBuilder(entry_block)

        # Reseteamos la tabla de símbolos para esta función
        self.symbol_table = {}

        # Visitamos todas las sentencias dentro de main
        for statement in node.children:
            self.visit(statement)

        # 'main' debe terminar con 'ret i32 0'
        # Si no hay un 'return' explícito, lo añadimos.
        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ir.IntType(32), 0))

    def visit_declaration(self, node):
        # 'node.value' tiene el tipo (ej: 'int')
        var_type = self.get_llvm_type(node.value)

        for child in node.children:
            if child.type == ASTNodeType.ASSIGNMENT:
                # Es 'int x = 5'
                var_name = child.children[0].value
                # 1. Reservar memoria (alloca)
                ptr = self.builder.alloca(var_type, name=var_name)
                # 2. Guardar el puntero en la tabla de símbolos
                self.symbol_table[var_name] = ptr
                # 3. Visitar el nodo de asignación para generar el 'store'
                self.visit(child)
            else:
                # Es 'int x'
                var_name = child.value
                # 1. Reservar memoria (alloca)
                ptr = self.builder.alloca(var_type, name=var_name)
                # 2. Guardar el puntero
                self.symbol_table[var_name] = ptr

    def visit_assignment(self, node):
        var_name = node.children[0].value
        
        # Buscamos el *puntero* a la variable en nuestra tabla
        ptr = self.symbol_table.get(var_name)
        if not ptr:
            # Esto no debería pasar si el semántico funcionó
            raise ValueError(f"Variable '{var_name}' no definida para el generador")

        # Visitamos la expresión a la derecha (ej: 5 + 10)
        # Esto nos devolverá un valor LLVM (un Constant o el resultado de una op)
        value_to_store = self.visit(node.children[1])
        
        # Generamos la instrucción 'store'
        self.builder.store(value_to_store, ptr)

    def visit_identifier(self, node):
        # Cuando un identificador se usa en una expresión (ej: c = a + b)
        # necesitamos Cargar su valor de la memoria.
        var_name = node.value
        ptr = self.symbol_table.get(var_name)
        if not ptr:
            raise ValueError(f"Variable '{var_name}' no definida para el generador")
        
        # Generamos la instrucción 'load'
        return self.builder.load(ptr, name=var_name)

    def visit_number(self, node):
        # El analizador semántico ya anotó el tipo
        if node.data_type == 'float':
            val = float(node.value)
            return ir.Constant(ir.FloatType(), val)
        else: # int
            val = int(node.value)
            return ir.Constant(ir.IntType(32), val)

    def visit_binary_op(self, node):
        # Visitamos recursivamente los operandos
        left_val = self.visit(node.children[0])
        right_val = self.visit(node.children[1])
        
        op = node.value
        
        # El semántico debió anotar el tipo resultante (ej: 'int' o 'float')
        # Esto es crucial para saber si usar 'fadd' (float) o 'add' (int)
        is_float = (node.data_type == 'float')
        
        if op == '+':
            return self.builder.fadd(left_val, right_val, name='fadd') if is_float else self.builder.add(left_val, right_val, name='add')
        elif op == '-':
            return self.builder.fsub(left_val, right_val, name='fsub') if is_float else self.builder.sub(left_val, right_val, name='sub')
        elif op == '*':
            return self.builder.fmul(left_val, right_val, name='fmul') if is_float else self.builder.mul(left_val, right_val, name='mul')
        elif op == '/':
            return self.builder.fdiv(left_val, right_val, name='fdiv') if is_float else self.builder.sdiv(left_val, right_val, name='sdiv')
        
        
        # raise NotImplementedError(f"Operador binario '{op}' no implementado en el generador")
        pass
    
    
    def visit_output_statement(self, node):
        """
        Genera una llamada a printf() basada en el tipo de la expresión.
        """
        # 1. Visitar la expresión que queremos imprimir (ej: 'a' o 'a + 5')
        expr_node = node.children[0]
        value_to_print = self.visit(expr_node)

        # 2. Determinar el tipo de dato de la expresión
        expr_type = expr_node.data_type
        
        # 3. Seleccionar la cadena de formato adecuada
        if expr_type == 'int':
            format_str_ptr = self.format_int
        elif expr_type == 'float':
            format_str_ptr = self.format_float
        # elif expr_type == 'string':
        #    format_str_ptr = self.format_str
        #    # (Imprimir strings es más complejo, lo dejamos para después)
        else:
            # Tipo no soportado para imprimir
            return

        # 4. Obtener un puntero a la cadena de formato
        #    (Necesario para 'call')
        zero = ir.Constant(ir.IntType(32), 0)
        gep_ptr = self.builder.gep(format_str_ptr, [zero, zero], inbounds=True, name="fmt_ptr")

        # 5. Generar la llamada a printf
        #    printf(puntero_a_formato, valor_a_imprimir)
        self.builder.call(self.printf, [gep_ptr, value_to_print])
    
    def visit_input_statement(self, node):
        """
        Genera una llamada a scanf() basada en el tipo de la variable.
        """
        # 1. Obtener el nombre de la variable (ej: 'a')
        var_name = node.children[0].value
        
        # 2. Buscar el *puntero* a la variable en la tabla de símbolos
        var_ptr = self.symbol_table.get(var_name)
        if not var_ptr:
            # Error semántico ya debió cachar esto, pero por si acaso
            raise ValueError(f"Variable '{var_name}' no definida para 'cin'")

        # 3. Determinar el tipo de la variable desde el puntero
        var_type = var_ptr.type.pointee # Saca el tipo al que apunta (ej: i32)
        
        format_str_ptr = None
        if isinstance(var_type, ir.IntType):
            format_str_ptr = self.scan_int
        elif isinstance(var_type, ir.FloatType):
            format_str_ptr = self.scan_float
        else:
            # Tipo no soportado para leer
            return

        # 4. Obtener un puntero a la cadena de formato
        zero = ir.Constant(ir.IntType(32), 0)
        gep_ptr = self.builder.gep(format_str_ptr, [zero, zero], inbounds=True, name="scanfmt_ptr")

        # 5. Generar la llamada a scanf
        #    scanf(puntero_a_formato, puntero_a_variable)
        self.builder.call(self.scanf, [gep_ptr, var_ptr])
