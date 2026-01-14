import sqlite3
import pandas as pd
import os
import sys
from datetime import datetime

# --- BLOQUE DE RUTA ABSOLUTA ---
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.append(directorio_actual)

try:
    import nuevo_scraper
    print(f"✅ Scraper cargado correctamente.")
except ImportError as e:
    print(f"❌ Error CRÍTICO importando nuevo_scraper: {e}")
    sys.exit()

# --- CONFIGURACIÓN ---
DB_NAME = "sistema_daytona_pro.db"
BODEGA_VIRTUAL = "Bajo Pedido"

def conectar_db():
    ruta_db = os.path.join(directorio_actual, DB_NAME)
    return sqlite3.connect(ruta_db)

def asegurar_tablas_existen(conn):
    cursor = conn.cursor()
    
    # 1. Tabla MAESTRA (Repuestos) - SIN COLUMNA DE IMAGEN
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repuestos (
            codigo TEXT PRIMARY KEY,
            nombre TEXT,
            precio REAL,
            categoria TEXT DEFAULT 'General',
            origen_datos TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Tabla INVENTARIO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_producto TEXT,
            bodega TEXT, 
            cantidad INTEGER DEFAULT 0,
            FOREIGN KEY(codigo_producto) REFERENCES repuestos(codigo),
            UNIQUE(codigo_producto, bodega)
        )
    ''')
    conn.commit()

def sincronizar_todo():
    print(f"\n🚀 INICIANDO SINCRONIZACIÓN (SIN IMÁGENES) - {datetime.now()}")
    
    # 1. EJECUTAR SCRAPER
    print("\n--- PASO 1: Escrapeando sitio web... ---")
    datos_nuevos = nuevo_scraper.obtener_catalogo_selenium()
    
    if not datos_nuevos:
        print("⚠️ El scraper no trajo datos. Abortando.")
        return

    print(f"📦 Datos obtenidos: {len(datos_nuevos)} productos.")
    
    # 2. ACTUALIZAR BASE DE DATOS
    conn = conectar_db()
    asegurar_tablas_existen(conn)
    cursor = conn.cursor()
    
    nuevos = 0
    actualizados = 0
    agotados = 0
    
    try:
        # A. Detectar qué había antes para saber qué se agotó
        cursor.execute("SELECT codigo_producto FROM inventario WHERE bodega = ? AND cantidad > 0", (BODEGA_VIRTUAL,))
        codigos_anteriores = set(row[0] for row in cursor.fetchall())
        codigos_actuales = set()

        cursor.execute('BEGIN TRANSACTION')

        for item in datos_nuevos:
            cod = item['codigo_referencia']
            codigos_actuales.add(cod)
            
            # --- FASE 1: EL CATÁLOGO ---
            # Insertamos SIN imagen
            cursor.execute('''
                INSERT OR IGNORE INTO repuestos (codigo, nombre, precio, categoria, origen_datos)
                VALUES (?, ?, ?, ?, 'IMPORTADORA')
            ''', (cod, item['nombre'], item['precio'], item['categoria']))
            
            if cursor.rowcount > 0:
                nuevos += 1
            
            # Solo actualizamos PRECIO (la imagen ya no importa)
            cursor.execute('''
                UPDATE repuestos 
                SET precio = ?
                WHERE codigo = ?
            ''', (item['precio'], cod))

            # --- FASE 2: EL STOCK ---
            cursor.execute('''
                INSERT INTO inventario (codigo_producto, bodega, cantidad)
                VALUES (?, ?, 1)
                ON CONFLICT(codigo_producto, bodega) DO UPDATE SET cantidad = 1
            ''', (cod, BODEGA_VIRTUAL))
            actualizados += 1

        # --- FASE 3: LIMPIEZA ---
        codigos_a_bajar = codigos_anteriores - codigos_actuales
        for cod_agotado in codigos_a_bajar:
            cursor.execute('''
                UPDATE inventario SET cantidad = 0 
                WHERE codigo_producto = ? AND bodega = ?
            ''', (cod_agotado, BODEGA_VIRTUAL))
            agotados += 1

        conn.commit()
        
        print("\n" + "="*40)
        print("      ✅ SINCRONIZACIÓN COMPLETADA")
        print("="*40)
        print(f"   ✨ Nuevos en Catálogo:      {nuevos}")
        print(f"   🔄 Stock 'Bajo Pedido':     {actualizados}")
        print(f"   📉 Marcados Agotados:       {agotados}")
        print("="*40)

    except Exception as e:
        conn.rollback()
        print(f"❌ Error Crítico: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    sincronizar_todo()