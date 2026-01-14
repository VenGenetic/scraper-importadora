import os
from PIL import Image

def convertir_jpg_a_webp(carpeta_origen, carpeta_destino, calidad=80):
    """
    Convierte todas las imágenes .jpg/.jpeg de una carpeta a .webp
    """
    
    # Crear la carpeta de destino si no existe
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        print(f"Carpeta creada: {carpeta_destino}")

    # Obtener lista de archivos
    archivos = os.listdir(carpeta_origen)
    
    contador = 0
    
    print(f"Iniciando conversión en: {carpeta_origen}...")

    for archivo in archivos:
        # Verificar si es jpg o jpeg (insensible a mayúsculas)
        if archivo.lower().endswith(('.jpg', '.jpeg')):
            
            ruta_completa_origen = os.path.join(carpeta_origen, archivo)
            
            # Definir el nombre del nuevo archivo (cambiando extensión)
            nombre_sin_ext = os.path.splitext(archivo)[0]
            nombre_nuevo = f"{nombre_sin_ext}.webp"
            ruta_completa_destino = os.path.join(carpeta_destino, nombre_nuevo)

            try:
                with Image.open(ruta_completa_origen) as img:
                    # Convertir y guardar
                    # 'optimize=True' reduce el tamaño extra
                    img.save(ruta_completa_destino, 'webp', quality=calidad, optimize=True)
                    
                print(f"[OK] Convertido: {archivo} -> {nombre_nuevo}")
                contador += 1
                
            except Exception as e:
                print(f"[ERROR] No se pudo convertir {archivo}: {e}")

    print("---")
    print(f"Proceso finalizado. Total convertidos: {contador}")

# --- CONFIGURACIÓN ---
# '.' significa la carpeta actual donde está el script.
# Puedes cambiar esto por una ruta absoluta ej: "C:/MisFotos/Vacaciones"
carpeta_entrada = "C:/Users/ferna/Documents/catalogo-motos-main/scraper/imagenes_repuestos"
carpeta_salida = "./convertidas_webp"

if __name__ == "__main__":
    convertir_jpg_a_webp(carpeta_entrada, carpeta_salida)