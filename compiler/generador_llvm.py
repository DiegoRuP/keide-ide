from llvmlite import ir
from analizador_sintactico import ASTNodeType
from llvmlite import binding as llvm

class CodeGenerator:
    """
    Esta clase recorre el Árbol de Sintaxis Abstracta (AST) que nos dio
    el analizador sintáctico y lo traduce a Código Intermedio de LLVM (LLVM IR).
    
    Usa el patrón "Visitor", por lo que tiene una función `visit_` para cada
    tipo de nodo del AST (ej: `visit_number`, `visit_binary_op`, etc.).
    """
    
    def __init__(self):
        
        # --- Configuración Inicial de LLVM ---
        
        # Obtiene la arquitectura de tu máquina (ej. "arm64-apple-darwin" para Mac M1/M2)
        # Esto es vital para que 'llc' sepa qué tipo de ensamblador generar.
        target_triple = llvm.get_default_triple()
        
        # El 'module' es el contenedor de todo nuestro código LLVM.
        self.module = ir.Module(name="mi_programa")
        self.module.triple = target_triple

        # El 'builder' es el objeto "lápiz" que usamos para escribir
        # las instrucciones LLVM (como 'add', 'store', 'call')
        self.builder = None
        
        # Nuestra tabla de símbolos. Guardará los *punteros* a las variables.
        # Ej: {'mi_variable': <puntero i32* a la dirección de memoria de mi_variable>}
        self.symbol_table = {}
        
        # Un contador para darle nombres únicos a las cadenas de texto globales.
        self.string_counter = 0 #

        # --- Declaración de Funciones Externas (de C) ---
        #
        # Le decimos a LLVM que "confíe en nosotros" y que funciones como 'printf'
        # y 'scanf' existen en algún lado (el 'linker' de C las encontrará).
        
        # Declarar 'printf' (para nuestro 'cout')
        # ir.IntType(32) -> Retorna un entero (i32)
        # [ir.IntType(8).as_pointer()] -> Toma un puntero a char (i8*) como primer argumento
        # var_arg=True -> Acepta un número variable de otros argumentos
        printf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")
        
        # Declarar 'scanf' (para nuestro 'cin')
        scanf_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_type, name="scanf")
        
        # --- Variables Globales (para las cadenas de formato) ---
        #
        # Creamos constantes globales para las cadenas de formato que usan printf/scanf.
        # Ej: "%d\n" (imprimir entero con salto de línea)
        # El '\00' es el terminador nulo de C.
        
        # Formato para 'cout << int' -> "%d\n"
        fmt_int_val = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray("%d\n\00".encode("utf8")))
        self.format_int = ir.GlobalVariable(self.module, fmt_int_val.type, name="fmt_int")
        self.format_int.initializer = fmt_int_val
        self.format_int.global_constant = True
        
        # Formato para 'cout << float' -> "%f\n"
        fmt_float_val = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray("%f\n\00".encode("utf8")))
        self.format_float = ir.GlobalVariable(self.module, fmt_float_val.type, name="fmt_float")
        self.format_float.initializer = fmt_float_val
        self.format_float.global_constant = True
        
        # Formato para 'cout << string' -> "%s\n"
        fmt_str_val = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray("%s\n\00".encode("utf8")))
        self.format_str = ir.GlobalVariable(self.module, fmt_str_val.type, name="fmt_str")
        self.format_str.initializer = fmt_str_val
        self.format_str.global_constant = True
        
        # Formato para 'cin >> int' -> "%d"
        scan_int_val = ir.Constant(ir.ArrayType(ir.IntType(8), 3), bytearray("%d\00".encode("utf8")))
        self.scan_int = ir.GlobalVariable(self.module, scan_int_val.type, name="scan_int")
        self.scan_int.initializer = scan_int_val
        self.scan_int.global_constant = True

        # Formato para 'cin >> float' -> "%f"
        scan_float_val = ir.Constant(ir.ArrayType(ir.IntType(8), 3), bytearray("%f\00".encode("utf8")))
        self.scan_float = ir.GlobalVariable(self.module, scan_float_val.type, name="scan_float")
        self.scan_float.initializer = scan_float_val
        self.scan_float.global_constant = True
    

    def get_llvm_type(self, type_str):
        """Función auxiliar para mapear tipos de nuestro lenguaje a tipos de LLVM."""
        if type_str == 'int':
            return ir.IntType(32) # Entero de 32 bits
        if type_str == 'float':
            return ir.FloatType() # Flotante
        if type_str == 'string':
            return ir.IntType(8).as_pointer() # Puntero a char (i8*)
        return ir.VoidType()

    def generate(self, node):
        """Punto de entrada principal. Inicia el recorrido del AST."""
        self.visit(node)
        # Al final, convierte todo el 'module' de LLVM a un string
        return str(self.module)

    # --- Motor del Patrón Visitor ---
    
    def visit(self, node):
        """
        Llama a la función 'visit_...' específica para el tipo de nodo.
        Ej: Si node.type es NUMBER, llama a 'self.visit_number(node)'.
        """
        if not node:
            return None
        
        method_name = f'visit_{node.type.name.lower()}'
        # Si no encuentra un 'visit_' específico, usa 'generic_visit'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Visitante genérico: solo visita a todos los hijos del nodo."""
        for child in node.children:
            self.visit(child)

    def visit_program(self, node):
        """Visitante para el nodo raíz del programa."""
        self.generic_visit(node)

    def visit_main(self, node):
        """Define la función 'main' en el código LLVM."""
        
        # 1. Definir la firma de la función: 'i32 main()'
        main_type = ir.FunctionType(ir.IntType(32), [])
        main_func = ir.Function(self.module, main_type, name='main')
        
        # 2. Crear el bloque de entrada (el punto de inicio de la función)
        entry_block = main_func.append_basic_block(name='entry')
        
        # 3. Apuntar nuestro 'builder' a este bloque.
        #    (Todas las instrucciones se escribirán aquí)
        self.builder = ir.IRBuilder(entry_block)

        # 4. Crear un nuevo scope para la tabla de símbolos de 'main'
        self.symbol_table = {}

        # 5. Visitar todas las sentencias dentro de 'main'
        for statement in node.children:
            self.visit(statement)

        # 6. Añadir el 'return 0' al final, como en C.
        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ir.IntType(32), 0))

    def visit_declaration(self, node):
        """Maneja la declaración de variables (ej: 'int a;')."""
        
        # Obtiene el tipo LLVM (ej: ir.IntType(32))
        var_type = self.get_llvm_type(node.value)

        # Recorre cada variable declarada (ej: 'int a, b;')
        for child in node.children:
            if child.type == ASTNodeType.ASSIGNMENT:
                # Caso: 'int a = 10;'
                var_name = child.children[0].value
                # 1. Reservar memoria para la variable en la 'pila' (stack)
                ptr = self.builder.alloca(var_type, name=var_name)
                # 2. Guardar el *puntero* a esa memoria en nuestra tabla
                self.symbol_table[var_name] = ptr
                # 3. Visitar la asignación para que guarde el valor
                self.visit(child)
            else:
                # Caso: 'int a;'
                var_name = child.value
                # 1. Reservar memoria
                ptr = self.builder.alloca(var_type, name=var_name)
                # 2. Guardar el puntero
                self.symbol_table[var_name] = ptr

    def visit_assignment(self, node):
        """Maneja la asignación (ej: 'a = 10;')."""
        
        var_name = node.children[0].value
        
        # 1. Buscar el *puntero* de la variable en la tabla de símbolos
        ptr = self.symbol_table.get(var_name)
        if not ptr:
            raise ValueError(f"Variable '{var_name}' no definida para el generador")

        # 2. Visitar el lado derecho de la asignación (la expresión)
        #    Esto nos devolverá el valor a guardar (ej: un 'ir.Constant(10)')
        value_to_store = self.visit(node.children[1])
        
        # 3. Generar la instrucción 'store' (guardar el valor en el puntero)
        self.builder.store(value_to_store, ptr)

    def visit_identifier(self, node):
        """Maneja el uso de una variable en una expresión (ej: '... = a + 5;')."""
        
        var_name = node.value
        
        # 1. Obtener el *puntero* a la variable (su dirección de memoria)
        ptr = self.symbol_table.get(var_name)
        if not ptr:
            raise ValueError(f"Variable '{var_name}' no definida para el generador")
        
        # 2. Generar la instrucción 'load' (cargar el *valor* que está en esa dirección)
        return self.builder.load(ptr, name=var_name)

    def visit_number(self, node):
        """Maneja un número literal (ej: 10 o 5.5)."""
        # Simplemente devuelve una constante de LLVM del tipo correcto.
        if node.data_type == 'float':
            val = float(node.value)
            return ir.Constant(ir.FloatType(), val)
        else: # int
            val = int(node.value)
            return ir.Constant(ir.IntType(32), val)
        
    def visit_string(self, node):
        """Maneja un string literal (ej: "hola")."""
        
        # 1. Preparar el string al estilo C (quitar comillas, añadir terminador \0)
        raw_val = node.value[1:-1]
        c_str_val = raw_val + "\00"
        
        # 2. Convertir a un array de bytes
        byte_val = bytearray(c_str_val.encode("utf8"))
        
        # 3. Definir el tipo LLVM (un array de N bytes)
        str_type = ir.ArrayType(ir.IntType(8), len(byte_val))
        
        # 4. Crear la constante
        str_const = ir.Constant(str_type, byte_val)
        
        # 5. Crear una variable GLOBAL y constante para este string.
        #    (Los strings literales se guardan en la sección de solo lectura del programa)
        
        # --- ¡CORRECCIÓN DE BUG! ---
        # Usamos 'string_counter' (definido en __init__) en lugar de 'str_counter'
        str_name = f".str.{self.string_counter}"
        self.string_counter += 1
        # --- FIN DE LA CORRECCIÓN ---
        
        g_str = ir.GlobalVariable(self.module, str_type, name=str_name)
        g_str.initializer = str_const
        g_str.global_constant = True
        g_str.unnamed_addr = True
        g_str.linkage = 'internal'

        # 6. Devolver un puntero al primer carácter de la cadena (un i8*).
        #    'gep' (Get Element Pointer) es la forma de LLVM de hacer esto.
        zero = ir.Constant(ir.IntType(32), 0)
        gep_ptr = self.builder.gep(g_str, [zero, zero], inbounds=True, name=f"{str_name}_ptr")
        return gep_ptr

    def visit_binary_op(self, node):
        """Maneja operaciones binarias (ej: a + b, c * 2)."""
        
        # 1. Visitar recursivamente los lados izquierdo y derecho
        left_val = self.visit(node.children[0])
        right_val = self.visit(node.children[1])
        
        op = node.value
        is_float = (node.data_type == 'float')
        
        # (Falta implementar la concatenación de strings con '+')
        
        # 2. Elegir la instrucción LLVM correcta basada en el operador y el tipo
        if op == '+':
            # 'fadd' para flotantes, 'add' para enteros
            return self.builder.fadd(left_val, right_val, name='fadd') if is_float else self.builder.add(left_val, right_val, name='add')
        elif op == '-':
            return self.builder.fsub(left_val, right_val, name='fsub') if is_float else self.builder.sub(left_val, right_val, name='sub')
        elif op == '*':
            return self.builder.fmul(left_val, right_val, name='fmul') if is_float else self.builder.mul(left_val, right_val, name='mul')
        elif op == '/':
            # 'fdiv' para flotantes, 'sdiv' (división firmada) para enteros
            return self.builder.fdiv(left_val, right_val, name='fdiv') if is_float else self.builder.sdiv(left_val, right_val, name='sdiv')
        
        pass # (Para operadores relacionales/lógicos que aún no implementamos)
    
    
    def visit_output_statement(self, node):
        """Maneja 'cout << ...'."""
        
        # 1. Visitar la expresión para obtener el valor a imprimir
        expr_node = node.children[0]
        value_to_print = self.visit(expr_node)

        # 2. Obtener el tipo de la expresión (gracias al analizador semántico)
        expr_type = expr_node.data_type
        
        # 3. Seleccionar la cadena de formato global correcta ("%d\n", "%f\n", "%s\n")
        format_str_ptr = None
        if expr_type == 'int':
            format_str_ptr = self.format_int
        elif expr_type == 'float':
            format_str_ptr = self.format_float
        elif expr_type == 'string':
            format_str_ptr = self.format_str
        else:
            return # Tipo no imprimible
        
        # 4. Obtener un puntero (i8*) a la cadena de formato
        zero = ir.Constant(ir.IntType(32), 0)
        gep_ptr = self.builder.gep(format_str_ptr, [zero, zero], inbounds=True, name="fmt_ptr")

        # 5. Generar la llamada a 'printf'
        #    Formato: call @printf(puntero_formato, valor_a_imprimir)
        self.builder.call(self.printf, [gep_ptr, value_to_print])
    
    def visit_input_statement(self, node):
        """Maneja 'cin >> ...'."""

        # 1. Obtener el nombre de la variable (ej: 'edad')
        var_name = node.children[0].value
        
        # 2. Obtener el *puntero* a la variable de la tabla de símbolos
        #    'scanf' necesita la dirección de memoria para saber dónde guardar el dato.
        var_ptr = self.symbol_table.get(var_name)
        if not var_ptr:
            raise ValueError(f"Variable '{var_name}' no definida para 'cin'")

        # 3. Obtener el tipo de la variable (i32, float)
        var_type = var_ptr.type.pointee
        
        # 4. Seleccionar la cadena de formato global correcta ("%d", "%f")
        format_str_ptr = None
        if isinstance(var_type, ir.IntType):
            format_str_ptr = self.scan_int
        elif isinstance(var_type, ir.FloatType):
            format_str_ptr = self.scan_float
        else:
            return # Tipo no legible

        # 5. Obtener un puntero (i8*) a la cadena de formato
        zero = ir.Constant(ir.IntType(32), 0)
        gep_ptr = self.builder.gep(format_str_ptr, [zero, zero], inbounds=True, name="scanfmt_ptr")

        # 6. Generar la llamada a 'scanf'
        #    Formato: call @scanf(puntero_formato, puntero_a_variable)
        self.builder.call(self.scanf, [gep_ptr, var_ptr])