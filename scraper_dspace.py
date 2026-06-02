import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import re

# =============================================================================
# INSTRUCCIONES PARA ADAPTAR A CUALQUIER REPOSITORIO DSPACE
# =============================================================================
# Este script está diseñado para extraer metadatos y descargar PDFs de repositorios
# institucionales que utilizan el sistema DSpace (específicamente la interfaz JSPUI).
# El repositorio REDICCES es un ejemplo de este sistema.
#
# PASOS PARA USAR CON OTRO DSPACE:
# 1. BASE_URL: Cambia esta variable por la URL principal del nuevo repositorio.
#    (Ejemplo: "http://repositorio.universidad.edu")
#
# 2. COLECCIONES: Navega manualmente en el repositorio DSpace hasta la página de 
#    la "Colección" de la cual quieres extraer los documentos.
#    La URL suele verse como: BASE_URL/jspui/handle/XXXXX/YYYY
#    Copia esas URLs y agrégalas a la lista COLECCIONES que está abajo.
#
# DSpace estructura sus enlaces internamente con el patrón '/jspui/handle/...'
# y usa el parámetro '?offset=' para la paginación, lo cual este script
# maneja automáticamente.
# =============================================================================

# --- CONFIGURACIÓN PRINCIPAL ---
# URL base del repositorio DSpace (Actualmente configurado para REDICCES)
BASE_URL = "http://www.redicces.org.sv"

# Encabezado para simular un navegador
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# URLs de las colecciones objetivo en el repositorio DSpace
COLECCIONES = [
    "http://www.redicces.org.sv/jspui/handle/10972/220",
    "http://www.redicces.org.sv/jspui/handle/10972/223",
    "http://www.redicces.org.sv/jspui/handle/10972/224",
    "http://www.redicces.org.sv/jspui/handle/10972/453",
    "http://www.redicces.org.sv/jspui/handle/10972/208",
    "http://www.redicces.org.sv/jspui/handle/10972/225",
    "http://www.redicces.org.sv/jspui/handle/10972/212"
]

# Configuración de salida
DOWNLOAD_DIR = "DSpace_PDFs"
EXCEL_FILENAME = "Catalogo_DSpace.xlsx"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
catalogo = []

def obtener_items_de_coleccion(url):
    items = set()
    offset = 0
    # DSpace utiliza el formato de enlace /jspui/handle/prefijo/id para los items
    patron_item = re.compile(r'^/jspui/handle/\d+/\d+$')
    print(f"Navegando por las páginas de {url}...")
    
    while True:
        # Paginación nativa de DSpace usando offset
        pag_url = f"{url}?offset={offset}"
        try:
            response = requests.get(pag_url, headers=HEADERS, timeout=15)
        except requests.exceptions.RequestException:
            time.sleep(5)
            continue
            
        soup = BeautifulSoup(response.text, 'html.parser')
        nuevos_items = 0
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if patron_item.match(href):
                url_completa = BASE_URL + href
                # Validar que no sea la URL de la colección en sí
                if url_completa not in COLECCIONES and url_completa not in items:
                    items.add(url_completa)
                    nuevos_items += 1
                    
        if nuevos_items == 0:
            break  # Fin de la colección
            
        offset += 20
        time.sleep(2)
    return list(items)

def procesar_item(item_url, item_id):
    try:
        response = requests.get(item_url, headers=HEADERS, timeout=15)
    except:
        return False
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Validar que sea una página de item con metadatos Dublin Core (DC)
    if not soup.find('meta', {'name': 'DC.title'}):
        return False
        
    try:
        titulo = soup.find('meta', {'name': 'DC.title'})['content']
    except:
        titulo = f"Documento_Sin_Titulo_{item_id}"
        
    try:
        tipo_doc = soup.find('meta', {'name': 'DC.type'})['content']
    except:
        tipo_doc = "Libro/Revista"
        
    pdf_url = None
    # Buscar enlaces a archivos PDF (DSpace los aloja en rutas tipo /bitstream/)
    for a in soup.find_all('a', href=True):
        if '.pdf' in a['href'].lower() and 'bitstream' in a['href'].lower():
            href = a['href']
            pdf_url = BASE_URL + href if href.startswith('/') else href
            break

    pdf_filename = ""
    if pdf_url:
        # Limpiar el título para usarlo como nombre de archivo válido
        pdf_filename = f"{item_id}_{str(titulo).replace(' ', '_')[:30]}.pdf"
        pdf_filename = "".join(c for c in pdf_filename if c.isalnum() or c in (' ', '.', '_')).rstrip()
        pdf_path = os.path.join(DOWNLOAD_DIR, pdf_filename)
        
        print(f"[{item_id}] Descargando: {pdf_filename}...")
        try:
            if not os.path.exists(pdf_path):
                pdf_response = requests.get(pdf_url, stream=True, headers=HEADERS, timeout=20)
                with open(pdf_path, 'wb') as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                print(f"  -> Archivo ya existente.")
        except Exception as e:
            print(f"Error descargando: {e}")
            pdf_filename = "ERROR"
            
    catalogo.append({
        "Id": item_id,
        "Titulo": titulo,
        "Tipo de Documento": tipo_doc,
        "Ficha Bibliografica_URL": item_url,
        "Archivo_PDF": pdf_filename
    })
    return True

print("Iniciando scraper de DSpace...")
todos_los_enlaces = []
for col_url in COLECCIONES:
    enlaces = obtener_items_de_coleccion(col_url)
    todos_los_enlaces.extend(enlaces)

todos_los_enlaces = list(set(todos_los_enlaces))
item_counter = 1

for url_doc in todos_los_enlaces:
    if procesar_item(url_doc, item_id=item_counter):
        item_counter += 1
    time.sleep(2) # Pausa amigable para no saturar el servidor

if catalogo:
    df = pd.DataFrame(catalogo)
    df.to_excel(EXCEL_FILENAME, index=False)
    print(f"¡Catálogo guardado en {EXCEL_FILENAME}!")
