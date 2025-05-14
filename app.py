# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from ROOOOOOOO import Solver
app = Flask(__name__)
CORS(app)

@app.route('/solve', methods=['POST'])
def solve_optimization():
    try:
        data = request.get_json()
        
        # Validate input data
        required_fields = [
            'villes', 'couts_usine', 'couts_entrepot',
            'rentabilite_usine', 'rentabilite_entrepot',
            'budget_total', 'distances', 'distance_min_usines'
        ]
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Convert distances format
        distances = {}
        for d in data['distances']:
            key = tuple(sorted((d['from'], d['to'])))
            distances[key] = d['distance']
        data['distances'] = distances
        
        # Solve the problem
        solver = Solver(data)
        solver.build_model()
        results = solver.solve()
        
        if results:
            return jsonify({
                "usines_construites": results['usines'],
                "entrepots_construits": results['entrepots'],
                "profitabilite_totale": results['profitabilite'],
                "budget_utilise": results['budget_utilise'],
                "budget_total": data['budget_total']
            })
        else:
            return jsonify({"error": "Aucune solution optimale trouvée"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)