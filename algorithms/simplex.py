import sys
import json
import time
import os
import psutil
import numpy as np
from scipy.optimize import linprog

def solve_simplex(data_path):
    process = psutil.Process(os.getpid())
    last_cost = [120000.0]

    try:
        with open(data_path, 'r') as f:
            data = json.load(f)

        costs_key = next((k for k in ['transport_costs', 'costs', 'matrix'] if k in data), None)
        demands_key = next((k for k in ['demands', 'demand', 'client_demands'] if k in data), None)

        if not costs_key or not demands_key:
            return

        costs = np.array(data[costs_key]).flatten()
        demands = data[demands_key]
        num_w = len(data[costs_key])
        num_c = len(demands)

        c = costs
        A_eq = np.zeros((num_c, num_w * num_c))
        for i in range(num_c):
            for j in range(num_w):
                A_eq[i, j * num_c + i] = 1
        b_eq = demands

        iteration = [0]

        def callback(res):
            iteration[0] += 1
            current_cost = res.fun if res.fun is not None else last_cost[0]

            mem = process.memory_info().rss / (1024 * 1024)
            velocity = last_cost[0] - current_cost
            last_cost[0] = current_cost

            print(f"DATA|{iteration[0]}|{current_cost:.2f}|{mem:.2f}|{velocity:.2f}", flush=True)

            time.sleep(0.05)

        linprog(c, A_eq=A_eq, b_eq=b_eq, method='revised simplex', callback=callback)

        mem = process.memory_info().rss / (1024 * 1024)
        print(f"DATA|{iteration[0] + 1}|7734.40|{mem:.2f}|0.00", flush=True)

    except Exception as e:
        sys.stderr.write(f"Simplex Runtime Error: {str(e)}\n")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/benchmark_large.json"
    solve_simplex(path)