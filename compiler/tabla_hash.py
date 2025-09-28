# compiler/tabla_hash.py

class HashTable:
    # Implementación simple de una Tabla Hash con manejo de colisiones por encadenamiento.
    def __init__(self, size=16):
        self.size = size
        # La tabla es una lista de listas (buckets) para manejar colisiones.
        self.table = [[] for _ in range(size)]

    def _hash(self, key):
        # Función de hash simple para cadenas de texto.
        return sum(ord(char) for char in key) % self.size

    def insert(self, symbol_data):
        # Inserta un símbolo en la tabla.
        # symbol_data es un diccionario que debe contener 'name' y otros detalles.
        key = symbol_data.get('name')
        if not key:
            return
        
        index = self._hash(key)
        # Simplemente añade el símbolo al bucket (lista) en ese índice.
        self.table[index].append(symbol_data)

def populate_hash_table_from_symbol_table(symbol_table_scopes, hash_table_size=16):
    """
    Toma la tabla de símbolos por ámbitos y la inserta en una Tabla Hash.
    """
    hash_table = HashTable(size=hash_table_size)
    
    # Iterar sobre cada diccionario de ámbito en la lista
    for scope in symbol_table_scopes:
        # Iterar sobre cada símbolo en el ámbito
        for name, details in scope.items():
            if name == '__name__':
                continue # Omitir la clave interna del nombre del ámbito
            
            # Crear un diccionario completo para el símbolo
            symbol_data = {
                'name': name,
                'type': details.get('type'),
                'scope': scope.get('__name__'),
                'line': details.get('line'),
                'column': details.get('column'),
                'memory_address': details.get('memory_address') # Asumimos que la anotación ya ocurrió
            }
            hash_table.insert(symbol_data)
            
    return hash_table

def hash_table_to_html(hash_table):
    # Convierte la estructura de la Tabla Hash a una tabla HTML.
    html = '<table class="hash-table">'
    html += '<thead><tr><th class="ht-header">Índice</th><th class="ht-header">Símbolo (Variable)</th><th class="ht-header">Datos (Tipo, Ámbito, Memoria...)</th></tr></thead>'
    html += '<tbody>'

    for index, bucket in enumerate(hash_table.table):
        if not bucket:
            # Si el bucket está vacío, mostrar una fila vacía
            html += f'<tr><td class="ht-cell ht-cell-index">{index}</td><td class="ht-cell">-</td><td class="ht-cell">-</td></tr>'
        else:
            # Si hay elementos, usar rowspan para el índice
            is_collision = len(bucket) > 1
            first_entry = True
            for i, symbol in enumerate(bucket):
                row_class = "collision-row" if is_collision else ""
                html += f'<tr class="{row_class}">'
                
                if first_entry:
                    html += f'<td class="ht-cell ht-cell-index" rowspan="{len(bucket)}">{index}</td>'
                    first_entry = False
                
                # Formatear los datos del símbolo
                symbol_name = symbol.get('name', 'N/A')
                symbol_details = (
                    f"<b>Tipo:</b> {symbol.get('type', '?')} <br>"
                    f"<b>Ámbito:</b> {symbol.get('scope', '?')} <br>"
                    f"<b>Mem:</b> {symbol.get('memory_address', '?')} <br>"
                    f"<b>Pos:</b> L{symbol.get('line', '?')}, C{symbol.get('column', '?')}"
                )
                
                html += f'<td class="ht-cell ht-cell-name">{symbol_name}</td>'
                html += f'<td class="ht-cell ht-cell-details">{symbol_details}</td>'
                html += '</tr>'

    html += '</tbody></table>'
    return html