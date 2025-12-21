import os
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_DIR = os.path.join(BASE_DIR, "source")
OUTPUT_DIR = os.path.join(BASE_DIR, "wynik")
TRANSLATE_FILE = os.path.join(BASE_DIR, "to_translate.yml")

if not os.path.exists(SOURCE_DIR):
    print(f"BŁĄD: Nie znaleziono folderu source: {SOURCE_DIR}")
    input("Naciśnij Enter, aby zakończyć...")
    sys.exit(1)

# Wczytanie to_translate
try:
    with open(TRANSLATE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
except Exception as e:
    print(f"Nie udało się wczytać pliku {TRANSLATE_FILE}: {e}")
    input("Naciśnij Enter, aby zakończyć...")
    exit(1)

# Podział na bloki po "### FILE:"
blocks = []
current_block = []
for line in lines:
    if line.startswith("### FILE:"):
        if current_block:
            blocks.append(current_block)
        current_block = [line]
    else:
        current_block.append(line)
if current_block:
    blocks.append(current_block)

# Tagi do podmiany
all_tags = ["name", "display_name", "itemname"]

# Przetwarzanie bloków
for block in blocks:
    file_name = block[0].replace("### FILE:", "").strip()
    source_file = os.path.join(SOURCE_DIR, file_name)

    if not os.path.exists(source_file):
        print(f"Plik {file_name} nie istnieje w folderze source. Pomijam.")
        continue

    # Wyciąganie tagów i lore z bloku
    tag_values = {tag: [] for tag in all_tags}
    lore_block = []
    in_lore = False
    for line in block[1:]:
        stripped = line.strip()
        if stripped.startswith("lore:"):
            in_lore = True
            continue
        if in_lore:
            # Poprawka: usuwamy myślnik i cudzysłowy z linii lore
            if stripped.startswith("-"):
                val = stripped[1:].strip().strip('"').strip("'")
                lore_block.append(val)
                continue
            elif stripped == "": # Puste linie w lore
                continue
            else:
                in_lore = False
        
        for tag in all_tags:
            if stripped.startswith(f"{tag}:"):
                val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                tag_values[tag].append(val)

    # Wczytanie pliku source jako YAML
    try:
        with open(source_file, "r", encoding="utf-8") as f:
            source_data = yaml.safe_load(f)
            if source_data is None:
                source_data = {}
    except Exception as e:
        print(f"Nie udało się wczytać pliku {file_name} jako YAML: {e}")
        continue

    # Kontroler stanu podmiany
    state = {"lore_replaced": False}

    # Funkcja rekurencyjna do podmiany tagów
    def recursive_replace(obj):
        if isinstance(obj, dict):
            # Tworzymy kopię kluczy, aby móc bezpiecznie modyfikować słownik
            keys = list(obj.keys())
            for k in keys:
                if k in all_tags and tag_values[k]:
                    old = obj[k]
                    obj[k] = tag_values[k].pop(0)
                    print(f" - {k} podmienione: '{old}' → '{obj[k]}'")
                elif k == "lore" and lore_block:
                    obj[k] = list(lore_block) # Kopiujemy listę lore
                    state["lore_replaced"] = True
                else:
                    recursive_replace(obj[k])
        elif isinstance(obj, list):
            for item in obj:
                recursive_replace(item)

    recursive_replace(source_data)

    # Zapis do folderu wynik
    out_path = os.path.join(OUTPUT_DIR, file_name)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            # Ustawienia dump zapewniają ładny format Minecraftowy
            yaml.dump(source_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"Przetworzono plik: {file_name}")
        print(f" - lore podmienione: {'Tak' if state['lore_replaced'] else 'Nie'}\n")
    except Exception as e:
        print(f"Nie udało się zapisać pliku {file_name}: {e}")

input("Przetwarzanie zakończone. Wyniki znajdziesz w folderze 'wynik'. Naciśnij Enter...")