from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import gurobipy as gp
from gurobipy import GRB

app = FastAPI()

class OptimizationInput(BaseModel):
    villes: List[str]
    couts_usine: Dict[str, float]
    couts_entrepot: Dict[str, float]
    rentabilite_usine: Dict[str, float]
    rentabilite_entrepot: Dict[str, float]
    budget_total: float
    distances: Dict[str, float]  # key: "ville1-ville2"
    diametre_region: float
    distance_min_usines: float
    centres_regions: List[str]
    max_entrepots_par_region: Dict[str, int]

@app.post("/optimize")
def optimize(data: OptimizationInput):
    villes = data.villes
    couts_usine = data.couts_usine
    couts_entrepot = data.couts_entrepot
    rentabilite_usine = data.rentabilite_usine
    rentabilite_entrepot = data.rentabilite_entrepot
    budget_total = data.budget_total
    diametre_region = data.diametre_region
    distance_min_usines = data.distance_min_usines
    centres_regions = data.centres_regions
    max_entrepots_par_region = data.max_entrepots_par_region

    # Convert distances to tuple keys
    distances = {
        tuple(sorted(k.split('-'))): v
        for k, v in data.distances.items()
    }

    m = gp.Model("Selection d'usines et entrepôts")
    m.setParam('OutputFlag', 0)

    x_U = m.addVars(villes, vtype=GRB.BINARY, name="usine")
    y   = m.addVars(villes, vtype=GRB.BINARY, name="entrepot")

    # Objectif
    m.setObjective(
        gp.quicksum(rentabilite_usine[i] * x_U[i] for i in villes) +
        gp.quicksum(rentabilite_entrepot[i] * y[i] for i in villes),
        GRB.MAXIMIZE
    )

    # Contrainte budget
    m.addConstr(
        gp.quicksum(couts_usine[i]   * x_U[i] for i in villes) +
        gp.quicksum(couts_entrepot[i] * y[i]   for i in villes)
        <= budget_total,
        name="Budget"
    )

    # Un entrepôt seulement si usine
    for i in villes:
        m.addConstr(y[i] <= x_U[i], name=f"Entrepot_Liaison_{i}")

    # Distance minimale entre usines
    for i in range(len(villes)):
        for j in range(i+1, len(villes)):
            vi, vj = villes[i], villes[j]
            d = distances.get(tuple(sorted((vi, vj))), float('inf'))
            if d < distance_min_usines:
                m.addConstr(x_U[vi] + x_U[vj] <= 1,
                            name=f"DistMin_{vi}_{vj}")

    # Limite par région
    for centre in centres_regions:
        region = [
            v for v in villes
            if v == centre or distances.get(tuple(sorted((v, centre))), float('inf')) <= diametre_region
        ]
        m.addConstr(
            gp.quicksum(y[v] for v in region) <= max_entrepots_par_region[centre],
            name=f"RegionMax_{centre}"
        )

    m.optimize()

    result = {
        "status": int(m.status),
        "usines_construites": [],
        "entrepots_construits": [],
        "rentabilite_maximale": None,
        "budget_utilise": None,
        "message": ""
    }

    if m.status == GRB.OPTIMAL:
        result["usines_construites"]    = [i for i in villes if x_U[i].x > 0.5]
        result["entrepots_construits"]  = [i for i in villes if y[i].x   > 0.5]
        result["rentabilite_maximale"]  = m.objVal
        result["budget_utilise"]        = sum(couts_usine[i]*x_U[i].x for i in villes) + \
                                          sum(couts_entrepot[i]*y[i].x   for i in villes)
        result["message"] = "Solution optimale trouvée."
    else:
        result["message"] = "Aucune solution optimale trouvée. Vérifiez les contraintes."

    return result
