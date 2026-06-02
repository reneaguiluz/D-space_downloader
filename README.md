# Scraper Universal para Repositorios DSpace

Este proyecto extrae metadatos y descarga archivos PDF de colecciones específicas en repositorios institucionales que utilicen DSpace (interfaz JSPUI).

## Instrucciones para configurar:
1. Abre `scraper_dspace.py` en un editor de texto.
2. Modifica la variable `BASE_URL` para que apunte al repositorio que deseas extraer (ej. REDICCES).
3. Cambia las URLs dentro de la lista `COLECCIONES` para incluir los enlaces de las colecciones objetivo.

## Ejecución:
1. Instala las librerías: `pip install -r requirements.txt`
2. Ejecuta el script: `python scraper_dspace.py`

Al finalizar, tendrás una carpeta `DSpace_PDFs` y un Excel `Catalogo_DSpace.xlsx`.
