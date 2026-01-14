import sqlite3
import json
import pandas as pd
import os
import sys

# --- CONFIGURACIÓN ---
DB_NAME = "sistema_daytona_pro.db"
ARCHIVO_JSON = 'data.json'
ARCHIVO_EXCEL = 'Inventario_Maestro_Limpio.xlsx'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Permite acceder a columnas por nombre
    return conn

def inicializar_tablas():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("⚙️  Configurando estructura de base de datos optimizada...")
    
    # Tabla MAESTRA con índices para búsqueda rápida
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repuestos (
            codigo TEXT PRIMARY KEY,
            nombre TEXT,
            precio REAL,
            categoria TEXT DEFAULT 'General',
            imagen_url TEXT,
            origen_datos TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Creamos un ÍNDICE en la columna nombre para que buscar repuestos sea instantáneo
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_nombre ON repuestos(nombre)')
    
    conn.commit()
    conn.close()

def procesar_datos():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    registros_json = 0
    registros_excel = 0
    ignorados = 0
    
    print("🚀 Iniciando carga masiva de datos...")

    # 1. CARGA DE LA IMPORTADORA (JSON) - Prioridad Alta (Mejores datos/fotos)
    if os.path.exists(ARCHIVO_JSON):
        try:
            with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items = data.get("RAW_SCRAPED_DATA", [])
                
            print(f"   📂 Procesando {len(items)} items del JSON...")
            
            # Usamos una TRANSACCIÓN para velocidad extrema
            cursor.execute('BEGIN TRANSACTION')
            
            for item in items:
                cod = str(item.get('codigo_referencia')).strip()
                
                # Insertamos o Ignoramos si ya existe
                cursor.execute('''
                    INSERT OR IGNORE INTO repuestos (codigo, nombre, precio, categoria, imagen_url, origen_datos)
                    VALUES (?, ?, ?, ?, ?, 'IMPORTADORA')
                ''', (cod, item.get('nombre'), item.get('precio'), item.get('categoria'), item.get('imagen')))
                
                if cursor.rowcount > 0:
                    registros_json += 1
                else:
                    ignorados += 1 # Ya existía o duplicado interno
            
            conn.commit()
            print(f"   ✅ {registros_json} repuestos importados del JSON.")
            
        except Exception as e:
            print(f"   ❌ Error crítico en JSON: {e}")
            conn.rollback()
    else:
        print(f"   ⚠️ No se encontró {ARCHIVO_JSON}")

    # 2. CARGA DE TU INVENTARIO (EXCEL) - Rellenar huecos
    if os.path.exists(ARCHIVO_EXCEL):
        try:
            print(f"   📊 Analizando Excel para encontrar repuestos antiguos...")
            df = pd.read_excel(ARCHIVO_EXCEL)
            
            cursor.execute('BEGIN TRANSACTION')
            
            for index, row in df.iterrows():
                cod = str(row['CODIGO']).strip()
                
                # Intentamos insertar. Si el código ya lo puso el JSON, esto fallará silenciosamente (OR IGNORE)
                # Así nos aseguramos de NO duplicar y quedarnos con la data del JSON si existe.
                cursor.execute('''
                    INSERT OR IGNORE INTO repuestos (codigo, nombre, precio, imagen_url, origen_datos)
                    VALUES (?, ?, ?, ?, 'MI_INVENTARIO')
                ''', (cod, row['DESCRIPCION'], row['PVP U'], 'sin_imagen.jpg'))
                
                if cursor.rowcount > 0:
                    registros_excel += 1
            
            conn.commit()
            print(f"   ✅ {registros_excel} repuestos EXCLUSIVOS recuperados del Excel.")
            
        except Exception as e:
            print(f"   ❌ Error crítico en Excel: {e}")
            conn.rollback()
    else:
        print(f"   ⚠️ No se encontró {ARCHIVO_EXCEL}")

    # RESUMEN FINAL
    cursor.execute('SELECT count(*) FROM repuestos')
    total = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n" + "="*40)
    print(f"   RESUMEN FINAL DE LA BASE DE DATOS")
    print("="*40)
    print(f"   📦 Total Repuestos Únicos:  {total}")
    print(f"   💾 Archivo Base de Datos:   {DB_NAME}")
    print(f"   ⚡ Estado:                  OPTIMIZADO")
    print("="*40)

if __name__ == "__main__":
    inicializar_tablas()
    procesar_datos()