import gurobipy as gp
from gurobipy import GRB

def saisir_villes():
    while True:
        try:
            n = int(input("Entrez le nombre de villes : "))
            if n <= 0:
                print("Le nombre de villes doit être positif.")
                continue
            villes = []
            for i in range(n):
                ville = input(f"Entrez le nom de la ville {i+1} : ")
                villes.append(ville)
            return villes
        except ValueError:
            print("Veuillez entrer un nombre valide.")

def saisir_donnees_ville(villes, message):
    donnees = {}
    for ville in villes:
        while True:
            try:
                valeur = float(input(f"{message} pour {ville} : "))
                donnees[ville] = valeur
                break
            except ValueError:
                print("Veuillez entrer un nombre valide.")
    return donnees

def saisir_distances(villes):
    distances = {}
    print("\nEntrez les distances entre les villes :")
    for i in range(len(villes)):
        for j in range(i+1, len(villes)):
            while True:
                try:
                    dist = float(input(f"Distance entre {villes[i]} et {villes[j]} : "))
                    if dist < 0:
                        print("La distance doit être positive.")
                        continue
                    distances[tuple(sorted((villes[i], villes[j])))] = dist
                    break
                except ValueError:
                    print("Veuillez entrer un nombre valide.")
    return distances

def choisir_centres(villes):
    print("\n=== Sélection des centres des régions ===")
    centres = []
    max_entrepots_par_region = {}
    
    while True:
        print("\nListe des villes disponibles :")
        for i, ville in enumerate(villes):
            print(f"{i+1}. {ville}")
        try:
            choix = int(input("Entrez le numéro de la ville choisie comme centre (0 pour terminer) : "))
            if choix == 0:
                break
            if 1 <= choix <= len(villes):
                centre = villes[choix-1]
                if centre in centres:
                    print("Cette ville est déjà sélectionnée comme centre.")
                else:
                    # Demander le nombre maximal d'entrepôts pour cette région
                    while True:
                        try:
                            max_e = int(input(f"Nombre maximal d'entrepôts pour la région de {centre} : "))
                            if max_e <= 0:
                                print("Le nombre maximal d'entrepôts doit être positif.")
                                continue
                            max_entrepots_par_region[centre] = max_e
                            centres.append(centre)
                            print(f"{centre} ajouté comme centre de région avec max {max_e} entrepôts.")
                            break
                        except ValueError:
                            print("Veuillez entrer un nombre valide.")
            else:
                print("Choix invalide. Veuillez entrer un numéro valide.")
        except ValueError:
            print("Veuillez entrer un numéro valide.")
    
    return centres, max_entrepots_par_region

# Saisie des données
print("=== Configuration du problème d'optimisation ===")
villes = saisir_villes()

print("\nSaisie des coûts des usines")
couts_usine = saisir_donnees_ville(villes, "Coût de l'usine")

print("\nSaisie des coûts des entrepôts")
couts_entrepot = saisir_donnees_ville(villes, "Coût de l'entrepôt")

print("\nSaisie des rentabilités des usines")
rentabilite_usine = saisir_donnees_ville(villes, "Rentabilité de l'usine")

print("\nSaisie des rentabilités des entrepôts")
rentabilite_entrepot = saisir_donnees_ville(villes, "Rentabilité de l'entrepôt")

while True:
    try:
        budget_total = float(input("\nEntrez le budget total : "))
        if budget_total <= 0:
            print("Le budget doit être positif.")
            continue
        break
    except ValueError:
        print("Veuillez entrer un nombre valide.")

distances = saisir_distances(villes)

while True:
    try:
        diametre_region = float(input("\nEntrez le diamètre maximal des régions : "))
        if diametre_region <= 0:
            print("Le diamètre doit être positif.")
            continue
        break
    except ValueError:
        print("Veuillez entrer un nombre valide.")

# La variable max_entrepots n'est plus demandée ici car elle est maintenant spécifique à chaque région

while True:
    try:
        distance_min_usines = float(input("\nEntrez la distance minimale entre deux usines : "))
        if distance_min_usines < 0:
            print("La distance minimale doit être positive ou nulle.")
            continue
        break
    except ValueError:
        print("Veuillez entrer un nombre valide.")

