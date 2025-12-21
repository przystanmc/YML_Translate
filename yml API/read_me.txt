YML Translator API

Ten skrypt służy do tłumaczenia plików .yml (np. pluginy Minecraft).

Jak to działa:

1. Wrzucasz pliki .yml do folderu "source"
2. Uruchamiasz generate_to_translate.py
   - powstaje plik to_translate.yml
   - zawiera name, itemname, display_name oraz lore
3. Tłumaczysz tekst w pliku to_translate.yml
4. Uruchamiasz apply_translation.py
   - gotowe pliki zapisują się w folderze "wynik"

Struktura folderów:

YML_Translator_API
├── source        (tu wrzucasz pliki .yml)
├── wynik         (tu pojawią się przetłumaczone pliki)
├── generate_to_translate.py
├── apply_translation.py
├── to_translate.yml
└── README.md

Wymagania:
- Python 3.x

Uruchamianie:
python generate_to_translate.py
python apply_translation.py
