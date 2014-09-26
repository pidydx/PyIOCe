#BASE_DIR = "./PyIOCe.app/Contents/Resources/"
pyinstaller -D -w pyioce.spec
cp indicator_terms* ./dist/PyIOCe.app/Contents/Resources
cp parameters* ./dist/PyIOCe.app/Contents/Resources
cp -r ./images ./dist/PyIOCe.app/Contents/Resources
