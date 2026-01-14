import json
import time
import random
import os
import math
import re
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
ARCHIVO_SALIDA = "data.json"

def obtener_catalogo_selenium():
    print(f"--- 🤖 Iniciando Scraper (Precios Blindados) ---")
    
    productos_totales = []
    ids_vistos = set()
    
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
                print(f"🛑 Límite de páginas alcanzado ({LIMITE_PAGINAS}).")
                break

            url = BASE_URL if pagina_actual == 1 else f"{BASE_URL}/page/{pagina_actual}"
            print(f"📄 Procesando Pag {pagina_actual}...", end="")
            driver.get(url)
            time.sleep(random.uniform(2, 3))
            
            items = driver.find_elements(By.CSS_SELECTOR, 'div.o_wsale_products_item')
            if not items:
                items = driver.find_elements(By.CSS_SELECTOR, 'form.oe_product_cart')
            
            if not items:
                print(" ❌ No se encontraron productos.")
                break
            
            items_nuevos = 0
            
            for item in items:
                try:
                    texto_completo = item.text
                    texto_lower = texto_completo.lower()

                    if "agotado" in texto_lower or "out of stock" in texto_lower:
                        continue

                    # --- EXTRACCIÓN ---
                    # 1. NOMBRE
                    try:
                        nombre = item.find_element(By.TAG_NAME, 'h6').text.strip()
                    except:
                        try:
                            nombre = item.find_element(By.CSS_SELECTOR, '.o_wsale_products_item_title a').text.strip()
                        except:
                            continue

                    # 2. CÓDIGO
                    codigo = "S/N"
                    match_code = re.search(r'(Código|Ref|Cod|Referencia)\s*[:\.]?\s*([a-zA-Z0-9\-\.]+)', texto_completo, re.IGNORECASE)
                    if match_code:
                        codigo = match_code.group(2).strip()
                    else:
                        match_bracket = re.search(r'\[(.*?)\]', nombre)
                        if match_bracket:
                            codigo = match_bracket.group(1).strip()
                    
                    if codigo in ids_vistos and codigo != "S/N":
                        continue
                    ids_vistos.add(codigo)

                    # 3. PRECIO (MEJORADO) -----------------------------------
                    precio_final = 0.0
                    try:
                        # Intento A: Selector estándar de Odoo (.oe_currency_value)
                        precio_tag = item.find_element(By.CSS_SELECTOR, '.oe_currency_value')
                        precio_texto = precio_tag.text
                    except:
                        try:
                            # Intento B: Buscar cualquier número con signo $
                            # A veces el precio está en un span 'text-danger' (oferta) o 'text-primary'
                            precio_tag = item.find_element(By.XPATH, ".//span[contains(text(), '$')]")
                            precio_texto = precio_tag.text.replace("$", "")
                        except:
                            precio_texto = "0"

                    # Limpieza del texto (quitar $, comas, espacios)
                    precio_limpio = precio_texto.replace("$", "").replace(",", ".").strip()
                    
                    try:
                        precio_base = float(precio_limpio)
                        # Aplicar tu margen del 20%
                        if precio_base > 0:
                            precio_final = math.ceil(precio_base * 1.20)
                    except ValueError:
                        precio_final = 0.0
                    # --------------------------------------------------------
                    
                    cat = "General"
                    if "llanta" in nombre.lower(): cat = "Llantas"
                    elif "bateria" in nombre.lower(): cat = "Baterías"
                    elif "lubricante" in nombre.lower(): cat = "Lubricantes"
                    
                    productos_totales.append({
                        "codigo_referencia": codigo,
                        "nombre": nombre,
                        "precio": precio_final,
                        "categoria": cat,
                        "stock": True
                    })
                    items_nuevos += 1
                    
                except Exception:
                    continue
            
            print(f" ✅ {items_nuevos} nuevos.")
            
            if items_nuevos == 0 and len(items) > 0:
                print("⚠️ Posible página duplicada. Deteniendo.")
                break
                
            pagina_actual += 1
            
    except Exception as e:
        print(f"\n❌ Error General: {e}")
    finally:
        print("🏁 Scraping finalizado.")
        if 'driver' in locals():
            driver.quit()

    return productos_totales

if __name__ == "__main__":
    datos = obtener_catalogo_selenium()
    # Guardado de prueba
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        json.dump({"RAW_SCRAPED_DATA": datos}, f, ensure_ascii=False, indent=4)
    print(f"Archivo guardado: {ARCHIVO_SALIDA}")