import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import os
import cv2
import numpy as np
import pyautogui
import tqdm
from sklearn.neighbors import KDTree
from collections import Counter


try:
    import chromedriver_autoinstaller
    chromedriver_autoinstaller.install()
except:
    print('Impossible de charger chromedriver ... ')

def get_data_from_overpass():
    # Requête Overpass pour récupérer les POI à Paris intramuros
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    area[name="Paris"][admin_level=8];
    node(area)["amenity"];
    out body;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()

    # Extraire les informations de chaque POI
    poi_list = []
    for element in data['elements']:
        poi_list.append({
            'name': element['tags'].get('name', 'Unknown'),
            'latitude': element['lat'],
            'longitude': element['lon'],
            'type': element['tags'].get('amenity', 'Unknown')
        })

    # Transformer en DataFrame pour une meilleure visualisation
    df_poi = pd.DataFrame(poi_list)

    # Filtrer les POI uniques
    df_unique_poi = df_poi.drop_duplicates(subset=['type'])
    

    # Enregistrer en fichier CSV
    df_poi.to_csv('data/poi_paris.csv', index=False, encoding='utf-8')

def get_unique_poi_types(filepath='data/poi_paris.csv'):
    """
    Lit un fichier CSV contenant des POI et retourne une liste des types uniques.
    
    :param filepath: Chemin du fichier CSV contenant les POI (par défaut 'data/poi_paris.csv').
    :return: Liste des types uniques de POI.
    """
    # Charger les données depuis le fichier CSV
    try:
        df_poi = pd.read_csv(filepath)
        
        # Vérifier si la colonne "type" existe
        if 'type' not in df_poi.columns:
            raise ValueError(f"La colonne 'type' n'existe pas dans le fichier {filepath}")
        
        # Obtenir les types uniques
        unique_types = df_poi['type'].dropna().unique().tolist()
        
        return unique_types
    except FileNotFoundError:
        print(f"Erreur : Le fichier {filepath} est introuvable.")
        return []
    except Exception as e:
        print(f"Erreur : {e}")
        return []


def simplify_ban(input_file='data/adresses-ban.csv', output_file='data/simplified_ban.csv'):
    """
    Simplifie la base de données des adresses en conservant uniquement les colonnes utiles
    et les noms de rue uniques.

    :param input_file: Chemin vers le fichier CSV original
    :param output_file: Chemin vers le fichier CSV simplifié (par défaut 'simplified_ban.csv')
    """
    # Charger le fichier CSV
    df = pd.read_csv(input_file, sep=';')

    # Normaliser les noms de colonnes
    df.columns = df.columns.str.strip()

    # Vérifier la présence des colonnes nécessaires
    required_columns = ['commune_nom', 'voie_nom', 'commune_insee']
    if not all(col in df.columns for col in required_columns):
        raise KeyError(f"Colonnes manquantes dans le fichier : {set(required_columns) - set(df.columns)}")

    # Garder uniquement les colonnes nécessaires
    df = df[required_columns]

    # Supprimer les doublons basés sur 'voie_nom' et 'commune_insee'
    df = df.drop_duplicates(subset=['voie_nom', 'commune_insee'])

    # Enregistrer le fichier nettoyé
    df.to_csv(output_file, index=False, sep=';')
    print(f"Le fichier simplifié a été enregistré sous {output_file}")



def resume_from_last_extraction(input_file, output_file):
    # Charger le fichier d'adresses à traiter
    adresses_df = pd.read_csv(input_file, sep=";", usecols=["voie_nom", "commune_nom", "commune_insee"])
    
    # Vérifier si le fichier de sortie existe pour récupérer les adresses déjà traitées
    if os.path.exists(output_file):
        # Charger les adresses déjà traitées
        processed_df = pd.read_csv(output_file)
        processed_addresses = set(processed_df['Adresse'])
        
        # Filtrer les adresses non traitées
        unprocessed_df = adresses_df[~adresses_df.apply(
            lambda row: f"{row['voie_nom']}, {row['commune_insee']} {row['commune_nom']}", axis=1
        ).isin(processed_addresses)]
    else:
        # Si le fichier de sortie n'existe pas, toutes les adresses doivent être traitées
        unprocessed_df = adresses_df

    return unprocessed_df


