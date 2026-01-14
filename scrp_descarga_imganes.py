import os
import time
import random
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 🔒 TUS CREDENCIALES ---
TU_EMAIL = "jhon_andrade75@hotmail.com"
TU_PASSWORD = "Barcelona75" 

# --- ⚙️ CONFIGURACIÓN ---
BASE_URL = "https://clientes.todomoto.com.ec/shop"
LOGIN_URL = "https://clientes.todomoto.com.ec/web/login"
LIMITE_PAGINAS = 18 
CARPETA_SALIDA = "FOTOS_POR_CODIGO"

# Crear carpeta si no existe
if not os.path.exists(CARPETA_SALIDA):
    os.makedirs(CARPETA_SALIDA)

def limpiar_nombre(texto):
    """Elimina caracteres prohibidos para nombres de archivo"""
    # Reemplazamos caracteres inválidos por guiones o vacío
    return re.sub(r'[\\/*?:"<>|]', "", texto).strip()

def descargar_y_guardar(url_imagen, nombre_archivo):
    """Descarga la imagen solo si tiene URL válida"""
    if not url_imagen or url_imagen == "Sin imagen":
        return

    try:
        # Definir extensión (jpg por defecto si no es obvia)
        ext = url_imagen.split('.')[-1].split('?')[0]
        if len(ext) > 4 or len(ext) < 2: ext = "jpg"
        
        nombre_final = f"{nombre_archivo}.{ext}"
        ruta = os.path.join(CARPETA_SALIDA, nombre_final)

        # Si ya existe, saltamos (para no perder tiempo)
        if os.path.exists(ruta):
            return

        # Descargar
        response = requests.get(url_imagen, stream=True, timeout=10)
        if response.status_code == 200:
            with open(ruta, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
    except Exception as e:
        print(f"   ⚠️ Error al guardar {nombre_archivo}: {e}")

def iniciar_descarga_masiva():
    print(f"--- 🚀 Iniciando Descarga (Corrección Tilde 'Código') ---")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    try:
        # 1. LOGIN
        driver.get(LOGIN_URL)
        time.sleep(2)
        
        if "login" in driver.current_url:
            print("🔑 Iniciando sesión...")
            try:
                driver.find_element(By.NAME, "login").send_keys(TU_EMAIL)
                caja_pass = driver.find_element(By.NAME, "password")
                caja_pass.send_keys(TU_PASSWORD)
                caja_pass.send_keys(Keys.RETURN)
                time.sleep(5) # Espera un poco más para asegurar el login
            except:
                print("⚠️ Ya estabas logueado o hubo un error en login.")

        # 2. RECORRIDO
        pagina_actual = 1
        imgs_totales = 0
        
        while pagina_actual <= LIMITE_PAGINAS:
            url = BASE_URL if pagina_actual == 1 else f"{BASE_URL}/page/{pagina_actual}"
            print(f"📄 Pag {pagina_actual}: ", end="")
            driver.get(url)
            time.sleep(random.uniform(2, 3))
            
            items = driver.find_elements(By.CSS_SELECTOR, 'div.o_wsale_products_item')
            if not items: 
                # Intento alternativo de selector si cambia la vista
                items = driver.find_elements(By.CSS_SELECTOR, 'form.oe_product_cart')
            
            if not items:
                print(" Fin (No hay más productos).")
                break

            imgs_pagina = 0
            for item in items:
                try:
                    texto = item.text
                    
                    # --- CORRECCIÓN AQUÍ ---
                    # Buscamos "C[óo]digo" para que acepte con o sin tilde
                    # Capturamos el código alfanumérico que sigue
                    match_code = re.search(r'(C[óo]digo|Ref|Cod|Referencia)\s*[:\.]?\s*([a-zA-Z0-9\-\.]+)', texto, re.IGNORECASE)
                    
                    nombre_archivo = ""
                    
                    if match_code:
                        codigo_encontrado = match_code.group(2).strip()
                        nombre_archivo = limpiar_nombre(codigo_encontrado)
                    else:
                        # Si FALLA el regex, usamos el nombre del producto como plan B
                        # para no perder la foto
                        try:
                            nombre_sucio = item.find_element(By.TAG_NAME, 'h6').text
                            if not nombre_sucio:
                                nombre_sucio = item.find_element(By.CSS_SELECTOR, '.o_wsale_products_item_title a').text
                            # Usamos solo los primeros 30 caracteres del nombre
                            nombre_archivo = limpiar_nombre(nombre_sucio.replace(" ", "_")[:30])
                        except:
                            continue # Si no tiene ni código ni nombre, saltamos

                    # Obtener URL de imagen
                    src = "Sin imagen"
                    try:
                        img_tag = item.find_element(By.TAG_NAME, 'img')
                        src = img_tag.get_attribute('src')
                        if src and src.startswith("/"):
                            src = "https://clientes.todomoto.com.ec" + src
                    except:
                        continue 

                    # Descargar
                    descargar_y_guardar(src, nombre_archivo)
                    imgs_pagina += 1
                    imgs_totales += 1

                except Exception as e:
                    continue
            
            print(f" {imgs_pagina} imágenes descargadas.")
            pagina_actual += 1

        print(f"\n🏁 PROCESO TERMINADO. {imgs_totales} imágenes en total.")

    except Exception as e:
        print(f"❌ Error fatal: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    iniciar_descarga_masiva()