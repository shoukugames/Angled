#!/usr/bin/env bash
# Build the Linux binary (PyInstaller) and package it as a .deb
#   ./build_linux.sh      ->  dist/angled_<version>_amd64.deb
set -euo pipefail
cd "$(dirname "$0")"
VERSION=$(python3 -c "from angled.config import VERSION; print(VERSION)")
python3 tools/write_build_info.py
[ -f assets/levels.json ] || python3 tools/gen_levels.py

rm -rf build/linux dist/linux
pyinstaller --noconfirm --clean --onedir --windowed --name angled \
  --distpath dist/linux --workpath build/linux --specpath build/linux \
  --add-data "$PWD/assets:assets" --icon "$PWD/assets/icon.png" \
  --exclude-module numpy --exclude-module tkinter \
  run.py

PKG=build/deb/angled_${VERSION}_amd64
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" "$PKG/opt/angled" "$PKG/usr/bin" "$PKG/usr/share/applications" \
         "$PKG/usr/share/icons/hicolor/256x256/apps" "$PKG/usr/share/doc/angled"
cp -a dist/linux/angled/. "$PKG/opt/angled/"
cat > "$PKG/usr/bin/angled" <<'SH'
#!/bin/sh
exec /opt/angled/angled "$@"
SH
chmod 755 "$PKG/usr/bin/angled"
cp assets/icon.png "$PKG/usr/share/icons/hicolor/256x256/apps/angled.png"
cp README.md BUGREPORT.md CHANGELOG.md "$PKG/usr/share/doc/angled/"
cp LICENSE "$PKG/usr/share/doc/angled/copyright"
cat > "$PKG/usr/share/applications/angled.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Angled
Name[ja]=アングルド
GenericName=Angle bubble puzzle
Comment=Pop each bubble at the angle written inside it! (v${VERSION})
Comment[ja]=かくどを あわせて ポン！
Exec=angled
Icon=angled
Terminal=false
Categories=Game;PuzzleGame;Education;
Keywords=bubble;angle;puzzle;math;kids;
DESK
SIZE=$(du -sk "$PKG/opt" | cut -f1)
cat > "$PKG/DEBIAN/control" <<CTL
Package: angled
Version: ${VERSION}
Section: games
Priority: optional
Architecture: amd64
Installed-Size: ${SIZE}
Maintainer: Shouku Games <info@shoukugames.org>
Homepage: https://shoukugames.org/
Description: Angled v${VERSION} - pop each bubble at the angle written inside it
 A physics bubble-popping game about angles and trick shots by Shouku Games
 (created by Shawn Rapaz and Claude Code). Bank shots off the walls flip the
 angle. 100 levels, 99-second timer, VS CPU battle, top-10 scoreboard,
 English/Japanese, and a For Parents progress screen.
CTL
cat > "$PKG/DEBIAN/postinst" <<'SH'
#!/bin/sh
set -e
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q /usr/share/icons/hicolor || true
exit 0
SH
chmod 755 "$PKG/DEBIAN/postinst"
mkdir -p dist
dpkg-deb --build --root-owner-group "$PKG" "dist/angled_${VERSION}_amd64.deb"
echo "Built dist/angled_${VERSION}_amd64.deb"
