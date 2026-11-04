@echo off
rem Build the Windows .exe natively on Windows (needs Python 3.11+, pip install pygame pyinstaller)
python tools\write_build_info.py
if not exist assets\levels.json python tools\gen_levels.py
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Angled-v0.1.2-win64 ^
  --add-data "assets;assets" --icon assets\icon.ico --version-file packaging\version_info.txt ^
  --exclude-module numpy --exclude-module tkinter run.py
