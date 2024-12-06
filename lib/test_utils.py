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
import os

from collections import Counter

def calculate_poi_counts(row, tree, poi_df, tolerance_km=0.5):
    """
    Calcule le nombre de POIs proches pour chaque type.
    """
    tolerance_deg = tolerance_km / 111  # Convert kilometers to degrees (approximation for latitude/longitude)
    lat_lon = (row['lat'], row['long'])
    idxs = tree.query_ball_point(lat_lon, tolerance_deg)
    nearby_pois = poi_df.iloc[idxs]['type'].values

    # Compter le nombre de POIs par type
    poi_counts = Counter(nearby_pois)
    return poi_counts

def merge_dataset(adress_dataset_filepath='adresses-ban.csv',
                  poi_paris_dataset_filepath='poi_paris 1.csv',
                  loyers_paris_adresses_filepath='loyers_paris_adresses.csv',
                  output_prefix='dataset/merged_part',
                  max_file_size_gb=1):

    # Vérification et création du dossier
    os.makedirs('dataset', exist_ok=True)

    # Chargement des fichiers CSV
    adresses_df = pd.read_csv(adress_dataset_filepath, delimiter=';')
    poi_df = pd.read_csv(poi_paris_dataset_filepath)
    loyers_df = pd.read_csv(loyers_paris_adresses_filepath)

    # Nettoyage des colonnes et filtrage
    adresses_df.columns = adresses_df.columns.str.strip().str.replace(r'[^A-Za-z0-9_]', '', regex=True)
    adresses_df_filtered = adresses_df[['cle_interop', 'commune_nom', 'voie_nom', 'numero', 'long', 'lat']].dropna()

    # Liste des types de POI intéressants
    interesting_pois = [
        'restaurant', 'cafe', 'bar', 'fast_food', 'pharmacy', 'school', 'library', 'bank', 'clinic',
        'hospital', 'theatre', 'cinema', 'marketplace', 'university', 'childcare', 'art_school',
        'music_school', 'dentist', 'driving_school', 'park', 'fitness_centre', 'pub', 'community_centre',
        'yoga_studio', 'dojo', 'sports_centre'
    ]

    # Filtrer les POI en fonction des types intéressants
    poi_df_filtered = poi_df[poi_df['type'].isin(interesting_pois)].dropna(subset=['latitude', 'longitude', 'type'])

    # Nettoyer et filtrer les loyers
    loyers_df_filtered = loyers_df[['Adresse', 'Nombre de pièces', 'Époque de construction',
                                    'Type de location', 'Loyer minimum (€/m²)', 'Loyer médian (€/m²)',
                                    'Loyer maximum (€/m²)']].dropna()

    loyers_df_filtered['voie_nom'] = loyers_df_filtered['Adresse'].apply(lambda x: x.split(',')[0])

    # Fusion des adresses et des loyers
    merged_adresses_loyers = pd.merge(adresses_df_filtered, loyers_df_filtered, on='voie_nom', how='inner')

    # Dictionnaire des poids des POI
    poi_weights = {
        'restaurant': 5, 'cafe': 3, 'bar': 2, 'fast_food': 1, 'pharmacy': 2,
        'school': 2, 'library': 3, 'bank': 1, 'clinic': 3, 'hospital': 4,
        'cinema': 4, 'theatre': 3, 'marketplace': 2, 'university': 5,
        'childcare': 2, 'art_school': 4, 'music_school': 4, 'dentist': 3,
        'driving_school': 2, 'park': 3, 'fitness_centre': 4, 'pub': 2,
        'community_centre': 3, 'yoga_studio': 3, 'dojo': 3, 'sports_centre': 4
    }

    # KDTree pour trouver les POI proches
    poi_coords = np.array(list(zip(poi_df_filtered['latitude'], poi_df_filtered['longitude'])))
    poi_tree = KDTree(poi_coords)
    
    # Application de la fonction pour calculer le nombre de POI pour chaque appartement
    merged_adresses_loyers['Nearby_POI_Counts'] = merged_adresses_loyers.apply(
        calculate_poi_counts, tree=poi_tree, poi_df=poi_df_filtered, axis=1
    )
    # Création de colonne pour chaque type de POI
    poi_types = interesting_pois  # List de types de POI
    
    for poi_type in poi_types:
        merged_adresses_loyers[f'num_{poi_type}'] = merged_adresses_loyers['Nearby_POI_Counts'].apply(
            lambda x: x.get(poi_type, 0)  # Obtenir le nombre pour le POI, 0 par défault s'il n'y en a pas.
        )
    
    # Droping the 'Nearby_POI_Counts' column after processing
    merged_adresses_loyers.drop(columns=['Nearby_POI_Counts'], inplace=True)




    def calculate_poi_weights(row, tree, poi_df, weights_dict, tolerance_km=0.5):
        """
        Calcule la somme des poids des POI proches pour une adresse.
        """
        tolerance_deg = tolerance_km / 111  # Conversion km -> degrés
        lat_lon = (row['lat'], row['long'])
        idxs = tree.query_ball_point(lat_lon, tolerance_deg)
        nearby_pois = poi_df.iloc[idxs]['type'].values

        # Calcul de la somme des poids des POI
        total_weight = sum(weights_dict.get(poi, 0) for poi in nearby_pois)
        return total_weight

    # Ajouter une colonne pour la somme des poids des POI
    merged_adresses_loyers['Nearby_POI_Weight'] = merged_adresses_loyers.apply(
        calculate_poi_weights, tree=poi_tree, poi_df=poi_df_filtered, weights_dict=poi_weights, axis=1
    )

    # Écriture des résultats dans des fichiers CSV segmentés
    max_file_size_bytes = max_file_size_gb * 1024 * 1024 * 1024
    current_file_index = 1
    current_file_size = 0
    output_file = f"{output_prefix}_{current_file_index}.csv"
    header_written = False

    for chunk_start in range(0, len(merged_adresses_loyers), 10000):  # Traite 10 000 lignes à la fois
        chunk = merged_adresses_loyers.iloc[chunk_start:chunk_start + 10000]
        chunk_size_bytes = chunk.memory_usage(deep=True).sum()

        # Si le fichier dépasse la taille maximale, crée un nouveau fichier
        if current_file_size + chunk_size_bytes > max_file_size_bytes:
            current_file_index += 1
            output_file = f"{output_prefix}_{current_file_index}.csv"
            current_file_size = 0
            header_written = False

        # Écrire le chunk dans le fichier actuel
        chunk.to_csv(output_file, mode='a', header=not header_written, index=False, encoding='utf-8')
        current_file_size += chunk_size_bytes
        header_written = True

    print(f"Les fichiers CSV ont été générés avec le préfixe '{output_prefix}'.")


def predict_Paris_renting_good_price(merged_adress_loyers_filepath='merged_adresses_loyers.csv'):
    # Charger les données
    data = pd.read_csv(merged_adress_loyers_filepath)

    # Sélectionner les colonnes pour la prédiction
    # Update the features to include the new POI count columns
    poi_count_features = [f'num_{poi}' for poi in interesting_pois]
    X = merged_adresses_loyers[['lat', 'long', 'Loyer minimum (€/m²)', 'Loyer maximum (€/m²)'] + poi_count_features]
    y = merged_adresses_loyers['Loyer médian (€/m²)']

    # Colonne cible: prédiction du loyer médian
    
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
