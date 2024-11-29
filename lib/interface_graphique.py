import tkinter as tk
from tkinter import messagebox
from tkintermapview import TkinterMapView
from geopy.geocoders import Nominatim
import pandas as pd

data_loyer = pd.read_csv("loyers_paris_adresses.csv")

typo = "Arial"
taille_ecriture = 12

# Global variable to hold the DataFrame
data_user = pd.DataFrame()

def traitement_pieces(pieces):
    
    if pieces == 1:
        return str(pieces)+" pièce"
    if pieces >=4:
        return "4 pièces et plus"
    else:
        return str(pieces)+" pièces"

def traitement_adresse(adresse):
    add = ""
    add_num = ""  # Initialiser add_num pour éviter les erreurs
    list_abreviation = ["rue", "impasse", "square"]
    liste = adresse.split(",")
    
    for i in liste:
        trimmed = i.strip().lower()  # Nettoyer et mettre en minuscule pour comparaison
        print(f"Traitement de : '{trimmed}'")  # Débogage

        # Vérifie si l'élément contient un mot-clé d'adresse
        if any(abrev in trimmed for abrev in list_abreviation):
            add += i.strip() + ", "  # Garde l'élément d'origine avec espaces enlevés
        # Vérifie si l'élément est un code postal parisien
        elif trimmed.isdigit() and trimmed.startswith("75"):
            print(f"Code postal trouvé : {'75'+'1'+trimmed[-2:]}")
            add_num = '75'+'1'+trimmed[-2:] # Garde le code postal exact
    
    # Gérer le cas où le code postal n'a pas été trouvé
    if not add_num:
        add_num = "Code postal non trouvé"
    
    return add + add_num + " Paris"


def get_address_from_coordinates(lat, lon):
    geolocator = Nominatim(user_agent="map_app")
    location = geolocator.reverse((lat, lon), language='en')
    if location:
        return location.address
    return "Adresse non trouvée"

def activate_map_click_mode(map_widget, adresse_var):
    def on_click(coords):
        lat, lon = coords
        address = get_address_from_coordinates(lat, lon)
        adresse_var.set(address)  # Update the address variable
        messagebox.showinfo("Adresse sélectionnée", f"Adresse ajoutée :\n{address}")
    map_widget.add_left_click_map_command(on_click)
    messagebox.showinfo("Mode ajout activé", "Cliquez sur la carte pour sélectionner une adresse.")