def get_data_from_referenceloyer(ban_path = "data/simplified-ban.csv", output_file = 'data/loyers_paris_adresses.csv'):
    
    driver = webdriver.Chrome()
    # Maximiser la fenêtre pour qu'elle soit en plein écran
    #driver.maximize_window()

    # URL du site
    url = "http://www.referenceloyer.drihl.ile-de-france.developpement-durable.gouv.fr/paris/"
    driver.get(url)
    time.sleep(1)
    
    #adresses_df = pd.read_csv(csv_path, sep=";", usecols=["voie_nom", "commune_nom", "commune_insee"])
    unprocessed_addresses = resume_from_last_extraction(ban_path, output_file)


    # Options disponibles pour le nombre de pièces, époque de construction, et type de location
    pieces_options = ['1 pièce', '2 pièces', '3 pièces', '4 pièces et plus']
    epoques_options = ['avant 1946', '1946-1970', '1971-1990', 'après 1990']
    locations_options = ['meublée', 'non meublée']
    
    # Parcourir les adresses du fichier CSV
    for index, row in tqdm.tqdm(unprocessed_addresses.iterrows(), total=unprocessed_addresses.shape[0], desc="Traitement des adresses"):

        try:
            # Construire l'adresse sous forme "nom_de_rue, code_postale nom_commune"
            adresse_complete = f"{row['voie_nom']}, {row['commune_insee']} {row['commune_nom']}"

            # Entrer l'adresse dans le champ de recherche
            search_input = driver.find_element(By.ID, 'search-adresse')
            search_input.clear()  # Vider le champ avant de saisir une nouvelle adresse
            search_input.send_keys(adresse_complete)

            # Sélectionner les options dans les menus déroulants pour les caractéristiques du logement
            for piece in pieces_options:
                for epoque in epoques_options:
                    for location in locations_options:
                        try:
                            time.sleep(0.1)
                            # Sélectionner les options pour le nombre de pièces, l'époque de construction, et le type de location
                            select_piece = Select(driver.find_element(By.ID, 'piece'))
                            select_piece.select_by_visible_text(piece)
                            
                            time.sleep(0.1)

                            select_epoque = Select(driver.find_element(By.ID, 'edit-epoque'))
                            select_epoque.select_by_visible_text(epoque)
                            
                            time.sleep(0.1)

                            select_location = Select(driver.find_element(By.ID, 'edit-meuble'))
                            select_location.select_by_visible_text(location)
                            
                            time.sleep(0.1)

                            # Simuler le clic sur le bouton "Valider"
                            
                            submit_button = driver.find_element(By.ID, 'edit-submit-adresse')
                            driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                            #submit_button.click()
                            
                            time.sleep(0.1)  # Attendre que la page se recharge
                            try:
                                # Construire l'XPath en utilisant le texte de l'adresse complète
                                xpath_expression = f"//li[contains(text(), '{row['voie_nom']}')]"

                                # Utiliser XPath pour trouver l'élément de la liste contenant l'adresse
                                ok_button = driver.find_element(By.XPATH, xpath_expression)

                                # Cliquer sur l'élément trouvé
                                ok_button.click()
                            except:
                                pass
                            
                            time.sleep(0.1)  # Attendre que la page se recharge
                                                                                    
                            #loyers = driver.find_element(By.CLASS_NAME, 'loyers')
                            #driver.execute_script("arguments[0].scrollIntoView(true);", loyers)

                            # Extraire les loyers (min, médian, max) en fonction des balises fournies
                            loyer_min = driver.find_element(By.CLASS_NAME, 'refmin').text
                            loyer_median = driver.find_element(By.CLASS_NAME, 'ref').text
                            loyer_max = driver.find_element(By.CLASS_NAME, 'refmaj').text

                            # Ajouter les données dans le fichier CSV de manière progressive
                            new_data = {
                                'Adresse': adresse_complete,
                                'Nombre de pièces': piece,
                                'Époque de construction': epoque,
                                'Type de location': location,
                                'Loyer minimum (€/m²)': loyer_min,
                                'Loyer médian (€/m²)': loyer_median,
                                'Loyer maximum (€/m²)': loyer_max
                            }

                            # Convertir les données en DataFrame pour ajouter une ligne au fichier CSV
                            pd.DataFrame([new_data]).to_csv(output_file, mode='a', index=False, header=not pd.io.common.file_exists(output_file))

                        except Exception as e:
                            print(f"Erreur lors de la récupération des données pour l'adresse {adresse_complete}, pièce {piece}, époque {epoque}, type {location}: {e}")

        except Exception as e:
            print(f"Erreur lors de la récupération des données pour l'adresse {adresse_complete}: {e}")
            continue


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
    print('[Start] - Merge Dataset')

    # Chargement des fichiers CSV
    adresses_df = pd.read_csv(adress_dataset_filepath, delimiter=';')
    poi_df = pd.read_csv(poi_paris_dataset_filepath)
    loyers_df = pd.read_csv(loyers_paris_adresses_filepath)

    print('[RUN PROCESS] - Data cleanning')
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
    
    print('[RUN PROCESS] - Merge Data into DataFrame')
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

    print('[RUN PROCESS] - POI cleanning')
    # KDTree pour trouver les POI proches
    poi_coords = np.array(list(zip(poi_df_filtered['latitude'], poi_df_filtered['longitude'])))
    poi_tree = KDTree(poi_coords)
    
    # Application de la fonction pour calculer le nombre de POI pour chaque appartement
    merged_adresses_loyers['Nearby_POI_Counts'] = merged_adresses_loyers.apply(
        calculate_poi_counts, tree=poi_tree, poi_df=poi_df_filtered, axis=1
    )
    # Création de colonne pour chaque type de POI
    poi_types = interesting_pois  # List de types de POI
    
    print('[RUN PROCESS] - Count POI by type')
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

    print('[RUN PROCESS] - Separate DataFrame as data chunk')
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

        print(f"[END PROCESS] - Save chunk file : '{output_file}'.")



if __name__=='__main__':
    #simplify_ban()
    #get_data_from_overpass()
    print(get_unique_poi_types(filepath='AppartVisor\\data\\poi_paris.csv'))
    #time.sleep(4)
