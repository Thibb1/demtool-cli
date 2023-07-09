import os
import zipfile

#  check if PackDLMap.zip file exists
if os.path.exists('./place_zip/PackDLMap.zip'):
    with zipfile.ZipFile('./place_zip/PackDLMap.zip', 'r') as zip_ref:
        zip_ref.extractall("place_zip")

files = os.listdir(f'./place_zip')

for file in files:
    if file == 'PackDLMap.zip':
        continue
    if file.endswith(".zip"):
        with zipfile.ZipFile(f'./place_zip/{file}', 'r') as zip_ref:
            zip_ref.extractall("input")