import gzip
import shutil

# Chemin vers le fichier .gz
fichier_gz = 'data\\000.osc.gz'
# Chemin vers le fichier décompressé
fichier_decompresse = 'data'

# Décompression du fichier .gz
with gzip.open(fichier_gz, 'rb') as f_in:
    with open(fichier_decompresse, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

print(f"Fichier décompressé : {fichier_decompresse}")

