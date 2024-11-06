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
    # Enregistrer en fichier CSV
    df_poi.to_csv('data/poi_paris.csv', index=False, encoding='utf-8')  


def find_and_click_button(template_path):
    # Pause pour laisser le temps de tout charger
    time.sleep(2)

    # Capture d'écran de la fenêtre complète
    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)

    # Convertir l'image en RGB pour OpenCV (car PyAutoGUI utilise un format différent)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)

    # Charger l'image du bouton "Valider" (template) que tu veux détecter
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    w, h = template.shape[:-1]

    # Faire correspondre l'image du template avec la capture d'écran
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

    # Définir un seuil pour la correspondance
    threshold = 0.8
    loc = np.where(result >= threshold)

    # Si le template est trouvé, cliquer à cet endroit
    if len(loc[0]) > 0:
        # Prendre la première correspondance (on peut améliorer si nécessaire)
        pt = (loc[1][0], loc[0][0])
        center_x, center_y = pt[0] + w // 2, pt[1] + h // 2

        # Compensation (par exemple, ajouter 10 pixels à droite et 20 pixels en hauteur)
        compensation_x = 70  # Ajuster à droite de 10 pixels
        compensation_y = -90  # Ajuster vers le haut de 20 pixels

        # Appliquer la compensation
        center_x += compensation_x
        center_y += compensation_y

        # Utiliser pyautogui pour cliquer à l'endroit détecté
        pyautogui.moveTo(center_x, center_y, duration=1)  # Déplacer la souris vers le centre du bouton ajusté
        pyautogui.click()  # Simuler le clic
        print(f"Clicked at: {center_x}, {center_y} (with compensation)")
    else:
        print("Le bouton n'a pas été trouvé.")


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


def get_data_from_referenceloyer():
    
    driver = webdriver.Chrome()
    # Maximiser la fenêtre pour qu'elle soit en plein écran
    #driver.maximize_window()

    # URL du site
    url = "http://www.referenceloyer.drihl.ile-de-france.developpement-durable.gouv.fr/paris/"
    driver.get(url)
    time.sleep(1)

    # Charger le fichier CSV 'adresses-ban.csv' en ne gardant que les colonnes nécessaires
    csv_path = "data/adresses-ban.csv"
    # Fichier CSV pour la sauvegarde progressive
    output_file = 'data/loyers_paris_adresses.csv'
    
    #adresses_df = pd.read_csv(csv_path, sep=";", usecols=["voie_nom", "commune_nom", "commune_insee"])
    unprocessed_addresses = resume_from_last_extraction(csv_path, output_file)


    # Options disponibles pour le nombre de pièces, époque de construction, et type de location
    pieces_options = ['1 pièce', '2 pièces', '3 pièces', '4 pièces et plus']
    epoques_options = ['avant 1946', '1946-1970', '1971-1990', 'après 1990']
    locations_options = ['meublée', 'non meublée']
    
    # Parcourir les adresses du fichier CSV
    for index, row in unprocessed_addresses.iterrows():
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
                            
                            #find_and_click_button('bouton_valide_2.png')
                                                        
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


if __name__=='__main__':
    #get_data_from_overpass()
    get_data_from_referenceloyer()
    #time.sleep(4)
    #find_and_click_button('bouton_valider.png')
