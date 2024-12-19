# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 14:59:41 2024

@author: Nicolas Bledin
"""

import pandas as pd
from scipy.spatial import KDTree
import numpy as np
import matplotlib.pyplot as plt
import os
from tqdm import tqdm

import torch
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.neighbors import KDTree
from tensorflow.keras.layers import TextVectorization


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Fonction pour préparer les données utilisateur
def predict_user_data(model, data_user, categorical_encoder, scaler, text_vectorizer, device):
    """
    Prédit le loyer médian (€/m²) pour une donnée utilisateur.

    Args:
        model (torch.nn.Module): Modèle PyTorch entraîné.
        data_user (pd.DataFrame): Donnée utilisateur (1 seule ligne) sous forme de DataFrame.
        categorical_encoder (OneHotEncoder): Encodeur catégorique entraîné.
        scaler (StandardScaler): Scaler entraîné pour les données numériques.
        text_vectorizer (TextVectorization): Vectoriseur textuel entraîné.
        device (torch.device): Appareil ('cpu' ou 'cuda') pour exécuter le modèle.

    Returns:
        float: Prédiction du loyer médian (€/m²).
    """
    # Préparer les données utilisateur
    # Vectorisation des textes
    user_text = data_user[['cle_interop', 'commune_nom', 'voie_nom', 'Adresse']].apply(
        lambda row: ' '.join(row.values.astype(str)), axis=1
    )
    user_text_vectorized = text_vectorizer(tf.convert_to_tensor(user_text)).numpy()

    # Encodage des données catégoriques
    user_categorical_encoded = categorical_encoder.transform(data_user[['Nombre de pièces', 'Époque de construction', 'Type de location']])

    # Mise à l'échelle des données numériques
    user_numerical_scaled = scaler.transform(data_user[['lat', 'long', 'numero', 'num_dentist', 'num_driving_school',
                                                        'num_park', 'num_fitness_centre', 'num_pub', 'num_community_centre',
                                                        'num_yoga_studio', 'num_dojo', 'num_sports_centre', 'num_bank',
                                                        'num_restaurant', 'num_library', 'num_cafe', 'num_clinic',
                                                        'num_theatre', 'num_cinema', 'num_marketplace', 'num_university',
                                                        'num_childcare', 'Loyer minimum (€/m²)', 'Loyer maximum (€/m²)']])

    # Combiner toutes les données
    user_combined = np.hstack([
        user_numerical_scaled,
        user_text_vectorized,
        user_categorical_encoded
    ]).astype(np.float32)

    # Convertir en tensor PyTorch
    user_tensor = torch.tensor(user_combined, dtype=torch.float32).to(device)

    # Effectuer la prédiction
    model.eval()  # Passer le modèle en mode évaluation
    with torch.no_grad():
        prediction = model(user_tensor).cpu().numpy()

    return prediction[0][0]  # Retourner la prédiction

def calculate_poi_counts_for_user(lat, long, poi_df, poi_tree, tolerance_km=0.5):
    """
    Calcule le nombre de POI proches pour chaque type à partir de la latitude et longitude fournies.

    Args:
        lat (float): Latitude de la localisation.
        long (float): Longitude de la localisation.
        poi_df (pd.DataFrame): DataFrame contenant les informations sur les POI.
        poi_tree (KDTree): KDTree construit à partir des coordonnées des POI.
        tolerance_km (float): Rayon de recherche des POI en kilomètres.

    Returns:
        dict: Dictionnaire avec le nombre de POI par type.
    """
    # Conversion du rayon de recherche de km à degrés (1° ~ 111 km)
    tolerance_deg = tolerance_km / 111

    # Rechercher les POI dans le rayon spécifié
    lat_lon = (lat, long)
    idxs = poi_tree.query_ball_point(lat_lon, tolerance_deg)

    # Filtrer les POI trouvés
    nearby_pois = poi_df.iloc[idxs]['type'].values

    # Compter les POI par type
    poi_counts = {poi_type: 0 for poi_type in poi_df['type'].unique()}
    for poi in nearby_pois:
        poi_counts[poi] += 1

    return poi_counts

# Fonction pour enrichir `data_user` avec les POI
def enrich_user_data_with_poi(data_user, poi_df):
    """
    Enrichit les données utilisateur avec les POI proches en ajoutant des colonnes pour chaque type de POI.

    Args:
        data_user (pd.DataFrame): Données utilisateur avec `lat` et `long`.
        poi_df (pd.DataFrame): DataFrame contenant les POI avec leurs types et coordonnées.

    Returns:
        pd.DataFrame: Données utilisateur enrichies avec les colonnes de POI.
    """
    # Construire le KDTree pour les POI
    poi_coords = np.array(list(zip(poi_df['latitude'], poi_df['longitude'])))
    poi_tree = KDTree(poi_coords)

    # Récupérer les POI pour chaque ligne utilisateur
    poi_types = poi_df['type'].unique()
    poi_columns = [f'num_{poi_type}' for poi_type in poi_types]

    # Initialiser les colonnes POI avec 0
    for col in poi_columns:
        data_user[col] = 0

    # Enrichir chaque ligne utilisateur avec les POI proches
    for idx, row in data_user.iterrows():
        poi_counts = calculate_poi_counts_for_user(row['lat'], row['long'], poi_df, poi_tree)
        for poi_type, count in poi_counts.items():
            column_name = f'num_{poi_type}'
            if column_name in data_user.columns:
                data_user.at[idx, column_name] = count

    return data_user

if __name__ == '__main__':
    # Charger ou définir les objets nécessaires

    # Exemple de données utilisateur
    data_user = pd.DataFrame({
        "cle_interop": ["example_key"],
        "commune_nom": ["Paris"],
        "voie_nom": ["Rue de Rivoli"],
        "Adresse": ["10 Rue de Rivoli, Paris"],
        "Nombre de pièces": ["2 pièces"],
        "Époque de construction": ["1990"],
        "Type de location": ["meublée"],
        "lat": [48.8566],
        "long": [2.3522],
        "numero": [10],
        "Loyer minimum (€/m²)": [15],
        "Loyer maximum (€/m²)": [30]
    })

    # Base de données des POI
    poi_df = pd.DataFrame({
        'name': ['Notre-Dame', 'Louvre Museum'],
        'latitude': [48.851834, 48.860611],
        'longitude': [2.3500556, 2.337644],
        'type': ['ferry_terminal', 'museum']
    })

    # Initialiser le modèle (exemple simplifié)
    class MockModel(torch.nn.Module):
        def forward(self, x):
            return torch.tensor([[25.0]])  # Exemple de valeur prédite (25 €/m²)

    model = MockModel()

    # Simuler les encodeurs et scaler (exemples simplifiés)
    categorical_encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
    categorical_encoder.fit(data_user[['Nombre de pièces', 'Époque de construction', 'Type de location']])

    scaler = StandardScaler()
    scaler.fit(data_user[['lat', 'long', 'numero', 'Loyer minimum (€/m²)', 'Loyer maximum (€/m²)']])

    text_vectorizer = TextVectorization(output_mode="tf-idf", max_tokens=10000)
    text_vectorizer.adapt(data_user[['cle_interop', 'commune_nom', 'voie_nom', 'Adresse']].apply(
        lambda row: ' '.join(row.values.astype(str)), axis=1
    ))

    # Enrichir les données utilisateur avec les POI
    data_user = enrich_user_data_with_poi(data_user, poi_df)

    # Prédire le loyer pour les données utilisateur enrichies
    try:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        rent_prediction = predict_user_data(model, data_user, categorical_encoder, scaler, text_vectorizer, device)
        print(f"Loyer prédit : {rent_prediction:.2f} €/m²")

    except ValueError as e:
        print(f"Erreur : {e}")