def get_user_inputs(frame2, adresse_var):
    age = tk.IntVar()
    surface = tk.IntVar()
    pieces = tk.IntVar()
    prix_total = tk.IntVar()
    meuble = tk.StringVar(value="Non Meublé")

    def update_age(value):
        int_value = int(float(value) * 99)
        age.set(int_value)
        label_age_var.set(f"Âge : {int_value}")

    def validate_all():
        # Update global DataFrame
        global data_user
        data_user = pd.DataFrame({
            "Âge": [age.get()],
            "Superficie (m²)": [surface.get()],
            "Nombre de pièces": [pieces.get()],
            "Prix total (€)": [prix_total.get()],
            "Type": [meuble.get()],
            "Adresse": [adresse_var.get()]
        })
        # Call the estimation display function
        estimation = "un bon appartement"
        affichage_estimation(estimation, frame2)
        data_user["Adresse"]= traitement_adresse(data_user["Adresse"][0])
        if data_user["Adresse"][0] in data_loyer["Adresse"].values:
            print(f'ce qu on done {data_user["Type"][0].lower()}' )
            print(f'bdd: {data_loyer["Type de location"]}') 

            # Filtrer les données de 'data_loyer' en fonction de plusieurs critères présents dans 'data_user'
            loyer_associe = data_loyer.loc[
                (data_loyer["Adresse"] == data_user.loc[0, "Adresse"]) 
                & (data_loyer["Nombre de pièces"] == traitement_pieces(data_user["Nombre de pièces"][0]))
                & (data_loyer["Type de location"] == data_user["Type"][0].lower())
                ].values[5]

            print(f"L'adresse est disponible. Le loyer associé est : {loyer_associe} €/m²")
        else:
            print("L'adresse n'est pas disponible.")

    label_age_var = tk.StringVar()
    label_age_var.set("Âge : 0")
    tk.Label(frame2, textvariable=label_age_var, font=(typo, taille_ecriture)).pack(pady=10)

    barre = tk.Scrollbar(frame2, orient="horizontal")
    barre.config(command=lambda *args: update_age(args[1]))
    barre.set(0, 0.01)
    barre.pack(side="top", fill="x", pady=10)

    tk.Label(frame2, text="Superficie (en m²):", font=(typo, taille_ecriture)).pack(pady=10)
    tk.Entry(frame2, textvariable=surface, font=(typo, taille_ecriture)).pack(pady=10)

    tk.Label(frame2, text="Nombre de pièces:", font=(typo, taille_ecriture)).pack(pady=10)
    tk.Entry(frame2, textvariable=pieces, font=(typo, taille_ecriture)).pack(pady=10)

    tk.Label(frame2, text="Prix total (€):", font=(typo, taille_ecriture)).pack(pady=10)
    tk.Entry(frame2, textvariable=prix_total, font=(typo, taille_ecriture)).pack(pady=10)

    tk.Label(frame2, text="Type:", font=(typo, taille_ecriture)).pack(pady=10)
    tk.Radiobutton(frame2, text="Meublée", variable=meuble, value="Meublée", font=(typo, taille_ecriture)).pack()
    tk.Radiobutton(frame2, text="Non Meublée", variable=meuble, value="Non Meublée", font=(typo, taille_ecriture)).pack()

    bouton = tk.Button(frame2, text="Estimer", command=validate_all, font=(typo, taille_ecriture, "italic"))
    bouton.pack(pady=20)

    return age, surface, pieces, prix_total, meuble

def fenetre_graph():
    fenetre = tk.Tk()
    fenetre['bg'] = 'white'
    fenetre.title("Prototipage rapide")
    fenetre.state('zoomed')

    tk.Label(fenetre, text="Appart'Visor !", fg="red", font=(typo, taille_ecriture-4, "bold")).pack(pady=10)
    tk.Label(fenetre, text="L'application qui donne le juste prix de ce que vous méritez", font=(typo, taille_ecriture, "bold")).pack(pady=10)

    menu1 = tk.Menu(fenetre)
    menu1.add_cascade(label="Fichier")
    menu1.add_cascade(label="Options")
    menu1.add_cascade(label="Aide")
    fenetre.config(menu=menu1)

    bouton = tk.Button(fenetre, text="Quitter", command=fenetre.destroy, fg="red", font=(typo, taille_ecriture, "italic"))
    bouton.pack()
    bouton.place(x=2700, y=10)

    frame1 = tk.LabelFrame(fenetre, text="Visualisation map", width=2000, height=500)
    frame1.pack(ipadx=20, ipady=20, side="left", fill="both", expand=False)
    
    frame2 = tk.LabelFrame(fenetre, text="Paramètres", width=20, height=20)
    frame2.pack(ipadx=2010, ipady=510, side="right", fill="both")
    
    map_widget = TkinterMapView(frame1, width=2000, height=1000)
    map_widget.pack(fill="both")
    
    map_widget.set_position(48.8566, 2.3522)
    map_widget.set_zoom(12)

    adresse_var = tk.StringVar(value="")
    bouton_add_point = tk.Button(frame1, text="Ajouter un point", command=lambda: activate_map_click_mode(map_widget, adresse_var), font=(typo, taille_ecriture))
    bouton_add_point.pack(pady=10, side="bottom")

    return fenetre, frame1, frame2, adresse_var
 
def affichage_estimation(estimation, frame2):
    label = tk.Label(frame2, text=f"Nous estimons que votre sélection est : {estimation}", 
                     font=(typo, taille_ecriture), fg="green")
    label.pack(pady=10, side="bottom")

fenetre, frame1, frame2, adresse_var = fenetre_graph()
age, surface, pieces, prix_total, meuble = get_user_inputs(frame2, adresse_var)



fenetre.mainloop()
