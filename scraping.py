import json
import time
import random
import os
import math
import re  # Importante para buscar texto
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

def obtener_catalogo_selenium():
    print(f"--- 🤖 Robot v4: Detección de 'Código' con Tilde ---")
    
    productos_totales = []
    
    options = webdriver.ChromeOptions()
    ruta_perfil = os.path.join(os.getcwd(), "perfil_robot_v2")
    options.add_argument(f"--user-data-dir={ruta_perfil}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 10)

        # 1. LOGIN
        print("🔍 Verificando sesión...")
        driver.get(LOGIN_URL)
        time.sleep(3)

        if "login" in driver.current_url or "Identificarse" in driver.page_source:
            try:
                print(f"⌨️  Logueando...")
                caja_user = wait.until(EC.presence_of_element_located((By.NAME, "login")))
                caja_user.clear()
                caja_user.send_keys(TU_EMAIL)
                caja_pass = driver.find_element(By.NAME, "password")
                caja_pass.clear()
                caja_pass.send_keys(TU_PASSWORD)
                caja_pass.send_keys(Keys.RETURN)
                time.sleep(5)
            except Exception as e:
                print(f"❌ Error Login: {e}")
        else:
            print("✅ Sesión activa.")

        # 2. SCRAPING
        pagina_actual = 1
        
        while True:
            if pagina_actual > LIMITE_PAGINAS:
                print(f"🛑 Límite alcanzado ({LIMITE_PAGINAS}).")
                break

            url = BASE_URL if pagina_actual == 1 else f"{BASE_URL}/page/{pagina_actual}"
            print(f"📄 Pag {pagina_actual}...", end="")
            driver.get(url)
            time.sleep(random.uniform(2.5, 4))
            
            items = driver.find_elements(By.CSS_SELECTOR, 'div.o_wsale_products_item')
            if not items:
                items = driver.find_elements(By.CSS_SELECTOR, 'form.oe_product_cart')
            
            if not items:
                if "404" in driver.title:
                    print(" ❌ Fin (404).")
                else:
                    print(" ❌ No hay productos.")
                break
                
            print(f" ✅ {len(items)} items.")
            
            items_guardados = 0
            
            for item in items:
                try:
                    texto_completo = item.text
                    texto_completo_lower = texto_completo.lower()

                    # FILTRO STOCK
                    if "agotado" in texto_completo_lower or "out of stock" in texto_completo_lower:
                        continue

                    # 1. NOMBRE
                    try:
                        nombre = item.find_element(By.CSS_SELECTOR, '.o_wsale_products_item_title a').text.strip()
                    except:
                        try:
                            nombre = item.find_element(By.TAG_NAME, 'h6').text.strip()
                        except:
                            continue 

                    # 2. CÓDIGO (LÓGICA ACTUALIZADA)
                    codigo = "S/N"
                    
                    # Regex Mejorado:
                    # - Busca "Código" (con tilde) o "Ref" o "Cod"
                    # - Acepta dos puntos opcionales (:)
                    # - Captura lo que sigue, ignorando mayúsculas/minúsculas
                    match_code = re.search(r'(Código|Ref|Cod|Referencia)\s*[:\.]?\s*([a-zA-Z0-9\-\.]+)', texto_completo, re.IGNORECASE)
                    
                    if match_code:
                        codigo = match_code.group(2).strip()
                    else:
                        # Plan B: Busca entre corchetes [ALGO]
                        match_bracket = re.search(r'\[(.*?)\]', nombre)
                        if match_bracket:
                            codigo = match_bracket.group(1).strip()

                    # 3. PRECIO (+20% y Redondeo Arriba)
                    try:
                        precio_tag = item.find_element(By.CSS_SELECTOR, '.oe_currency_value')
                        precio_base = float(precio_tag.text.replace(",", "."))
                        precio_final = math.ceil(precio_base * 1.20)
                    except:
                        precio_final = 0
                    
                    # 4. IMAGEN
                    try:
                        img_tag = item.find_element(By.TAG_NAME, 'img')
                        src = img_tag.get_attribute('src')
                        if src and src.startswith("/"):
                            imagen = "https://clientes.todomoto.com.ec" + src
                        else:
                            imagen = src
                    except:
                        imagen = "Sin imagen"
                    
                    cat = "General"
                    if "llanta" in nombre.lower(): cat = "Llantas"
                    elif "bateria" in nombre.lower(): cat = "Baterías"
                    
                    productos_totales.append({
                        "id": codigo if codigo != "S/N" else nombre.lower().replace(" ", "-")[:30],
                        "codigo_referencia": codigo, # El código extraído
                        "nombre": nombre,
                        "precio": precio_final,
                        "categoria": cat,
                        "imagen": imagen,
                        "stock": True
                    })
                    items_guardados += 1
                except:
                    continue
            
            print(f"    (Guardados {items_guardados})")
            pagina_actual += 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        print("🏁 Fin.")
        if 'driver' in locals():
            driver.quit()

    return productos_totales

def guardar_json(datos):
    if not datos:
        print("⚠️ Nada que guardar.")
        return
    
    datos_finales = {
        "RAW_SCRAPED_DATA": datos
    }
    
    with open('productos.json', 'w', encoding='utf-8') as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=4)
        
    print(f"✅ ¡LISTO! {len(datos)} productos guardados.")

if __name__ == "__main__":
    datos = obtener_catalogo_selenium()
    guardar_json(datos)