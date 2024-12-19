import tkinter as tk
from tkinter import messagebox
from tkintermapview import TkinterMapView
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
data_loyer = pd.read_csv("AppartVisor\data\loyers_paris_adresses.csv")

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
    
    if mode_var.get() == "manuel":
        adr = adresse.split(",")
        adre = adr[0]
        a = adre.split(" ")
        adre = " ".join(a[1:])
        adre = " ".join([mot.lower() if mot in ["Le", "La", "De","Du"] else mot for mot in adre.split()])
        adr_fin = adre + ", 751"+adr[1][1:3] + adr[-1]
        return adr_fin
    
    else:
        add = ""
        add_num = ""  # Initialiser add_num pour éviter les erreurs
        list_abreviation = ["rue", "impasse", "square","place"]
        liste = adresse.split(",")
        
        for i in liste:
            trimmed = i.strip().lower()  # Nettoyer et mettre en minuscule pour comparaison
    
            # Vérifie si l'élément contient un mot-clé d'adresse
            if any(abrev in trimmed for abrev in list_abreviation):
                add += i.strip() + ", "  # Garde l'élément d'origine avec espaces enlevés
            # Vérifie si l'élément est un code postal parisien
            elif trimmed.isdigit() and trimmed.startswith("75"):
                add_num = '75'+'1'+trimmed[-2:] # Garde le code postal exact
        
        # Gérer le cas où le code postal n'a pas été trouvé
        if not add_num:
            add_num = "Code postal non trouvé"
        
        return add + add_num + " Paris"




 

def validate_address():
    # Vérifie si le mode sélectionné est "manuel"
    if mode_var.get() == "manuel":
        address = rue_var.get()
        address = traitement_adresse(address)
        if address != "":  # Vérifie que l'adresse n'est pas vide
            print(f"L'adresse validée est : {address}")
            messagebox.showinfo("Adresse entrée", f"Adresse ajoutée :\n{address}")
        else:
            messagebox.showwarning("Erreur", "Veuillez entrer une adresse valide.")
    else:
        messagebox.showwarning("Mode invalide", "Vous devez être en mode manuel pour valider l'adresse.")




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
    date_cons = tk.StringVar(value="None")
    def update_age(value):
        int_value = int(float(value) * 99)
        age.set(int_value)
        label_age_var.set(f"Âge : {int_value}")

    def validate_all():
        # Update global DataFrame
        global data_user
        if adresse_var.get() == " ":
            data_user = pd.DataFrame({
                "Âge": [age.get()],
                "Superficie (m²)": [surface.get()],
                "Nombre de pièces": [pieces.get()],
                "Prix total (€)": [prix_total.get()],
                "Type": [meuble.get()],
                "date de construction":[date_cons.get()],
                "Adresse": [adresse_var.get()]
            })
        else :
            data_user = pd.DataFrame({
                "Âge": [age.get()],
                "Superficie (m²)": [surface.get()],
                "Nombre de pièces": [pieces.get()],
                "Prix total (€)": [prix_total.get()],
                "Type": [meuble.get()],
                "date de construction":[date_cons.get()],
                "Adresse": [rue_var.get()]
            })
            
        # Call the estimation display function
        estimation = "un bon appartement"
        affichage_estimation(estimation, frame2)
        data_user["Adresse"]= traitement_adresse(data_user["Adresse"][0])
        if data_user["Adresse"][0] in data_loyer["Adresse"].values:

            if data_user["date de construction"][0]!="None":
                loyer_associe = data_loyer.loc[
                    (data_loyer["Adresse"] == data_user.loc[0, "Adresse"]) 
                    & (data_loyer["Nombre de pièces"] == traitement_pieces(data_user["Nombre de pièces"][0]))
                    & (data_loyer["Type de location"] == data_user["Type"][0].lower())
                    & (data_loyer["Époque de construction"] == data_user["date de construction"][0])
                    ].values
                print(f"L'adresse est disponible. Le loyer associé est : {loyer_associe[0][-2]} €/m²") #a changer par: loyer_associe[-2]
                
            else: 
                loyer_associe = data_loyer.loc[
                    (data_loyer["Adresse"] == data_user.loc[0, "Adresse"]) 
                    & (data_loyer["Nombre de pièces"] == traitement_pieces(data_user["Nombre de pièces"][0]))
                    & (data_loyer["Type de location"] == data_user["Type"][0].lower())
                    ].values
                columns = ['Address', 'Nombre de pièces', 'Époque de construction', 'Type de location', 'min', 'moyen', 'max']
                df_moyenne_prix = pd.DataFrame(loyer_associe, columns=columns)                

                
                print(f"L'adresse est disponible. Le loyer associé est : {np.mean(df_moyenne_prix['moyen'])} €/m²")
                
            
        else:
            print(traitement_pieces(data_user["Nombre de pièces"][0]))
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

    tk.Label(frame2, text="Date de construction:", font=(typo, taille_ecriture)).pack(pady=10)
    tk.Radiobutton(frame2, text="avant 1946", variable=date_cons, value="avant 1946", font=(typo, taille_ecriture)).pack()
    tk.Radiobutton(frame2, text="1946-1970", variable=date_cons, value="1946-1970", font=(typo, taille_ecriture)).pack()
    tk.Radiobutton(frame2, text="1971-1990", variable=date_cons, value="1971-1990", font=(typo, taille_ecriture)).pack()
    tk.Radiobutton(frame2, text="après 1990", variable=date_cons, value="après 1990", font=(typo, taille_ecriture)).pack()
    tk.Radiobutton(frame2, text="None", variable=date_cons, value="None", font=(typo, taille_ecriture)).pack()
    
    
    
    bouton = tk.Button(frame2, text="Estimer", command=validate_all, font=(typo, taille_ecriture, "italic"))
    bouton.pack(pady=20)

    return age, surface, pieces, prix_total, meuble

