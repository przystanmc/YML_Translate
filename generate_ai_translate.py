import os
import sys
import requests
import json
import time
from datetime import datetime

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)



# --- FUNKCJA TŁUMACZENIA ZA POMOCĄ TWOJEGO SERWERA ---
SERVER_URL = "https://translator-backend-7gyv.onrender.com/translate"

def check_server():
    log("Łączenie z serwerem tłumaczeń... (To może zająć do 60s, jeśli serwer śpi)")
    try:
        # Próbujemy pingnąć serwer krótkim timeoutem, aby sprawdzić czy żyje
        # Wysyłamy puste zapytanie lub po prostu tekst "ping"
        requests.post(SERVER_URL, json={"text": ""}, timeout=60)
        log("Serwer jest aktywny! Rozpoczynam tłumaczenie...")
    except Exception:
        log("Uwaga: Serwer potrzebuje chwili na rozruch, proszę o cierpliwość...")


# WYWOŁANIE SPRAWDZANIA:
check_server()

def translate_text(text):
    if not text or len(text.strip()) < 1: 
        return text
    
    try:
        # Teraz wysyłamy tekst do TWOJEGO serwera
        response = requests.post(
            url=SERVER_URL,
            json={"text": text},
            timeout=40  # Dłuższy timeout, bo darmowy Render musi się "obudzić"
        )
        
        if response.status_code == 200:
            # Twój serwer zwraca JSON {"translated": "tekst"}
            return response.json().get('translated', text)
        else:
            log(f"Błąd serwera (Status: {response.status_code})")
            return text
    except Exception as e:
        log(f"Błąd połączenia z serwerem: {e}")
        return text

# --- LOGIKA PLIKÓW (BEZ ZMIAN, ALE Z NOWĄ FUNKCJĄ) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(BASE_DIR, "source")
TRANSLATE_FILE = os.path.join(BASE_DIR, "to_translate.yml")

output_lines = []

if not os.path.exists(SOURCE_DIR):
    log("Błąd: Brak folderu source!")
    sys.exit()

files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".yml")]

if not files:
    log("Błąd: Brak plików w folderze source!")
    sys.exit()

for file_name in files:
    log(f"\nProcessing: {file_name}")
    output_lines.append(f"### FILE: {file_name}\n")
    
    try:
        with open(os.path.join(SOURCE_DIR, file_name), "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        log(f"Błąd odczytu pliku {file_name}: {e}")
        continue

    is_in_lore = False
    for line in lines:
        raw_line = line.rstrip()
        stripped = raw_line.strip()

        target_tags = ["name:", "display_name:", "itemname:"]
        found_tag = None
        for tag in target_tags:
            if stripped.startswith(tag):
                found_tag = tag
                break

        if found_tag:
            indent = raw_line[:raw_line.find(found_tag)]
            value = stripped.split(found_tag, 1)[1].strip().strip('"').strip("'")
            
            log(f"  > Translating {found_tag}...")
            translated = translate_text(value)
            output_lines.append(f"{indent}{found_tag} '{translated}'\n")
            # Skróciłem czas oczekiwania, bo Twój serwer ma własne limity
            time.sleep(0.5) 

        elif stripped == "lore:":
            output_lines.append(raw_line + "\n")
            is_in_lore = True
        
        elif is_in_lore and stripped.startswith("-"):
            indent = raw_line[:raw_line.find("-")]
            value = stripped[1:].strip().strip('"').strip("'")
            
            log(f"  > Translating lore line...")
            translated = translate_text(value)
            output_lines.append(f"{indent}- '{translated}'\n")
            time.sleep(0.5)

        else:
            if stripped != "" and not stripped.startswith("-"):
                is_in_lore = False

    output_lines.append("\n")

with open(TRANSLATE_FILE, "w", encoding="utf-8") as f:
    f.writelines(output_lines)

log("\n--- ZAKOŃCZONO ---")