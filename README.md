# Keide IDE 🚀

Keide IDE es un entorno de desarrollo integrado (IDE) sencillo y personalizable, diseñado para facilitar la escritura y compilación de código. Este proyecto está construido con **Electron**, **Python** y tecnologías web como **HTML**, **CSS** y **JavaScript**.

---

## Instalación 🛠️

Sigue estos pasos para instalar y ejecutar Keide IDE en tu máquina:

1. **Clona el repositorio**:
```bash
git clone [https://github.com/diegorup/keide-ide.git](https://github.com/diegorup/keide-ide.git)
cd keide-ide
````

2.  **Instala dependencias**:

<!-- end list -->

```bash
npm install
```

3.  **Ejecuta la aplicación**:

<!-- end list -->

```bash
npm start
```

-----

## Características del Lenguaje 📜

El compilador de Keide IDE soporta un lenguaje de programación imperativo, tipado estáticamente y con una sintaxis inspirada en C++ y Pascal. A continuación se detallan sus características principales.

-----

### Tipos de Datos

El lenguaje maneja tres tipos de datos primitivos:

  * **`int`**: Para números enteros (ej. `10`, `-5`, `1000`).
  * **`float`**: Para números de punto flotante (ej. `3.14`, `-0.5`, `100.0`).
  * **`string`**: Para cadenas de texto (ej. `"hola mundo"`, `"Keide IDE"`).

-----

### Variables y Ámbito

Las variables deben ser declaradas antes de su uso. El compilador soporta múltiples ámbitos (scopes).

  * **Declaración Global**: Las variables declaradas fuera de cualquier función son globales.
    ```c
    int version = 1;
    string status = "OK";
    ```
  * **Declaración Local**: Las variables declaradas dentro de una función (incluyendo `main`) son locales a esa función.
    ```c
    main {
        int score = 100;
    }
    ```
  * **Inicialización**: Se puede asignar un valor a una variable en la misma línea de su declaración.
    ```c
    float health = 100.0;
    ```
  * **Sombreado (Shadowing)**: Es posible declarar una variable local con el mismo nombre que una global. La variable local tendrá prioridad dentro de su ámbito.

-----

### Estructuras de Control

#### Condicionales

Se utiliza la estructura `if-then-else-end`. El bloque `else` es opcional. La condición debe ir entre paréntesis.

```c
if (score > 100 && status == "OK") then
    cout << "Nivel superado";
else
    cout << "Sigue intentando";
end
```

#### Bucles

  * **`while`**: Se ejecuta mientras la condición sea verdadera.
    ```c
    int i = 5;
    while (i > 0)
        cout << i;
        i = i - 1;
    end
    ```
  * **`do-until`**: Se ejecuta al menos una vez y continúa hasta que la condición sea verdadera.
    ```c
    int x = 0;
    do
        x = x + 1;
    until (x == 10);
    ```

-----

### Operadores

| Tipo | Operadores | Descripción |
| :--- | :--- | :--- |
| **Aritméticos** | `+`, `-`, `*`, `/`, `%` | Realizan operaciones matemáticas. El `+` también concatena strings. |
| **Relacionales**| `==`, `!=`, `<`, `>`, `<=`, `>=` | Comparan valores y devuelven un resultado booleano. |
| **Lógicos** | `&&` (Y), `||` (O) | Combinan expresiones booleanas. |
| **Asignación** | `=` | Asigna un valor a una variable. |

-----

### Funciones

Se pueden declarar funciones personalizadas con tipo de retorno y parámetros. Las variables declaradas dentro de una función son locales a ella.

```c
int calcular_puntaje(int tiempo, int enemigos) {
    int puntos_base = 1000;
    int resultado = puntos_base - tiempo + (enemigos * 10);
}

main {
    // El compilador actual solo analiza la declaración de la función,
    // no las llamadas a la misma.
}
```

-----

### Entrada y Salida

El lenguaje incluye comandos básicos para interactuar con la consola.

  * **Salida (`cout`)**: Imprime texto o el valor de una variable en la consola.
    ```c
    cout << "Hola, " + player_name;
    ```
  * **Entrada (`cin`)**: Lee un valor desde la consola y lo asigna a una variable.
    ```c
    int edad;
    cin >> edad;
    ```

-----

### Limitaciones Actuales ⚠️

Es importante tener en cuenta las características que **no** están implementadas en la versión actual del compilador:

  * No hay soporte para bucles `for`.
  * No hay soporte para la estructura `switch`.
  * No se pueden declarar `arreglos (arrays)` ni `estructuras (structs)`.
  * Las **llamadas a funciones** no se validan semánticamente (no se comprueba el número o tipo de argumentos).
  * No se valida el uso de la sentencia `return` dentro de las funciones.

<!-- end list -->

```