import os
from PIL import Image

# --- ⚙️ CONFIGURACIÓN ---
# Carpeta donde están las fotos originales con marcas de agua
CARPETA_ORIGEN = "FOTOS_POR_CODIGO" 

# Carpeta donde se guardarán las fotos limpias
CARPETA_DESTINO = "FOTOS_RECORTADAS_SIN_MARCA"

# ¿Qué porcentaje de la parte inferior quieres eliminar?
# Basado en tu ejemplo, las marcas son grandes, probemos con 20%.
# Si corta mucho producto, reduce este número (ej. 15).
# Si sigue apareciendo la marca, auméntalo (ej. 25).
PORCENTAJE_A_RECORTAR = 22.0 

# Calidad al guardar JPG (85 es un buen estándar)
CALIDAD_JPG = 90
# ------------------------

# Asegurar que las carpetas existan
if not os.path.exists(CARPETA_ORIGEN):
    print(f"❌ Error: La carpeta de origen '{CARPETA_ORIGEN}' no existe.")
    exit()
    
if not os.path.exists(CARPETA_DESTINO):
    os.makedirs(CARPETA_DESTINO)
    print(f"📁 Carpeta destino '{CARPETA_DESTINO}' creada.")

def recortar_imagen(nombre_archivo):
    ruta_origen = os.path.join(CARPETA_ORIGEN, nombre_archivo)
    
    try:
        # 1. Abrir imagen
        with Image.open(ruta_origen) as img:
            # Convertir a RGB para asegurar compatibilidad al guardar como JPG
            img = img.convert("RGB")
            
            ancho_original, alto_original = img.size
            
            # 2. Calcular dónde cortar
            # Si queremos quitar el 20% de abajo, nos quedamos con el 80% de arriba.
            factor_corte = 1.0 - (PORCENTAJE_A_RECORTAR / 100.0)
            nuevo_alto = int(alto_original * factor_corte)
            
            # Definir la caja de recorte (Izquierda, Arriba, Derecha, Abajo)
            # Mantenemos todo el ancho, empezamos desde arriba (0), hasta el nuevo alto calculado.
            caja_recorte = (0, 0, ancho_original, nuevo_alto)
            
            # 3. Ejecutar el recorte
            img_recortada = img.crop(caja_recorte)
            
            # 4. Guardar imagen procesada
            # Cambiamos extensión a .jpg por si acaso la original era png
            nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
            nombre_final = f"{nombre_sin_ext}_cut.jpg"
            ruta_destino = os.path.join(CARPETA_DESTINO, nombre_final)
            
            img_recortada.save(ruta_destino, "JPEG", quality=CALIDAD_JPG, optimize=True)
            # print(f"   ✂️ Recortada: {nombre_archivo} (Alto original: {alto_original} -> Nuevo: {nuevo_alto})")
            return True

    except Exception as e:
        print(f"   ⚠️ Error procesando {nombre_archivo}: {e}")
        return False

def iniciar_proceso():
    print(f"--- INICIANDO RECORTE INFERIOR ({PORCENTAJE_A_RECORTAR}%) ---")
    
    archivos = os.listdir(CARPETA_ORIGEN)
    imagenes_validas = [f for f in archivos if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    total = len(imagenes_validas)
    procesados = 0
    
    if total == 0:
        print("⚠️ No se encontraron imágenes en la carpeta de origen.")
        return

    print(f"Detectadas {total} imágenes. Procesando...")

    for i, archivo in enumerate(imagenes_validas):
        if recortar_imagen(archivo):
            procesados += 1
            # Mostrar progreso cada 10 imágenes para no saturar la consola
            if (i + 1) % 10 == 0 or (i + 1) == total:
                 print(f"   Progreso: {i + 1}/{total} imágenes.")

    print(f"\n✅ FIN. {procesados} imágenes recortadas guardadas en '{CARPETA_DESTINO}'.")

if __name__ == "__main__":
    iniciar_proceso()