def get_window_dimensions(fenetre):
    return fenetre.winfo_width(), fenetre.winfo_height()  # Largeur et Hauteur actuelle

def fenetre_graph():
    fenetre = tk.Tk()
    fenetre.update_idletasks()
    fenetre_largeur, fenetre_hauteur = get_window_dimensions(fenetre)

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

    frame1 = tk.LabelFrame(fenetre, text="Visualisation map", width=int(fenetre_largeur*0.0), height=int(fenetre_hauteur*0.4))
    frame1.pack(ipadx=20, ipady=20, side="left", fill="both", expand=False)
    
    frame2 = tk.LabelFrame(fenetre, text="Paramètres", width=20, height=20)
    frame2.pack(ipadx=2010, ipady=510, side="right", fill="both")

    map_widget = TkinterMapView(frame1)
    map_widget.pack(fill="both", expand=True)
    map_widget.set_position(48.8566, 2.3522)
    map_widget.set_zoom(12)
    
    # Fonction pour redimensionner les frames
    def resize_frames(event=None):
        fenetre_largeur, fenetre_hauteur = get_window_dimensions(fenetre)
        
        # Dimensions pour frame1
        largeur_frame1 = int(fenetre_largeur * 0.5)  # 50% de la largeur
        hauteur_frame1 = int(fenetre_hauteur * 0.4)  # 40% de la hauteur
        
        # Configurer la taille de frame1
        frame1.config(width=largeur_frame1, height=hauteur_frame1)
        
        # Frame2 occupe le reste de l'espace
        largeur_frame2 = fenetre_largeur - largeur_frame1
        hauteur_frame2 = fenetre_hauteur  # Reste toute la hauteur
        frame2.config(width=largeur_frame2, height=hauteur_frame2)

    # Redimensionner dynamiquement en fonction des modifications de la fenêtre
    fenetre.bind("<Configure>", resize_frames)

    global mode_var
    global rue_var


    mode_var = tk.StringVar(value="manuel")  

    # Boutons radio pour le choix de la méthode
    tk.Label(frame1, text="Choisissez une méthode :", font=(typo, taille_ecriture)).pack(pady=10, side="top")
    tk.Radiobutton(
        frame1, 
        text="Entrer l'adresse manuellement", 
        variable=mode_var, 
        value="manuel", 
        font=(typo, taille_ecriture),
        command=lambda: toggle_mode("manuel")
    ).pack(anchor="w", padx=10)

    tk.Radiobutton(
        frame1, 
        text="Sélectionner un point sur la carte", 
        variable=mode_var, 
        value="carte", 
        font=(typo, taille_ecriture),
        command=lambda: toggle_mode("carte")
    ).pack(anchor="w", padx=10)

    # Frame pour l'entrée manuelle
    frame_manual = tk.Frame(frame1)
    frame_manual.pack(pady=10, fill="x")

    rue_var = tk.StringVar(value="")
    departement_var = tk.StringVar(value="")
    adresse_var = tk.StringVar(value="")

    tk.Label(frame_manual, text="Nom de la rue :", font=(typo, taille_ecriture)).pack(pady=5, side="top")
    rue_entry = tk.Entry(frame_manual, textvariable=rue_var, font=(typo, taille_ecriture), width=50)
    rue_entry.pack(pady=5, side="top")
    

    tk.Button(frame_manual, text="Valider l'adresse", command=validate_address, font=(typo, taille_ecriture)).pack(pady=5, side="top")

    # Frame pour la sélection sur la carte
    frame_map_selection = tk.Frame(frame1)
    frame_map_selection.pack_forget()  # Masqué par défaut

    tk.Label(frame_map_selection, text="Cliquez sur un point de la carte pour choisir une adresse :", font=(typo, taille_ecriture)).pack(pady=5, side="top")
    tk.Button(frame_map_selection, text="Activer le mode carte", command=lambda: activate_map_click_mode(map_widget, adresse_var), font=(typo, taille_ecriture)).pack(pady=10)

    # Fonction pour basculer entre les modes
    def toggle_mode(mode):
        if mode == "manuel":
            frame_manual.pack(pady=10, fill="x")
            frame_map_selection.pack_forget()
        elif mode == "carte":
            frame_manual.pack_forget()
            frame_map_selection.pack(pady=10, fill="x")

    return fenetre, frame1, frame2, adresse_var

 
def affichage_estimation(estimation, frame2):
    label = tk.Label(frame2, text=f"Nous estimons que votre sélection est : {estimation}", 
                     font=(typo, taille_ecriture), fg="green")
    label.pack(pady=10, side="bottom")

fenetre, frame1, frame2, adresse_var = fenetre_graph()
age, surface, pieces, prix_total, meuble = get_user_inputs(frame2, adresse_var)



fenetre.mainloop()