# La saisie des priorités a été supprimée
centres_regions, max_entrepots_par_region = choisir_centres(villes)

# Création du modèle
m = gp.Model("Selection d'usines et entrepôts")

# Variables binaires pour les usines
x_U = m.addVars(villes, vtype=GRB.BINARY, name="usine")

# Variables binaires pour les entrepôts dans les villes
y = m.addVars(villes, vtype=GRB.BINARY, name="entrepot_ville")

# Fonction objectif : maximiser la rentabilité
m.setObjective(
    gp.quicksum(rentabilite_usine[i] * x_U[i] for i in villes) +
    gp.quicksum(rentabilite_entrepot[i] * y[i] for i in villes),
    GRB.MAXIMIZE
)

# Contrainte de budget total
m.addConstr(
    gp.quicksum(couts_usine[i] * x_U[i] for i in villes) +
    gp.quicksum(couts_entrepot[i] * y[i] for i in villes) <= budget_total,
    "Budget")

# Contrainte de liaison entre entrepôt et usine
for i in villes:
    m.addConstr(y[i] <= x_U[i], name=f"Entrepot_Liaison_{i}")

# Contrainte de distance minimale entre usines
for i in range(len(villes)):
    for j in range(i+1, len(villes)):
        ville_i = villes[i]
        ville_j = villes[j]
        distance_ij = distances.get(tuple(sorted((ville_i, ville_j))), float('inf'))
        if distance_ij < distance_min_usines:
            m.addConstr(x_U[ville_i] + x_U[ville_j] <= 1, name=f"Dist_Min_Usines_{ville_i}_{ville_j}")

# Contrainte de limitation des entrepôts par région
for centre in centres_regions:
    region = [ville for ville in villes if (ville == centre or distances.get(tuple(sorted((ville, centre))), float('inf')) <= diametre_region)]
    m.addConstr(gp.quicksum(y[i] for i in region) <= max_entrepots_par_region[centre], name=f"Region_Limite_{centre}")

# Résolution du modèle
m.optimize()

# Affichage des résultats
print("\n=== Résultats de l'optimisation ===")
if m.status == GRB.OPTIMAL:
    print("\nSolution optimale trouvée :")
    
    # Affichage des usines et entrepôts construits
    usines_construites = []
    entrepots_construits = []
    
    for i in villes:
        if x_U[i].x > 0.5:
            usines_construites.append(i)
            print(f"Une usine est construite à {i}.")
        if y[i].x > 0.5:
            entrepots_construits.append(i)
            print(f"Un entrepôt est construit à {i}.")
    
    # Vérification des distances entre usines
    print("\nVérification des distances entre usines construites:")
    for i in range(len(usines_construites)):
        for j in range(i+1, len(usines_construites)):
            ville_i = usines_construites[i]
            ville_j = usines_construites[j]
            distance_ij = distances.get(tuple(sorted((ville_i, ville_j))), float('inf'))
            print(f"Distance entre usines {ville_i} et {ville_j}: {distance_ij} (Minimum requis: {distance_min_usines})")
    
    # Vérification du nombre d'entrepôts par région
    print("\nVérification du nombre d'entrepôts par région:")
    for centre in centres_regions:
        region = [ville for ville in villes if (ville == centre or distances.get(tuple(sorted((ville, centre))), float('inf')) <= diametre_region)]
        entrepots_dans_region = [ville for ville in region if ville in entrepots_construits]
        print(f"Région de {centre}: {len(entrepots_dans_region)}/{max_entrepots_par_region[centre]} entrepôts")
        print(f"  Villes de la région: {', '.join(region)}")
        print(f"  Entrepôts dans la région: {', '.join(entrepots_dans_region) if entrepots_dans_region else 'Aucun'}")
    
    print(f"\nRentabilité maximale : {m.objVal:.2f}")
    cout_total = sum(couts_usine[i] * x_U[i].x for i in villes) + sum(couts_entrepot[i] * y[i].x for i in villes)
    print(f"Budget utilisé: {cout_total:.2f} / {budget_total:.2f} ({cout_total/budget_total*100:.1f}%)")
else:
    print("Aucune solution optimale trouvée.")
    print("Vérifiez les contraintes du problème.")