# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 14:59:41 2024

@author: Nicolas Bledin
"""

import pandas as pd
from scipy.spatial import KDTree
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import tensorflow as tf
from tensorflow.keras import layers, models



def merge_dataset(adress_dataset_filepath='adresses-ban.csv',
                  poi_paris_dataset_filepath='poi_paris 1.csv',
                  loyers_paris_adresses_filepath='loyers_paris_adresses.csv',
                  output_prefix='dataset/merged_part',
                  max_file_size_gb=1):

    # Load the data from the uploaded CSV files
    adresses_df = pd.read_csv(adress_dataset_filepath, delimiter=';')
    poi_df = pd.read_csv(poi_paris_dataset_filepath)
    loyers_df = pd.read_csv(loyers_paris_adresses_filepath)

    # Clean and filter each DataFrame
    adresses_df.columns = adresses_df.columns.str.strip().str.replace(r'[^A-Za-z0-9_]', '', regex=True)
    adresses_df_filtered = adresses_df[['cle_interop', 'commune_nom', 'voie_nom', 'numero', 'long', 'lat']].dropna()

    poi_df_filtered = poi_df[['name', 'latitude', 'longitude', 'type']].dropna()

    loyers_df_filtered = loyers_df[['Adresse', 'Nombre de pièces', 'Époque de construction',
                                    'Type de location', 'Loyer minimum (€/m²)', 'Loyer médian (€/m²)',
                                    'Loyer maximum (€/m²)']].dropna()

    loyers_df_filtered['voie_nom'] = loyers_df_filtered['Adresse'].apply(lambda x: x.split(',')[0])

    # Merge `adresses_df_filtered` and `loyers_df_filtered`
    merged_adresses_loyers = pd.merge(adresses_df_filtered, loyers_df_filtered, on='voie_nom', how='inner')

    # KDTree setup for POI search
    poi_coords = np.array(list(zip(poi_df_filtered['latitude'], poi_df_filtered['longitude'])))
    poi_tree = KDTree(poi_coords)

    def find_nearby_pois_kdtree(row, tree, poi_df, tolerance_km=0.5):
        tolerance_deg = tolerance_km / 111  # Convert km to degrees
        lat_lon = (row['lat'], row['long'])
        idxs = tree.query_ball_point(lat_lon, tolerance_deg)
        nearby_pois = poi_df.iloc[idxs]['type'].values
        return ', '.join(nearby_pois)

    # Add nearby POIs to the dataset
    merged_adresses_loyers['Nearby_POIs'] = merged_adresses_loyers.apply(
        find_nearby_pois_kdtree, tree=poi_tree, poi_df=poi_df_filtered, axis=1)

    # Write directly into multiple files of max 1 GB
    max_file_size_bytes = max_file_size_gb * 1024 * 1024 * 1024
    current_file_index = 1
    current_file_size = 0
    output_file = f"{output_prefix}_{current_file_index}.csv"
    header_written = False

    for chunk_start in range(0, len(merged_adresses_loyers), 10000):  # Process 10,000 rows at a time
        chunk = merged_adresses_loyers.iloc[chunk_start:chunk_start + 10000]
        chunk_size_bytes = chunk.memory_usage(deep=True).sum()

        # If adding this chunk exceeds the limit, start a new file
        if current_file_size + chunk_size_bytes > max_file_size_bytes:
            current_file_index += 1
            output_file = f"{output_prefix}_{current_file_index}.csv"
            current_file_size = 0
            header_written = False

        # Write the chunk to the current file
        chunk.to_csv(output_file, mode='a', header=not header_written, index=False, encoding='utf-8')
        current_file_size += chunk_size_bytes
        header_written = True

    print(f"Les fichiers CSV ont été générés avec le préfixe '{output_prefix}'.")


def predict_Paris_renting_good_price(merged_adress_loyers_filepath='merged_adresses_loyers.csv'):
    # Charger les données
    data = pd.read_csv(merged_adress_loyers_filepath)

    # Sélectionner les colonnes pour la prédiction
    X = data[['lat', 'long', 'Loyer minimum (€/m²)', 'Loyer maximum (€/m²)', 'commune_nom', 'Nearby_POIs']]
    y = data['Loyer médian (€/m²)']  # Colonne cible: prédiction du loyer médian

    # Diviser les données en ensembles d'entraînement et de test (80% entraînement, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Prétraitement : normalisation des données numériques et encodage des données catégorielles
    numeric_features = ['lat', 'long', 'Loyer minimum (€/m²)', 'Loyer maximum (€/m²)']
    categorical_features = ['commune_nom', 'Nearby_POIs']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # Appliquer le prétraitement aux données
    X_train_preprocessed = preprocessor.fit_transform(X_train)
    X_test_preprocessed = preprocessor.transform(X_test)

    # Créer un modèle de réseau de neurones pour la prédiction du loyer médian
    model = models.Sequential()

    # Couches denses pour le modèle
    model.add(layers.Dense(64, activation='relu', input_shape=(X_train_preprocessed.shape[1],)))
    model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Dense(16, activation='relu'))

    # Couche de sortie pour la régression (prédiction du loyer médian)
    model.add(layers.Dense(1))  # Pas d'activation car c'est une régression

    # Compiler le modèle avec l'optimiseur Adam et la perte MSE (mean squared error)
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    # Résumé du modèle
    model.summary()

    # Entraîner le modèle
    history = model.fit(X_train_preprocessed, y_train, epochs=50, validation_split=0.2, batch_size=32)

    # Évaluer le modèle sur les données de test
    test_loss, test_mae = model.evaluate(X_test_preprocessed, y_test)
    print(f'Erreur absolue moyenne sur les données de test: {test_mae}')


    # Visualiser la courbe de perte
    plt.plot(history.history['loss'], label='Train loss')
    plt.plot(history.history['val_loss'], label='Validation loss')
    plt.title('Courbe de perte')
    plt.xlabel('Époques')
    plt.ylabel('Perte')
    plt.legend()
    plt.show()

    # Visualiser la courbe de MAE (Erreur absolue moyenne)
    plt.plot(history.history['mae'], label='Train MAE')
    plt.plot(history.history['val_mae'], label='Validation MAE')
    plt.title('Erreur Absolue Moyenne (MAE)')
    plt.xlabel('Époques')
    plt.ylabel('MAE')
    plt.legend()
    plt.show()

if __name__=='__main__':
    pass