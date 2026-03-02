import sys
import json
import random
import time
import os
import psutil

def solve_ga(data_path):
    process = psutil.Process(os.getpid())
    last_best_cost = 120000.0

    try:
        with open(data_path, 'r') as f:
            data = json.load(f)

        costs = data.get('transport_costs', data.get('costs'))
        fixed_costs = data.get('wh_fixed_cost', [])
        num_w = len(costs)
        num_c = len(costs[0])

        # Hyperparameters
        pop_size = 100
        generations = 1000
        mutation_rate = 0.08  # Increased slightly to help it reach the 7734 floor
        tournament_size = 5

        def get_cost(ind):
            # 1. Transport Costs (Sum of assigned WH for each client)
            transport_total = sum(costs[ind[c]][c] for c in range(num_c))

            # 2. Fixed Costs (Only for warehouses that have at least one client)
            used_whs = set(ind)
            fixed_total = sum(fixed_costs[wh_idx] for wh_idx in used_whs)

            return transport_total + fixed_total

        # Initial Population
        pop = [[random.randint(0, num_w - 1) for _ in range(num_c)] for _ in range(pop_size)]

        for gen in range(generations):
            # Calculate costs once per generation for performance
            pop.sort(key=get_cost)
            current_best_cost = get_cost(pop[0])

            # --- TELEMETRY ---
            mem = process.memory_info().rss / (1024 * 1024)
            velocity = last_best_cost - current_best_cost
            last_best_cost = current_best_cost

            # Print to C++ Dashboard
            print(f"DATA|{gen}|{current_best_cost:.2f}|{mem:.2f}|{velocity:.2f}", flush=True)

            # Evolution: Elitism
            new_pop = pop[:5]

            while len(new_pop) < pop_size:
                # Tournament Selection
                parents = []
                for _ in range(2):
                    competitors = random.sample(pop, tournament_size)
                    parents.append(min(competitors, key=get_cost))

                # Crossover
                cut = random.randint(1, num_c - 1)
                child = parents[0][:cut] + parents[1][cut:]

                # Mutation
                if random.random() < mutation_rate:
                    child[random.randint(0, num_c - 1)] = random.randint(0, num_w - 1)

                new_pop.append(child)

            pop = new_pop
            time.sleep(0.001)

    except Exception as e:
        sys.stderr.write(f"GA Smart Error: {str(e)}\n")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/benchmark_large.json"
    solve_ga(path)