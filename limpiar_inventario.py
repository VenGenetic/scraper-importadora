import pandas as pd

# CONFIGURACIÓN
archivo_entrada = 'PVP DAYTONA AXXO NOV 2025 JA.xlsx' # Pon el nombre exacto de tu archivo
archivo_salida = 'Inventario_Maestro_Limpio.xlsx'
nombre_hoja = 'DAYTONA' # El nombre de la pestaña que vi en tu foto

print("--- Iniciando proceso de limpieza ---")

# 1. Cargar el Excel
# 'header=4' indica que los encabezados están en la fila 5 (Python cuenta desde 0)
df = pd.read_excel(archivo_entrada, sheet_name=nombre_hoja, header=4)

print(f"Registros totales encontrados: {len(df)}")

# 2. Asegurar que la columna FECHA sea formato fecha
# Ajusta 'FECHA' si el nombre de tu columna tiene espacios, ej: 'FECHA '
try:
    df['FECHA'] = pd.to_datetime(df['FECHA'])
except Exception as e:
    print(f"Error convirtiendo fechas: {e}")

# 3. Ordenar: Lo más reciente arriba
df = df.sort_values(by='FECHA', ascending=False)

# 4. Eliminar duplicados
# subset=['CODIGO'] -> Busca duplicados solo en esta columna
# keep='first' -> Como ya ordenamos por fecha descendente, el 'primero' es el más nuevo.
df_limpio = df.drop_duplicates(subset=['CODIGO'], keep='first')

print(f"Registros únicos finales: {len(df_limpio)}")
print(f"Se eliminaron {len(df) - len(df_limpio)} registros antiguos.")

# 5. Guardar el resultado en un nuevo Excel
df_limpio.to_excel(archivo_salida, index=False)

print(f"--- Éxito. Archivo guardado como: {archivo_salida} ---")