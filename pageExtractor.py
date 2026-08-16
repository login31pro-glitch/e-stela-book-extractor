import json
import os
import re
import sys
from io import BytesIO
import requests
from PIL import Image

# Automatically resolve the folder where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

TRANSLATIONS = {
    "1": {  # English
        "lang_name": "English",
        "file_prompt": "Enter the filename of your .js file (default: pageEditor.js): ",
        "file_not_found": "Error: File '{}' was not found in '{}'.",
        "parse_error": "Error: Could not locate `var readerConfig` or parse JSON in '{}'.",
        "no_pages": "Error: No pages found in configuration.",
        "starting": "Found {total} pages. Starting download... (This may take a while depending on the number of pages and your connection speed)",
        "progress": "[{current}/{total}] Downloading page...",
        "fetch_error": "Failed to download page {page_num} (HTTP {status})",
        "saving": "Compiling {total} pages into PDF...",
        "done": "Success! PDF saved to: {output_path}",
    },
    "2": {  # Español
        "lang_name": "Español",
        "file_prompt": "Introduce el nombre del archivo .js (por defecto: pageEditor.js): ",
        "file_not_found": "Error: No se encontró el archivo '{}' en '{}'.",
        "parse_error": "Error: No se pudo encontrar `var readerConfig` o analizar el JSON en '{}'.",
        "no_pages": "Error: No se encontraron páginas en la configuración.",
        "starting": "Se encontraron {total} páginas. Iniciando descarga... (Esto puede tardar un tiempo dependiendo de la cantidad de páginas y la velocidad de tu conexión)",
        "progress": "[{current}/{total}] Descargando página...",
        "fetch_error": "Error al descargar la página {page_num} (HTTP {status})",
        "saving": "Compilando {total} páginas en PDF...",
        "done": "¡Completado! PDF guardado en: {output_path}",
    },
}

def select_language() -> dict:
    print("========================================")
    print(" Select Language / Selecciona Idioma")
    print("========================================")
    for key, val in TRANSLATIONS.items():
        print(f" [{key}] {val['lang_name']}")
    
    choice = input("\nSelect [1-2] (default: 1): ").strip()
    return TRANSLATIONS.get(choice, TRANSLATIONS["1"])

def extract_config(js_path: str, t: dict) -> dict:
    # Resolve path relative to script directory if not absolute
    if not os.path.isabs(js_path):
        resolved_path = os.path.join(SCRIPT_DIR, js_path)
    else:
        resolved_path = js_path

    if not os.path.isfile(resolved_path):
        print(t["file_not_found"].format(os.path.basename(resolved_path), os.path.dirname(resolved_path)))
        sys.exit(1)

    with open(resolved_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Search for readerConfig object
    match = re.search(r"var\s+readerConfig\s*=\s*(\{[\s\S]*\});?", content)
    if not match:
        print(t["parse_error"].format(resolved_path))
        sys.exit(1)

    raw_json = match.group(1).rstrip(";")
    return json.loads(raw_json)

def main():
    t = select_language()
    
    user_file = input("\n" + t["file_prompt"]).strip()
    js_file_name = user_file if user_file else "pageEditor.js"

    config = extract_config(js_file_name, t)
    pages = config.get("pages", [])

    if not pages:
        print(t["no_pages"])
        sys.exit(1)

    total_pages = len(pages)
    print("\n" + t["starting"].format(total=total_pages))

    images = []
    for idx, page in enumerate(pages, 1):
        url = page.get("FW9", "")
        if not url:
            continue
        if url.startswith("//"):
            url = "https:" + url

        print(t["progress"].format(current=idx, total=total_pages))
        
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                images.append(img)
            else:
                print(t["fetch_error"].format(page_num=idx, status=resp.status_code))
        except Exception as e:
            print(f"Error ({idx}): {e}")

    if images:
        output_name = os.path.join(SCRIPT_DIR, "extracted_book.pdf")
        print("\n" + t["saving"].format(total=len(images)))
        images[0].save(
            output_name,
            save_all=True,
            append_images=images[1:],
            resolution=100.0,
        )
        print(t["done"].format(output_path=output_name))

if __name__ == "__main__":
    main()