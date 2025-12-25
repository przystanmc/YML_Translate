import tkinter as tk
from tkinter import ttk
import os
import sys
import threading
import pygame
import ctypes
import requests
import time
import yaml
from datetime import datetime

# --- KONFIGURACJA ŚCIEŻEK ---
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_DIR = os.path.join(BASE_DIR, "source")
OUTPUT_DIR = os.path.join(BASE_DIR, "wynik")
TRANSLATE_FILE = os.path.join(BASE_DIR, "to_translate.yml")
SERVER_URL = "https://translator-backend-7gyv.onrender.com/translate"

for d in [SOURCE_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)
# Próba importu do ciemnego paska (Windows 10/11)
def set_dark_title_bar(window):
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(window.winfo_id())
    rendering_policy = ctypes.c_int(1)
    set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))


# ---------- LOGIKA MUZYKI ----------
class MusicPlayer:
    def __init__(self, label_var, root): 
        pygame.mixer.init()
        self.label_var = label_var
        self.root = root
        # Lista piosenek - program szuka wszystkich plików muzycznych w folderze
        extensions = ('.mp3', '.mod', '.xm', '.it', '.s3m', '.wav')
        self.playlist = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(extensions)]
        self.current_index = 0
        self.is_paused = False

        self.check_music()
    def play(self):
        if self.playlist:
            path = os.path.join(BASE_DIR, self.playlist[self.current_index])
            pygame.mixer.music.load(path)
            # Zmieniamy z -1 na 0 (0 oznacza zagranie piosenki raz)
            pygame.mixer.music.play(0)
            
            # AKTUALIZACJA NAZWY W GUI:
            track_name = self.playlist[self.current_index]
            self.label_var.set(f"Gram: {track_name}") 
            print(f">>> Gram: {track_name}")

    def check_music(self):
        # Jeśli muzyka przestała grać i nie jest wciśnięta pauza -> następny utwór
        if not pygame.mixer.music.get_busy() and not self.is_paused:
            self.next_track()
        
        # Sprawdzaj co 2 sekundy (2000 ms)
        self.root.after(2000, self.check_music)

    def toggle_pause(self, btn):
        if self.is_paused:
            pygame.mixer.music.unpause()
            btn.config(text="PAUZA")
        else:
            pygame.mixer.music.pause()
            btn.config(text="GRAJ")
        self.is_paused = not self.is_paused

    def next_track(self):
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play()

# --- SYSTEM LOGOWANIA DO GUI ---
class SafeLogger:
    def __init__(self, widget=None):
        self.widget = widget
        self.terminal = sys.__stdout__

    def write(self, msg):
        if self.widget:
            self.widget.config(state="normal")
            self.widget.insert(tk.END, msg)
            self.widget.see(tk.END)
            self.widget.config(state="disabled")
        if self.terminal:
            self.terminal.write(msg)

    def flush(self):
        if self.terminal: self.terminal.flush()

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

# --- LOGIKA TŁUMACZENIA (TWOJE AI) ---
def translate_text(text):
    if not text or len(text.strip()) < 1: 
        return text
    try:
        response = requests.post(url=SERVER_URL, json={"text": text}, timeout=40)
        if response.status_code == 200:
            return response.json().get('translated', text)
        return text
    except Exception as e:
        log(f"Błąd połączenia: {e}")
        return text

# --- FUNKCJE OPERACYJNE ---

