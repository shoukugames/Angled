#!/usr/bin/env bash
# Build the Windows .exe with PyInstaller running under Wine (from Linux).
# Requires a Windows Python in Wine at C:\py311 with pygame + pyinstaller:
#   see README.md "Building" for the one-time setup.
#   ./build_windows.sh    ->  dist/Angled-v<version>-win64.exe
# On Windows itself, run the same pyinstaller command in build_windows.bat.
set -euo pipefail
cd "$(dirname "$0")"
VERSION=$(python3 -c "from angled.config import VERSION; print(VERSION)")
python3 tools/write_build_info.py
[ -f assets/levels.json ] || python3 tools/gen_levels.py
WINPY='C:\py311\python.exe'
SRC=$(winepath -w "$PWD")
rm -rf build/win dist/win
cat > build/_win_build.bat <<BAT
cd /d "${SRC}"
${WINPY} -m PyInstaller --noconfirm --clean --onefile --windowed --name Angled-v${VERSION}-win64 ^
  --distpath dist\\win --workpath build\\win --specpath build\\win ^
  --add-data "${SRC}\\assets;assets" --icon "${SRC}\\assets\\icon.ico" ^
  --version-file "${SRC}\\packaging\\version_info.txt" ^
  --exclude-module numpy --exclude-module tkinter ^
  run.py > build\\win_build.log 2>&1
BAT
mkdir -p build
WINEDEBUG=-all wine cmd /c "$(winepath -w build/_win_build.bat)" </dev/null >/dev/null 2>&1 || true
tail -3 build/win_build.log || true
mkdir -p dist
cp "dist/win/Angled-v${VERSION}-win64.exe" "dist/Angled-v${VERSION}-win64.exe"
echo "Built dist/Angled-v${VERSION}-win64.exe"
