# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 14:59:41 2024

@author: nicol
"""

import pandas as pd

# Load the data from the uploaded CSV files
adresses_df = pd.read_csv('adresses-ban.csv')
poi_df = pd.read_csv('poi_paris 1.csv')
loyers_df = pd.read_csv('loyers_paris_adresses.csv')

# Display the first few rows of each DataFrame to understand their structures
adresses_head = adresses_df.head()
poi_head = poi_df.head()
loyers_head = loyers_df.head()

adresses_head, poi_head, loyers_head

##
# Step 1: Clean and filter each DataFrame

# Clean and split columns for adresses-ban.csv
# Specify the delimiter as `;` to separate columns
adresses_df = pd.read_csv('adresses-ban.csv', delimiter=';')

# Remove any leading special characters from column names in adresses_df
adresses_df.columns = adresses_df.columns.str.strip().str.replace(r'[^A-Za-z0-9_]', '', regex=True)
# Keep relevant columns (assuming 'cle_interop', 'commune_nom', 'voie_nom', 'numero', 'long', 'lat' are needed)
adresses_df_filtered = adresses_df[['cle_interop', 'commune_nom', 'voie_nom', 'numero', 'long', 'lat']].dropna()

# Clean poi_paris 1.csv
# Keep only name, latitude, longitude, and type as relevant columns
poi_df_filtered = poi_df[['name', 'latitude', 'longitude', 'type']].dropna()

# Clean loyers_paris_adresses.csv
# Keep address, type, number of pieces, and rent prices
loyers_df_filtered = loyers_df[['Adresse', 'Nombre de pièces', 'Époque de construction',
                                'Type de location', 'Loyer minimum (€/m²)', 'Loyer médian (€/m²)', 
                                'Loyer maximum (€/m²)']].dropna()

# Display cleaned data samples to ensure correctness
adresses_df_filtered.head(), poi_df_filtered.head(), loyers_df_filtered.head()

# Check column names for each DataFrame to troubleshoot issues with missing columns
adresses_columns = adresses_df.columns
poi_columns = poi_df.columns
loyers_columns = loyers_df.columns

adresses_columns, poi_columns, loyers_columns

# Re-attempt filtering the cleaned DataFrames
adresses_df_filtered = adresses_df[['cle_interop', 'commune_nom', 'voie_nom', 'numero', 'long', 'lat']].dropna()
poi_df_filtered = poi_df[['name', 'latitude', 'longitude', 'type']].dropna()
loyers_df_filtered = loyers_df[['Adresse', 'Nombre de pièces', 'Époque de construction',
                                'Type de location', 'Loyer minimum (€/m²)', 'Loyer médian (€/m²)', 
                                'Loyer maximum (€/m²)']].dropna()

# Display samples to ensure correct filtering
adresses_df_filtered.head(), poi_df_filtered.head(), loyers_df_filtered.head()

# Step 2: Merge `adresses_df_filtered` and `loyers_df_filtered` on street name and address
# Extract the street name from `Adresse` in loyers_df_filtered to facilitate matching
loyers_df_filtered['voie_nom'] = loyers_df_filtered['Adresse'].apply(lambda x: x.split(',')[0])

# Merge on 'voie_nom' and filter the merged data to keep relevant columns for the model
merged_adresses_loyers = pd.merge(adresses_df_filtered, loyers_df_filtered, on='voie_nom', how='inner')

# Display the merged result to ensure correctness
merged_adresses_loyers.head()

from scipy.spatial import KDTree
import numpy as np

# # Construction of the KDTree with the coordinates of POIs
poi_coords = np.array(list(zip(poi_df_filtered['latitude'], poi_df_filtered['longitude'])))
poi_tree = KDTree(poi_coords)

# Define function to find nearby POIS with KDTree
def find_nearby_pois_kdtree(row, tree, poi_df, tolerance_km=0.5):
    tolerance_deg = tolerance_km / 111  # Conversion km to degrees
    lat_lon = (row['lat'], row['long'])
    idxs = tree.query_ball_point(lat_lon, tolerance_deg)
    # Get the nearby POIs
    nearby_pois = poi_df.iloc[idxs]['type'].values
    return ', '.join(nearby_pois)


sample_result = merged_adresses_loyers.head(50).copy()
sample_result['Nearby_POIs'] = sample_result.apply(find_nearby_pois_kdtree, tree=poi_tree, poi_df=poi_df_filtered, axis=1)

# Display the result
sample_result[['cle_interop', 'voie_nom', 'Adresse', 'Loyer médian (€/m²)', 'Nearby_POIs']]

# Enregistrer le résultat dans un fichier CSV
sample_result.to_csv('sample_result.csv', index=False, encoding='utf-8')

# #apply it on merged_adresses_loyers
merged_adresses_loyers['Nearby_POIs'] = merged_adresses_loyers.apply(find_nearby_pois_kdtree, tree=poi_tree, poi_df=poi_df_filtered, axis=1)

# Enregistrer le résultat dans un fichier CSV
merged_adresses_loyers.to_csv('sample_result.csv', index=False, encoding='utf-8')

merged_adresses_loyers = pd.read_csv('merged_adresses_loyers.csv') 

