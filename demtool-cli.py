import argparse
import os
import subprocess
import re

parser = argparse.ArgumentParser(description='Convert and merge map data')

parser.add_argument('-p', '--projection', dest='projection', default='idokeido',
    help='Projection type: idokeido, UTM, heimen (default: idokeido)')
parser.add_argument('-z', '--zone', dest='zone', default='54',
    help='UTM zone number: 51 ~ 56 (default: 54)')
parser.add_argument('-c', '--coordinate' ,dest='coordinate', default='1',
    help='Plane coordinate number: 1 ~ 19 (default: 1)')
parser.add_argument('-s', '--shaded', dest='shaded', default='1',
    help='Shaded relief: 0 (off), 1 (on) (default: 1)')
parser.add_argument('-i', '--input', dest='input_directory', default='./input',
    help='Directory path containing input files (default: ./input)')
parser.add_argument('-l' , '--level', dest='ocean_level', default='0',
    help='Ocean level: 0 (Floor 0), 1 (Floor -9999) (default: 0)')



args = parser.parse_args()

# Check if arguments are valid
if args.projection not in ['idokeido', 'UTM', 'heimen']:
    print('Invalid projection type. Closing program.')
    exit()
zone = int(args.zone)
if args.projection == 'UTM':
    if zone < 51 or zone > 56:
        print('Invalid UTM zone number. Closing program.')
        exit()
coordinate = int(args.coordinate)
if args.projection == 'UTM':
    if coordinate < 1 or coordinate > 19:
        print('Invalid plane coordinate number. Closing program.')
        exit()
shaded = int(args.shaded)
if shaded != 0 and shaded != 1:
    print('Invalid shaded relief. Closing program.')
    exit()

# Check if dem.exe exists
if not os.path.exists('dem.exe'):
    print('demtools not found. Closing program.')
    exit()

# Set environment variable
env = os.environ.copy()
env['GDAL_DATA'] = 'data'
env['GDAL_FILENAME_IS_UTF8'] = 'YES'
env['PROJ_LIB'] = 'proj'

# Create output directory
if not os.path.exists('output'):
    os.makedirs('output')

# Check if merge.tif file exists
if os.path.exists('output/merge.tif'):
    print('merge.tif file exists. Please delete it first.')
    exit()

list_files = os.listdir(args.input_directory)
nb_files = len(list_files)
nb_processed = 0
bar_length = 20
jdg = ''
pattern = re.compile(r'^.*FG-GML.*xml$')
print('Converting files...')
for file in list_files:
    nb_processed += 1
    percent = 100.0 * nb_processed / nb_files
    completed_length = int(percent / (100.0 / bar_length))
    bar = '=' * completed_length + '-' * (bar_length - completed_length)
    print(f"Completed: [{bar}] {int(percent):>3}%", end="\r")
    if pattern.match(file):
        str_cmd = f'dem.exe "{args.input_directory}/{file}" {args.ocean_level}'
        flag = subprocess.run(str_cmd, shell=True, env=env, capture_output=True)
        if jdg == '':
            jdg = flag.returncode
        if flag.returncode != jdg:
            print(f'{file} projection is different ({flag.returncode} != {jdg}). Closing program.')
            exit()
print()
# Move new tif files to converted directory
if not os.path.exists('converted'):
    os.makedirs('converted')
list_files = os.listdir(args.input_directory)
for file in list_files:
    if file.endswith('.tif'):
        if os.path.exists(f'converted/{file}'):
            os.remove(f'converted/{file}')
        os.rename(f'{args.input_directory}/{file}', f'converted/{file}')

projection=''
if args.projection == 'idokeido':
    projection = 4612
    if jdg == "2011":
        projection = 6668
elif args.projection == 'UTM':
    projection = 3097 + zone - 51
    if jdg == "2011":
        projection += 3591
elif args.projection == 'heimen':
    projection = 2443 + coordinate - 1
    if jdg == "2011":
        projection += 4226
projection = f'epsg:{projection}'
print(f'Projection: {projection}, JDG: {jdg}')

# Merge LatLong
print('Merging LatLong files...')
str_cmd = f'gdalbuildvrt.exe -overwrite converted/mergeLL.vrt converted/*.tif'
flag = subprocess.run(str_cmd, shell=True, env=env, capture_output=True)
if flag.returncode != 0:
    print('Failed to merge LatLong files. Closing program.')
    exit()
print(f'Merged LatLong files: converted/mergeLL.vrt')

# Merge tif files
print('Merging files...')
nodata = 'None' if args.ocean_level == '0' else '-9999 -dstnodata -9999'
str_cmd = 'gdalwarp.exe -r bilinear ' \
    f'-srcnodata {nodata} ' \
    f'-t_srs {projection} converted/mergeLL.vrt output/final.tif'
flag = subprocess.run(str_cmd, shell=True, env=env, capture_output=True)
if flag.returncode != 0:
    print('Failed to merge files. Closing program.')
    exit()
print(f'Merged files: output/final.tif')

# Create hillshade
if shaded == 1:
    print('Creating hillshade...')
    str_cmd = f'gdaldem.exe hillshade -s 1 output/final.tif output/final_hillshade.tif'
    flag = subprocess.run(str_cmd, shell=True, env=env, capture_output=True)
    if flag.returncode != 0:
        print('Failed to create hillshade. Closing program.')
        exit()
    print(f'Created hillshade: output/final_hillshade.tif')

print('Finished!')