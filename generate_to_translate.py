import os
import sys
from datetime import datetime

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_DIR = os.path.join(BASE_DIR, "source")
OUTPUT_DIR = os.path.join(BASE_DIR, "wynik")
TRANSLATE_FILE = os.path.join(BASE_DIR, "to_translate.yml")

if not os.path.exists(SOURCE_DIR):
    log(f"BŁĄD: Nie znaleziono folderu source: {SOURCE_DIR}")
    sys.exit(1)

output_lines = []

# Lista tagów do wyciągania
tags_to_capture = ["name:", "lore:", "itemname:", "display_name:"]

try:
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".yml")]
    if not files:
        log("Brak plików .yml w folderze source.")
    else:
        log(f"Znaleziono {len(files)} plików .yml w folderze source.")

    for file_name in files:
        source_path = os.path.join(SOURCE_DIR, file_name)
        
        # Przechowywanie znalezionych wartości dla raportu
        captured_data = {
            "name": [],
            "itemname": [],
            "display_name": [],
            "lore_found": False
        }

        try:
            with open(source_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            log(f"Nie udało się odczytać pliku {file_name}: {e}")
            continue

        output_lines.append(f"### FILE: {file_name}\n")
        capture_lore = False
        
        for line in lines:
            stripped = line.strip()

            # Sprawdzanie tagów
            found_tag = False
            for tag in ["name:", "itemname:", "display_name:"]:
                if stripped.startswith(tag):
                    output_lines.append(line.rstrip("\n") + "\n")
                    # Wyciągamy samą wartość po dwukropku do raportu
                    val = stripped.split(":", 1)[1].strip()
                    captured_data[tag.replace(":", "")].append(val)
                    found_tag = True
                    break
            
            if found_tag:
                continue

            # Sprawdzanie sekcji lore
            if stripped == "lore:":
                output_lines.append(line.rstrip("\n") + "\n")
                capture_lore = True
                captured_data["lore_found"] = True
                continue

            if capture_lore:
                if stripped.startswith("-"):
                    output_lines.append(line.rstrip("\n") + "\n")
                else:
                    capture_lore = False

        output_lines.append("\n")
        
        # --- DYNAMICZNY RAPORT W KONSOLI ---
        log(f"\n--- Przetworzono plik: {file_name} ---")
        
        for key in ["name", "itemname", "display_name"]:
            if captured_data[key]:
                log(f"    - Zapisano {key} ({len(captured_data[key])}):")
                for value in captured_data[key]:
                    log(f"        > {value}") # Każda wartość w nowej linii
        
        if captured_data["lore_found"]:
            log(f"    - Zapisano lore: Tak")
        else:
            log(f"    - Zapisano lore: Nie znaleziono")
        
        log("-" * (25 + len(file_name)))

    # Zapis UTF-8
    with open(TRANSLATE_FILE, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    log(f"\nPlik {TRANSLATE_FILE} został wygenerowany pomyślnie!")

except Exception as e:
    log(f"Wystąpił błąd: {e}")

