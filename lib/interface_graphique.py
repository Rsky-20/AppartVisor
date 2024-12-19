import tkinter as tk
from tkinter import messagebox
from tkintermapview import TkinterMapView
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np

class AppartVisorGUI():
    def __init__(self):
        
        self.data_loyer = pd.read_csv("AppartVisor\data\loyers_paris_adresses.csv")

        self.typo = "Arial"
        self.taille_ecriture = 12

        # Global variable to hold the DataFrame
        self.data_user = pd.DataFrame()
        self.address_fin_fin = None
        self.mode_var = None
        self.rue_var = None
        
        self.fenetre, self.frame1, self.frame2, self.adresse_var = self.fenetre_graph()
        self.age, self.surface, self.pieces, self.prix_total, self.meuble = self.get_user_inputs(self.frame2, self.adresse_var)

        self.fenetre.mainloop()

    def traitement_pieces(self, pieces):
        
        if pieces == 1:
            return str(pieces)+" pièce"
        if pieces >=4:
            return "4 pièces et plus"
        else:
            return str(pieces)+" pièces"

    def traitement_adresse(self, adresse):
    
        if self.mode_var.get() == "manuel":
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
            #print(liste)
            for i in liste:
                trimmed = i.strip().lower()
                #print(f"trimmed est: {trimmed}")
                if any(abrev in trimmed for abrev in list_abreviation) and i.strip():
                    add = i.strip()
                    #print(f"Rue ajoutée : {add}")
                elif trimmed.isdigit() and trimmed.startswith("75") and i.strip():
                    add_num = '75' + '1' + trimmed[-2:]
                    #print(f"Code postal ajouté : {add_num}")
            
            adresse_final = add + ", " + add_num + " Paris"
            #print(f"L'adresse finale est : {adresse_final}")
            return adresse_final
    

    def validate_address(self):
        if self.mode_var.get() == "manuel":
            address = self.rue_var.get()
        else:  # Mode carte
            address = self.adresse_var.get()

        # Vérifie que l'adresse n'est pas vide
        if address and address.strip() != "":
            self.address_fin_fin = self.traitement_adresse(address)
            #print(f"L'adresse fin_fin validée est : {address_fin_fin}")
            messagebox.showinfo("Adresse entrée", f"Adresse ajoutée :\n{self.address_fin_fin}")
            
        else:
            messagebox.showwarning("Erreur", "Veuillez entrer ou sélectionner une adresse valide.")


    def get_address_from_coordinates(self, lat, lon):
        geolocator = Nominatim(user_agent="map_app")
        location = geolocator.reverse((lat, lon), language='en')
        if location:
            return location.address
        return "Adresse non trouvée"
    
    
    def get_lat_long(self, adresse):
        geolocator = Nominatim(user_agent="app_loyer")
        location = geolocator.geocode(adresse)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None


    def activate_map_click_mode(self, map_widget, adresse_var):
        def on_click(coords):
            lat, lon = coords
            address = self.get_address_from_coordinates(lat, lon)
            adresse_var.set(address)  # Update the address variable
            messagebox.showinfo("Adresse sélectionnée", f"Adresse ajoutée :\n{address}")
        map_widget.add_left_click_map_command(on_click)
        messagebox.showinfo("Mode ajout activé", "Cliquez sur la carte pour sélectionner une adresse.")
        

    def get_user_inputs(self, frame2, adresse_var):
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
            if adresse_var.get() == " ":
                lat, long = self.get_lat_long(adresse_var.get())
                self.data_user = pd.DataFrame({
                    "Âge": [age.get()],
                    "Superficie (m²)": [surface.get()],
                    "Nombre de pièces": [pieces.get()],
                    "Prix total (€)": [prix_total.get()],
                    "Type": [meuble.get()],
                    "date de construction":[date_cons.get()],
                    "Adresse": [adresse_var.get()],
                    "Latitude": lat,
                    "Longitude": long
                })
            else :
                self.data_user = pd.DataFrame({
                    "Âge": [age.get()],
                    "Superficie (m²)": [surface.get()],
                    "Nombre de pièces": [pieces.get()],
                    "Prix total (€)": [prix_total.get()],
                    "Type": [meuble.get()],
                    "date de construction":[date_cons.get()],
                    "Adresse": [self.rue_var.get()],
                    "Latitude": self.get_lat_long(adresse_var.get())[0],
                    "Longitude": self.get_lat_long(adresse_var.get())[1],
                })
                
            # Call the estimation display function
            estimation = "un bon appartement"
            self.affichage_estimation(estimation, frame2)
            self.data_user["Adresse"]= self.traitement_adresse(self.data_user["Adresse"][0])
            if self.data_user["Adresse"][0] in self.data_loyer["Adresse"].values:

                if self.data_user["date de construction"][0]!="None":
                    loyer_associe = self.data_loyer.loc[
                        (self.data_loyer["Adresse"] == self.data_user.loc[0, "Adresse"]) 
                        & (self.data_loyer["Nombre de pièces"] == self.traitement_pieces(self.data_user["Nombre de pièces"][0]))
                        & (self.data_loyer["Type de location"] == self.data_user["Type"][0].lower())
                        & (self.data_loyer["Époque de construction"] == self.data_user["date de construction"][0])
                        ].values
                    print(f"L'adresse est disponible. Le loyer associé est : {loyer_associe[0][-2]} €/m²") #a changer par: loyer_associe[-2]
                    
                else: 
                    loyer_associe = self.data_loyer.loc[
                        (self.data_loyer["Adresse"] == self.data_user.loc[0, "Adresse"]) 
                        & (self.data_loyer["Nombre de pièces"] == self.traitement_pieces(self.data_user["Nombre de pièces"][0]))
                        & (self.data_loyer["Type de location"] == self.data_user["Type"][0].lower())
                        ].values
                    columns = ['Address', 'Nombre de pièces', 'Époque de construction', 'Type de location', 'min', 'moyen', 'max']
                    df_moyenne_prix = pd.DataFrame(loyer_associe, columns=columns)                
                    
                    print(f"L'adresse est disponible. Le loyer associé est : {np.mean(df_moyenne_prix['moyen'])} €/m²")
                    
            else:
                print(self.traitement_pieces(self.data_user["Nombre de pièces"][0]))
                print("L'adresse n'est pas disponible.")

        label_age_var = tk.StringVar()
        label_age_var.set("Âge : 0")
        tk.Label(frame2, textvariable=label_age_var, font=(self.typo, self.taille_ecriture)).pack(pady=10)

        barre = tk.Scrollbar(frame2, orient="horizontal")
        barre.config(command=lambda *args: update_age(args[1]))
        barre.set(0, 0.01)
        barre.pack(side="top", fill="x", pady=10)

        tk.Label(frame2, text="Superficie (en m²):", font=(self.typo, self.taille_ecriture)).pack(pady=10)
        tk.Entry(frame2, textvariable=surface, font=(self.typo, self.taille_ecriture)).pack(pady=10)

        tk.Label(frame2, text="Nombre de pièces:", font=(self.typo, self.taille_ecriture)).pack(pady=10)
        tk.Entry(frame2, textvariable=pieces, font=(self.typo, self.taille_ecriture)).pack(pady=10)

        tk.Label(frame2, text="Prix total (€):", font=(self.typo, self.taille_ecriture)).pack(pady=10)
        tk.Entry(frame2, textvariable=prix_total, font=(self.typo, self.taille_ecriture)).pack(pady=10)

        tk.Label(frame2, text="Type:", font=(self.typo, self.taille_ecriture)).pack(pady=10)
        tk.Radiobutton(frame2, text="Meublée", variable=meuble, value="Meublée", font=(self.typo, self.taille_ecriture)).pack()
        tk.Radiobutton(frame2, text="Non Meublée", variable=meuble, value="Non Meublée", font=(self.typo, self.taille_ecriture)).pack()

        tk.Label(frame2, text="Date de construction:", font=(self.typo, self.taille_ecriture)).pack(pady=10)
        tk.Radiobutton(frame2, text="avant 1946", variable=date_cons, value="avant 1946", font=(self.typo, self.taille_ecriture)).pack()
        tk.Radiobutton(frame2, text="1946-1970", variable=date_cons, value="1946-1970", font=(self.typo, self.taille_ecriture)).pack()
        tk.Radiobutton(frame2, text="1971-1990", variable=date_cons, value="1971-1990", font=(self.typo, self.taille_ecriture)).pack()
        tk.Radiobutton(frame2, text="après 1990", variable=date_cons, value="après 1990", font=(self.typo, self.taille_ecriture)).pack()
        tk.Radiobutton(frame2, text="None", variable=date_cons, value="None", font=(self.typo, self.taille_ecriture)).pack()
        
        
        
        bouton = tk.Button(frame2, text="Estimer", command=validate_all, font=(self.typo, self.taille_ecriture, "italic"))
        bouton.pack(pady=20)

        return age, surface, pieces, prix_total, meuble

    def get_window_dimensions(self, fenetre):
        return fenetre.winfo_width(), fenetre.winfo_height()  # Largeur et Hauteur actuelle

    def fenetre_graph(self):
        self.fenetre = tk.Tk()
        self.fenetre.update_idletasks()
        self.fenetre_largeur, self.fenetre_hauteur = self.get_window_dimensions(self.fenetre)

        self.fenetre['bg'] = 'white'
        self.fenetre.title("Prototipage rapide")
        self.fenetre.state('zoomed')

        tk.Label(self.fenetre, text="Appart'Visor !", fg="red", font=(self.typo, self.taille_ecriture-4, "bold")).pack(pady=10)
        tk.Label(self.fenetre, text="L'application qui donne le juste prix de ce que vous méritez", font=(self.typo, self.taille_ecriture, "bold")).pack(pady=10)

        menu1 = tk.Menu(self.fenetre)
        menu1.add_cascade(label="Fichier")
        menu1.add_cascade(label="Options")
        menu1.add_cascade(label="Aide")
        self.fenetre.config(menu=menu1)

        bouton = tk.Button(self.fenetre, text="Quitter", command=self.fenetre.destroy, fg="red", font=(self.typo, self.taille_ecriture, "italic"))
        bouton.pack()

        frame1 = tk.LabelFrame(self.fenetre, text="Visualisation map", width=int(self.fenetre_largeur*0.0), height=int(self.fenetre_hauteur*0.4))
        frame1.pack(ipadx=20, ipady=20, side="left", fill="both", expand=False)
        
        frame2 = tk.LabelFrame(self.fenetre, text="Paramètres", width=20, height=20)
        frame2.pack(ipadx=2010, ipady=510, side="right", fill="both")

        map_widget = TkinterMapView(frame1)
        map_widget.pack(fill="both", expand=True)
        map_widget.set_position(48.8566, 2.3522)
        map_widget.set_zoom(12)
        
        # Fonction pour redimensionner les frames
        def resize_frames(event=None):
            fenetre_largeur, fenetre_hauteur = self.get_window_dimensions(self.fenetre)
            
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
        self.fenetre.bind("<Configure>", resize_frames)

        self.mode_var = tk.StringVar(value="manuel")  

        # Boutons radio pour le choix de la méthode
        tk.Label(frame1, text="Choisissez une méthode :", font=(self.typo, self.taille_ecriture)).pack(pady=10, side="top")
        tk.Radiobutton(
            frame1, 
            text="Entrer l'adresse manuellement", 
            variable=self.mode_var, 
            value="manuel", 
            font=(self.typo, self.taille_ecriture),
            command=lambda: toggle_mode("manuel")
        ).pack(anchor="w", padx=10)

        tk.Radiobutton(
            frame1, 
            text="Sélectionner un point sur la carte", 
            variable=self.mode_var, 
            value="carte", 
            font=(self.typo, self.taille_ecriture),
            command=lambda: toggle_mode("carte")
        ).pack(anchor="w", padx=10)

        # Frame pour l'entrée manuelle
        frame_manual = tk.Frame(frame1)
        frame_manual.pack(pady=10, fill="x")

        self.rue_var = tk.StringVar(value="")
        departement_var = tk.StringVar(value="")
        adresse_var = tk.StringVar(value="")

        tk.Label(frame_manual, text="Nom de la rue :", font=(self.typo, self.taille_ecriture)).pack(pady=5, side="top")
        rue_entry = tk.Entry(frame_manual, textvariable=self.rue_var, font=(self.typo, self.taille_ecriture), width=50)
        rue_entry.pack(pady=5, side="top")
        

        tk.Button(frame_manual, text="Valider l'adresse", command=self.validate_address, font=(self.typo, self.taille_ecriture)).pack(pady=5, side="top")

        # Frame pour la sélection sur la carte
        frame_map_selection = tk.Frame(frame1)
        frame_map_selection.pack_forget()  # Masqué par défaut

        tk.Label(frame_map_selection, text="Cliquez sur un point de la carte pour choisir une adresse :", font=(self.typo, self.taille_ecriture)).pack(pady=5, side="top")
        tk.Button(frame_map_selection, text="Activer le mode carte", command=lambda: self.activate_map_click_mode(map_widget, adresse_var), font=(self.typo, self.taille_ecriture)).pack(pady=10)

        # Fonction pour basculer entre les modes
        def toggle_mode(mode):
            if mode == "manuel":
                frame_manual.pack(pady=10, fill="x")
                frame_map_selection.pack_forget()
            elif mode == "carte":
                frame_manual.pack_forget()
                frame_map_selection.pack(pady=10, fill="x")

        return self.fenetre, frame1, frame2, adresse_var

    
    def affichage_estimation(self, estimation, frame2):
        self.affichage_user_data()
        label = tk.Label(frame2, text=f"Nous estimons que votre sélection est : {estimation}", 
                        font=(self.typo, self.taille_ecriture), fg="green")
        label.pack(pady=10, side="bottom")
        
    def affichage_user_data(self):
        """
        Affiche les données utilisateur contenues dans self.data_user.
        """
        if hasattr(self, 'data_user') and not self.data_user.empty:
            print("""
    [User Data]
    -----------------------------
    """)
            for col in self.data_user.columns:
                print(f"{col}: {self.data_user[col].iloc[0]}")
            print("-----------------------------")
        else:
            print("[Erreur] : Les données utilisateur (self.data_user) n'ont pas été définies ou sont vides.")


if __name__=='__main__':
    app = AppartVisorGUI()
