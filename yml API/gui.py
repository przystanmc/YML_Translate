import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import threading
import pygame
from tkinter import ttk
import ctypes

# Próba importu do ciemnego paska (Windows 10/11)
def set_dark_title_bar(window):
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(window.winfo_id())
    rendering_policy = ctypes.c_int(1)
    set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

# ---------- LOGGER ----------
class GuiLogger:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.config(state="normal")
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.config(state="disabled")

    def flush(self):
        pass


# ---------- FUNKCJE ----------
def run_generate_ai():
    threading.Thread(target=_run_generate_ai_task, daemon=True).start()

def _run_generate_ai_task():
    try:
        process = subprocess.Popen(
            [sys.executable, os.path.join(BASE_DIR, "generate_ai_translate.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(line, end="")  # trafia do GuiLogger

        process.wait()

        if process.returncode == 0:
            messagebox.showinfo(
                "Gotowe",
                "Plik to_translate.yml został wygenerowany."
            )
        else:
            messagebox.showerror("Błąd", "Wystąpił błąd podczas generowania.")

    except Exception as e:
        messagebox.showerror("Błąd", str(e))


def run_generate():
    threading.Thread(target=_run_generate_task, daemon=True).start()

def _run_generate_task():
    try:
        process = subprocess.Popen(
            [sys.executable, os.path.join(BASE_DIR, "generate_to_translate.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(line, end="")  # trafia do GuiLogger

        process.wait()

        if process.returncode == 0:
            messagebox.showinfo(
                "Gotowe",
                "Plik to_translate.yml został wygenerowany."
            )
        else:
            messagebox.showerror("Błąd", "Wystąpił błąd podczas generowania.")

    except Exception as e:
        messagebox.showerror("Błąd", str(e))



def run_apply():
    threading.Thread(target=_run_apply, daemon=True).start()

def _run_apply():
    print(">>> Dodawanie tłumaczenia...")
    try:
        process = subprocess.Popen(
            [sys.executable, os.path.join(BASE_DIR, "apply_translation.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(line, end="")  # trafia do GuiLogger

        process.wait()

        if process.returncode == 0:
            messagebox.showinfo(
                "Gotowe",
                "Tłumaczenie zostało zastosowane.\nSprawdź folder 'wynik'."
            )
        else:
            messagebox.showerror("Błąd", "Wystąpił błąd podczas generowania.")

    except Exception as e:
        messagebox.showerror("Błąd", str(e))

# Funkcja przełączania Fullscreen
def toggle_fullscreen(event=None):
    is_full = root.attributes("-fullscreen")
    root.attributes("-fullscreen", not is_full)


# ---------- GUI ----------
root = tk.Tk()
root.title("YML Translator API")
root.geometry("700x600")
root.configure(bg="#1e1e1e")

# Inicjalizacja odtwarzacza przed resztą GUI
song_name_var = tk.StringVar(value="Brak muzyki")
# ---- PANEL MUZYCZNY (Nad konsolą) ----
music_frame = tk.Frame(root, bg="#1e1e1e")
music_frame.grid(row=4, column=0, sticky="ew", padx=15, pady=5)

# Nazwa piosenki (po lewej stronie panelu)
song_label = tk.Label(music_frame, textvariable=song_name_var, font=("Consolas", 9), fg="#888", bg="#1e1e1e")
song_label.pack(side="left", padx=5)

player = MusicPlayer(song_name_var, root)

# Włącz ciemny pasek tytułowy
try: set_dark_title_bar(root)
except: pass

# Konfiguracja siatki
root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=0)
root.grid_rowconfigure(2, weight=0)
root.grid_rowconfigure(3, weight=0)
root.grid_rowconfigure(4, weight=0) # Panel muzyczny - stała wysokość
root.grid_rowconfigure(5, weight=1) # Konsola - rozciąga się
root.grid_columnconfigure(0, weight=1)

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
    width=30, height=2, command=run_generate,
    bg="#333", fg="white", activebackground="#00ff88", font=("Segoe UI", 9, "bold"),
    relief="flat"
)
btn_generate_yml.pack(pady=5)

btn_apply = tk.Button(
    left_buttons_frame, text="Zastosuj tłumaczenie",
    width=30, height=2, command=run_apply,
    bg="#333", fg="white", activebackground="#00ff88", font=("Segoe UI", 9, "bold"),
    relief="flat"
)
btn_apply.pack(pady=5)

# Prawa strona - jeden duży przycisk AI
btn_ai_generate = tk.Button(
    buttons_frame, text="GENERUJ\nTŁUMACZENIE AI",
    width=25, height=5, command=run_generate_ai, # Tutaj podepnij odpowiednią funkcję
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

# ---- KONSOLA ----
log_frame = tk.Frame(root, bg="#000")
log_frame.grid(row=5, column=0, padx=15, pady=(5, 15), sticky="nsew") # pady: 5 u góry, 15 u dołu
log_frame.grid_rowconfigure(0, weight=1)
log_frame.grid_columnconfigure(0, weight=1)

log_box = tk.Text(log_frame, bg="#000", fg="#00ff88", font=("Consolas", 10), bd=0, highlightthickness=0, state="disabled", wrap="word")
log_box.grid(row=0, column=0, sticky="nsew")

scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_box.yview, style="Vertical.TScrollbar")
scrollbar.grid(row=0, column=1, sticky="ns")
log_box.config(yscrollcommand=scrollbar.set)

sys.stdout = GuiLogger(log_box)
sys.stderr = sys.stdout

# CIEMNY SUWAK TTK
scrollbar = ttk.Scrollbar(
    log_frame, 
    orient="vertical", 
    command=log_box.yview, 
    style="Vertical.TScrollbar"
)
scrollbar.grid(row=0, column=1, sticky="ns")

log_box.config(yscrollcommand=scrollbar.set)

# Przechwycenie print()
sys.stdout = GuiLogger(log_box)
sys.stderr = sys.stdout

# Start muzyki
threading.Thread(target=player.play, daemon=True).start()

root.mainloop()