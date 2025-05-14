# optimization_solver.py
import gurobipy as gp
from gurobipy import GRB

class Solver:
    def __init__(self, data):
        self.data = data
        self.villes = data['villes']
        self.model = None
        self.x_U = None
        self.y = None
        
    def build_model(self):
        # Create model
        self.model = gp.Model("Selection d'usines et entrepôts")
        
        # Create variables
        self.x_U = self.model.addVars(self.villes, vtype=GRB.BINARY, name="usine")
        self.y = self.model.addVars(self.villes, vtype=GRB.BINARY, name="entrepot_ville")
        
        # Set objective
        self.model.setObjective(
            gp.quicksum(self.data['rentabilite_usine'][i] * self.x_U[i] for i in self.villes) +
            gp.quicksum(self.data['rentabilite_entrepot'][i] * self.y[i] for i in self.villes),
            GRB.MAXIMIZE
        )
        
        # Add constraints
        self._add_constraints()
    
    def _add_constraints(self):
        # Budget constraint
        self.model.addConstr(
            gp.quicksum(self.data['couts_usine'][i] * self.x_U[i] for i in self.villes) +
            gp.quicksum(self.data['couts_entrepot'][i] * self.y[i] for i in self.villes) <= self.data['budget_total'],
            "Budget"
        )
        
        # Warehouse-factory linkage
        for i in self.villes:
            self.model.addConstr(self.y[i] <= self.x_U[i], name=f"Entrepot_Liaison_{i}")
        
        if len(self.villes) > 1:
            self.model.addConstr(
                gp.quicksum(self.y[i] for i in self.villes) >= 1,
                name="Min_One_Entrepot_If_Factory"
            )
        
       


        # Distance constraints
        distances = self.data['distances']
        distance_min = self.data['distance_min_usines']
        for i in range(len(self.villes)):
            for j in range(i+1, len(self.villes)):
                ville_i = self.villes[i]
                ville_j = self.villes[j]
                distance_ij = distances.get(tuple(sorted((ville_i, ville_j))), float('inf'))
                if distance_ij < distance_min:
                    self.model.addConstr(self.x_U[ville_i] + self.x_U[ville_j] <= 1, 
                                      name=f"Dist_Min_Usines_{ville_i}_{ville_j}")
    
    def solve(self):
        self.model.optimize()
        return self._format_results()
    
    def _format_results(self):
        if self.model.status == GRB.OPTIMAL:
            results = {
                'usines': [ville for ville in self.villes if self.x_U[ville].x > 0.5],
                'entrepots': [ville for ville in self.villes if self.y[ville].x > 0.5],
                'profitabilite': self.model.objVal,
                'budget_utilise': sum(
                    self.data['couts_usine'][ville] * self.x_U[ville].x +
                    self.data['couts_entrepot'][ville] * self.y[ville].x
                    for ville in self.villes
                )
            }
            return results
        return None