import sys

def compilar(codigo):
    # Lógica de compilación
    return f"Código compilado: {codigo}"

if __name__ == "__main__":
    codigo = sys.stdin.read()
    resultado = compilar(codigo)
    print(resultado)