def run_extract():
    log(">>> Rozpoczynam wyciąganie tekstu...")
    if not os.path.exists(SOURCE_DIR):
        log(f"BŁĄD: Nie znaleziono folderu source: {SOURCE_DIR}")
        return

    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".yml")]
    if not files:
        log("Brak plików .yml w folderze source.")
        return
    
    log(f"Znaleziono {len(files)} plików do przetworzenia.")

    output_lines = []
    
    for file_name in files:
        source_path = os.path.join(SOURCE_DIR, file_name)
        
        # Zmienna do raportowania (przywracamy Twoją logikę)
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
            raw_line = line.rstrip()
            stripped = raw_line.strip()

            # Sprawdzanie tagów i zbieranie danych do raportu
            found_tag = False
            for tag in ["name:", "itemname:", "display_name:"]:
                if stripped.startswith(tag):
                    output_lines.append(line)
                    val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
                    captured_data[tag.replace(":", "")].append(val)
                    found_tag = True
                    break
            
            if found_tag:
                continue

            # Sprawdzanie sekcji lore
            if stripped == "lore:":
                output_lines.append(line)
                capture_lore = True
                captured_data["lore_found"] = True
                continue

            if capture_lore:
                if stripped.startswith("-"):
                    output_lines.append(line)
                else:
                    capture_lore = False

        output_lines.append("\n")
        
        # --- DYNAMICZNY RAPORT W GUI (Przywrócony) ---
        log(f"\n--- Przetworzono plik: {file_name} ---")
        
        for key in ["name", "itemname", "display_name"]:
            if captured_data[key]:
                log(f"    - Zapisano {key} ({len(captured_data[key])}):")
                for value in captured_data[key]:
                    log(f"        > {value}")
        
        if captured_data["lore_found"]:
            log(f"    - Zapisano lore: Tak")
        else:
            log(f"    - Zapisano lore: Nie znaleziono")
        
        log("-" * (25 + len(file_name)))

    # Zapis finalny
    with open(TRANSLATE_FILE, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    log(f"\nPlik {TRANSLATE_FILE} został wygenerowany pomyślnie!")

def run_ai_translate():
    if not os.path.exists(TRANSLATE_FILE):
        log("BŁĄD: Brak pliku to_translate.yml! Najpierw wyciągnij tekst.")
        return
    
    log(">>> Łączenie z serwerem AI... (Cierpliwości, Render może się budzić)")
    
    try:
        with open(TRANSLATE_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        log(f"BŁĄD odczytu pliku: {e}")
        return

    new_content = []
    current_file = "Nieznany"
    translated_count = 0
    
    for line in lines:
        raw = line.rstrip()
        stripped = raw.strip()
        
        # Śledzenie nazwy pliku dla lepszych logów
        if stripped.startswith("### FILE:"):
            current_file = stripped.replace("### FILE:", "").strip()
            new_content.append(line)
            continue

        target_tags = ["name:", "display_name:", "itemname:"]
        found_tag = next((t for t in target_tags if stripped.startswith(t)), None)

        if found_tag:
            indent = raw[:raw.find(found_tag)]
            value = stripped.split(found_tag, 1)[1].strip().strip('"').strip("'")
            
            # Logowanie przed tłumaczeniem, żeby użytkownik wiedział, że program "myśli"
            log(f"[{current_file}] Tłumaczenie {found_tag}...")
            
            translated = translate_text(value)
            
            # Raport: Oryginał -> Wynik
            log(f"    > '{value}' -> '{translated}'")
            
            new_content.append(f"{indent}{found_tag} '{translated}'\n")
            translated_count += 1
            time.sleep(0.3) # Przerwa na odświeżenie GUI

        elif stripped.startswith("-") and "###" not in line and stripped != "-":
            indent = raw[:raw.find("-")]
            value = stripped[1:].strip().strip('"').strip("'")
            
            log(f"[{current_file}] Tłumaczenie lore...")
            translated = translate_text(value)
            
            log(f"    > Lore: '{value}' -> '{translated}'")
            
            new_content.append(f"{indent}- '{translated}'\n")
            translated_count += 1
            time.sleep(0.3)
        else:
            new_content.append(line + "\n")

    try:
        with open(TRANSLATE_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_content)
        
        log(f"\n>>> ZAKOŃCZONO TŁUMACZENIE AI <<<")
        log(f"Przetworzono łącznie {translated_count} fraz.")
    except Exception as e:
        log(f"BŁĄD zapisu pliku tłumaczeń: {e}")
def run_apply():
    log(">>> ROZPOCZYNAM SKŁADANIE PLIKÓW WYNIKOWYCH...")
    if not os.path.exists(TRANSLATE_FILE):
        log("BŁĄD: Brak pliku tłumaczenia (to_translate.yml)!")
        return

    try:
        with open(TRANSLATE_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        log(f"BŁĄD odczytu pliku tłumaczeń: {e}")
        return

    blocks = content.split("### FILE:")[1:]
    if not blocks:
        log("BŁĄD: Nie znaleziono żadnych bloków danych w pliku tłumaczeń.")
        return

    for block in blocks:
        lines = block.strip().split("\n")
        if not lines: continue
        
        file_name = lines[0].strip()
        data_lines = lines[1:]

        log(f"\n--- Składanie pliku: {file_name} ---")

        # Wczytujemy oryginał
        source_path = os.path.join(SOURCE_DIR, file_name)
        if not os.path.exists(source_path):
            log(f"POMIJAM: Plik {file_name} nie istnieje w folderze source.")
            continue

        try:
            with open(source_path, "r", encoding="utf-8") as f:
                source_yaml = yaml.safe_load(f) or {}
        except Exception as e:
            log(f"BŁĄD YAML w {file_name}: {e}")
            continue

        # Parsowanie tłumaczeń z bloku
        translations = {"lore": []}
        has_lore_in_block = False
        
        for dl in data_lines:
            stripped_dl = dl.strip()
            if not stripped_dl: continue
            
            if stripped_dl.startswith("-"):
                val = stripped_dl[1:].strip().strip("'").strip('"')
                translations["lore"].append(val)
                has_lore_in_block = True
            elif ":" in stripped_dl:
                k, v = stripped_dl.split(":", 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                if k == "lore":
                    has_lore_in_block = True
                else:
                    translations[k] = v

        # Statystyki dla logów
        stats = {"replaced_keys": 0, "lore_updated": False}

        # Rekurencyjna podmiana w YAML
        def update_yaml(obj):
            if isinstance(obj, dict):
                for k in list(obj.keys()):
                    # Podmiana zwykłych tagów
                    if k in translations and k != "lore":
                        old_val = obj[k]
                        obj[k] = translations[k]
                        log(f"    - Podmieniono {k}:")
                        log(f"        '{old_val}' -> '{obj[k]}'")
                        stats["replaced_keys"] += 1
                    # Podmiana lore
                    elif k == "lore" and has_lore_in_block:
                        obj[k] = translations["lore"]
                        stats["lore_updated"] = True
                    else:
                        update_yaml(obj[k])
            elif isinstance(obj, list):
                for item in obj:
                    update_yaml(item)

        update_yaml(source_yaml)

        # Raport końcowy dla pliku
        if stats["lore_updated"]:
            log(f"    - Zaktualizowano sekcję lore: Tak ({len(translations['lore'])} linii)")
        
        if stats["replaced_keys"] == 0 and not stats["lore_updated"]:
            log("    - Nie znaleziono pasujących kluczy do podmiany.")

        # Zapis do folderu wynik
        output_path = os.path.join(OUTPUT_DIR, file_name)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                # Zachowujemy styl Minecraftowy (brak sortowania kluczy, obsługa unicode)
                yaml.dump(source_yaml, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            log(f"SUKCES: Zapłacono wynik do folderu 'wynik/{file_name}'")
        except Exception as e:
            log(f"BŁĄD zapisu {file_name}: {e}")
        
        log("-" * (25 + len(file_name)))

    log("\n>>> PROCES SKŁADANIA ZAKOŃCZONY POMYŚLNIE <<<")
# Funkcja przełączania Fullscreen
def toggle_fullscreen(event=None):
    is_full = root.attributes("-fullscreen")
    root.attributes("-fullscreen", not is_full)    

import random

class Equalizer:
    def __init__(self, parent, num_bars=15):
        self.canvas = tk.Canvas(parent, width=120, height=30, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(side="left", padx=10)
        self.bars = []
        self.num_bars = num_bars
        self.bar_width = 6
        
        for i in range(num_bars):
            x0 = i * (self.bar_width + 2)
            y0 = 30
            x1 = x0 + self.bar_width
            y1 = 30
            bar = self.canvas.create_rectangle(x0, y0, x1, y1, fill="#00ff88", outline="")
            self.bars.append(bar)
        
        # Nie wywołujemy self.animate() tutaj! 
        # Zrobimy to po zainicjowaniu playera.

    def animate(self):
        try:
            # Sprawdzamy czy mixer działa i czy player istnieje
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy() and not getattr(player, 'is_paused', False):
                for bar in self.bars:
                    new_h = random.randint(2, 28)
                    x0, _, x1, _ = self.canvas.coords(bar)
                    self.canvas.coords(bar, x0, 30 - new_h, x1, 30)
            else:
                for bar in self.bars:
                    x0, _, x1, _ = self.canvas.coords(bar)
                    self.canvas.coords(bar, x0, 28, x1, 30)
        except:
            pass # Ignoruj błędy jeśli player jeszcze się ładuje
        
        self.canvas.after(100, self.animate)

# --- GUI ---
root = tk.Tk()
root.title("YML Translator API")
root.geometry("700x600")
root.configure(bg="#1e1e1e")

# Konfiguracja logowania do log_box
sys.stdout = SafeLogger()
def thread_it(func):
    threading.Thread(target=func, daemon=True).start()
# ---------- GUI ----------
# Konfiguracja siatki
root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=0)
root.grid_rowconfigure(2, weight=0)
root.grid_rowconfigure(3, weight=0)
root.grid_rowconfigure(4, weight=0) # Panel muzyczny - stała wysokość
root.grid_rowconfigure(5, weight=1) # Konsola - rozciąga się
root.grid_columnconfigure(0, weight=1)

# 1. NAJPIERW TWORZYMY RAMKĘ (Kontener)
music_frame = tk.Frame(root, bg="#1e1e1e")
music_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=5)

# 2. INICJALIZUJEMY ZMIENNĄ TEKSTOWĄ
song_name_var = tk.StringVar(value="Brak muzyki")

# 3. DODAJEMY ETYKIETĘ DO RAMKI
song_label = tk.Label(music_frame, textvariable=song_name_var, font=("Consolas", 9), fg="#888", bg="#1e1e1e")
song_label.pack(side="left", padx=5)

# 4. TWORZYMY EQUALIZER (Wewnątrz music_frame)
visualizer = Equalizer(music_frame)

# 5. TWORZYMY PLAYERA (Zmienna 'player' musi być dostępna dla equalizera)
player = MusicPlayer(song_name_var, root)

# 6. URUCHAMIAMY ANIMACJĘ Z OPÓŹNIENIEM
root.after(1000, visualizer.animate)

# Włącz ciemny pasek tytułowy
try: set_dark_title_bar(root)
except: pass



root.bind("<F11>", toggle_fullscreen)

title = tk.Label(
    root, text="YML TRANSLATOR API", 
    font=("Segoe UI", 18, "bold"), fg="#00ff88", bg="#1e1e1e"
)
title.grid(row=0, column=0, pady=10)

# --- NAGŁÓWEK ---
title = tk.Label(
    root, text="YML TRANSLATOR API", 
    font=("Segoe UI", 18, "bold"), fg="#00ff88", bg="#1e1e1e"
)
title.grid(row=0, column=0, pady=20)

# --- PANEL PRZYCISKÓW (Kontener na przyciski) ---
buttons_frame = tk.Frame(root, bg="#1e1e1e")
buttons_frame.grid(row=1, column=0, pady=5, padx=20, sticky="nsew")
buttons_frame.grid_columnconfigure(0, weight=1) # Lewa strona
buttons_frame.grid_columnconfigure(1, weight=1) # Prawa strona

# Lewa strona - pionowo dwa przyciski
left_buttons_frame = tk.Frame(buttons_frame, bg="#1e1e1e")
left_buttons_frame.grid(row=0, column=0, padx=10)

btn_generate_yml = tk.Button(
    left_buttons_frame, text="Wyciągnij tekst do tłumaczenia",
    width=30, height=2, command=lambda: thread_it(run_extract),
    bg="#333", fg="white", activebackground="#00ff88", font=("Segoe UI", 9, "bold"),
    relief="flat"
)
btn_generate_yml.pack(pady=5)

btn_apply = tk.Button(
    left_buttons_frame, text="Zastosuj tłumaczenie",
    width=30, height=2, command=lambda: thread_it(run_apply),
    bg="#333", fg="white", activebackground="#00ff88", font=("Segoe UI", 9, "bold"),
    relief="flat"
)
btn_apply.pack(pady=5)

# Prawa strona - jeden duży przycisk AI
btn_ai_generate = tk.Button(
    buttons_frame, text="GENERUJ\nTŁUMACZENIE AI",
    width=25, height=5, command=lambda: thread_it(run_ai_translate), # Tutaj podepnij odpowiednią funkcję
    bg="#005f44", fg="#00ff88", activebackground="#00ff88", font=("Segoe UI", 10, "bold"),
    relief="flat", bd=2
)
btn_ai_generate.grid(row=0, column=1, padx=10, sticky="ns")

# --- INFO ---
info = tk.Label(
    root, text="F11: Pełny ekran | Logi poniżej",
    font=("Segoe UI", 9), fg="#888", bg="#1e1e1e"
)
info.grid(row=3, column=0, pady=10)

# Dalej idzie reszta Twojego kodu (Style, Music Player, Log Box...)
style = ttk.Style()
style.theme_use('clam') # 'clam' najlepiej współpracuje z ciemnymi kolorami

style.configure(
    "Vertical.TScrollbar",
    gripcount=0,
    background="#333333",    # Kolor uchwytu
    troughcolor="#1e1e1e",  # Kolor tła suwaka
    bordercolor="#1e1e1e",
    arrowcolor="#00ff88"     # Kolor strzałek (pasuje do Twoich logów)
)

style.map("Vertical.TScrollbar",
    background=[('active', '#444444')] # Kolor po najechaniu myszką
)


# Przyciski sterowania (po prawej stronie panelu)
btn_next = tk.Button(music_frame, text="NASTĘPNA", width=10, bg="#333", fg="#00ff88", font=("Segoe UI", 8, "bold"), relief="flat", 
                     command=player.next_track)
btn_next.pack(side="right", padx=2)

btn_pause = tk.Button(music_frame, text="PAUZA", width=8, bg="#333", fg="#00ff88", font=("Segoe UI", 8, "bold"), relief="flat", 
                      command=lambda: player.toggle_pause(btn_pause))
btn_pause.pack(side="right", padx=2)


log_box = tk.Text(root, bg="#000", fg="#00ff88", font=("Consolas", 10), state="disabled", wrap="word")
log_box.grid(row=5, column=0, padx=15, pady=15, sticky="nsew")  # row=5 bo to rząd dla konsoli
sys.stdout.widget = log_box

# Aby pasek przewijania działał poprawnie
scrollbar = ttk.Scrollbar(root, command=log_box.yview)
scrollbar.grid(row=5, column=1, sticky='ns', pady=15)
log_box.config(yscrollcommand=scrollbar.set)



log("Program gotowy. Umieść pliki w folderze 'source'.")
root.mainloop()