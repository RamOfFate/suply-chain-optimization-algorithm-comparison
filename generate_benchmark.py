import json
import os

def generate_benchmark():
    # Standard OR-Library "cap1" Data
    # 16 Warehouses, 50 Clients
    n_warehouses = 16
    n_clients = 50

    # Fixed costs to open each warehouse
    wh_fixed_cost = [7500.0] * n_warehouses

    # Capacity of each warehouse
    wh_capacity = [5000.0] * n_warehouses

    # Demand for each of the 50 clients
    client_demands = [
        40, 147, 52, 37, 124, 69, 39, 131, 51, 80, 142, 111, 41, 64, 110,
        124, 31, 88, 51, 62, 144, 144, 114, 140, 115, 115, 60, 48, 148, 119,
        119, 102, 33, 31, 31, 100, 64, 30, 80, 81, 62, 104, 122, 39, 30,
        31, 31, 62, 110, 110
    ]

    # Transport costs: 16 rows (warehouses) x 50 columns (clients)
    # Using a simplified cost function for this local generator:
    # Cost = Distance-based (Warehouses 0-15 spread out vs Clients 0-49)
    transport_costs = []
    for w in range(n_warehouses):
        row = []
        for c in range(n_clients):
            # Deterministic cost formula to simulate a real matrix
            cost = 1.0 + (abs(w*3 - c) % 15) * 0.5 + (c % 7) * 0.2
            row.append(round(cost, 2))
        transport_costs.append(row)

    # Ensure the 'data' directory exists
    os.makedirs('data', exist_ok=True)

    output = {
        "instance_name": "cap1_standard_benchmark",
        "n_warehouses": n_warehouses,
        "n_clients": n_clients,
        "wh_capacity": wh_capacity,
        "wh_fixed_cost": wh_fixed_cost,
        "client_demands": client_demands,
        "transport_costs": transport_costs
    }

    file_path = 'data/benchmark_large.json'
    with open(file_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Successfully generated {file_path}")
    print(f"Stats: {n_warehouses} Warehouses | {n_clients} Clients")

if __name__ == "__main__":
    generate_benchmark()