import random
import copy
import json
import sys
import os
import psutil # Needed for memory tracking

# ─────────────────────────────────────────────
# 1. DATA LOADING
# ─────────────────────────────────────────────

def load_benchmark(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

# ─────────────────────────────────────────────
# 2. COST FUNCTION
# ─────────────────────────────────────────────

def evaluate(open_warehouses, assignment, data):
    total_cost = 0.0
    for i, is_open in enumerate(open_warehouses):
        if is_open:
            total_cost += data['wh_fixed_cost'][i]

    for client_idx, wh_idx in enumerate(assignment):
        if not open_warehouses[wh_idx]:
            return float('inf')
        total_cost += data['transport_costs'][wh_idx][client_idx]

    return total_cost

# ─────────────────────────────────────────────
# 3. TABU SEARCH WITH METRICS
# ─────────────────────────────────────────────

def solve_tabu(data, max_iterations=500, tabu_tenure=15):
    process = psutil.Process(os.getpid())
    n_wh = data['n_warehouses']
    n_cl = data['n_clients']

    # Initial Solution
    current_open = [True] * n_wh
    current_assignment = []
    for c in range(n_cl):
        costs = [data['transport_costs'][w][c] for w in range(n_wh)]
        current_assignment.append(costs.index(min(costs)))

    current_cost = evaluate(current_open, current_assignment, data)
    best_cost = current_cost
    last_reported_cost = current_cost

    tabu_list = {}

    # Initial Report
    mem = process.memory_info().rss / (1024 * 1024)
    print(f"DATA|0|{best_cost:.2f}|{mem:.2f}|0.00", flush=True)

    for iteration in range(1, max_iterations + 1):
        neighbors = []

        # Generate neighbors
        for _ in range(20):
            move_type = random.choice(['toggle_wh', 'reassign_client'])
            neighbor_open = list(current_open)
            neighbor_assign = list(current_assignment)

            if move_type == 'toggle_wh':
                w_idx = random.randint(0, n_wh - 1)
                neighbor_open[w_idx] = not neighbor_open[w_idx]
                if not any(neighbor_open): continue

                if not neighbor_open[w_idx]:
                    open_indices = [i for i, o in enumerate(neighbor_open) if o]
                    for c in range(n_cl):
                        if neighbor_assign[c] == w_idx:
                            neighbor_assign[c] = random.choice(open_indices)
                move_key = ('wh', w_idx)
            else:
                c_idx = random.randint(0, n_cl - 1)
                open_indices = [i for i, o in enumerate(neighbor_open) if o]
                neighbor_assign[c_idx] = random.choice(open_indices)
                move_key = ('cl', c_idx, neighbor_assign[c_idx])

            cost = evaluate(neighbor_open, neighbor_assign, data)
            neighbors.append((cost, neighbor_open, neighbor_assign, move_key))

        neighbors.sort(key=lambda x: x[0])

        for cost, n_open, n_assign, m_key in neighbors:
            if m_key in tabu_list and tabu_list[m_key] > iteration:
                if cost < best_cost: pass
                else: continue
            current_open, current_assignment, current_cost = n_open, n_assign, cost
            tabu_list[m_key] = iteration + tabu_tenure
            break

        if current_cost < best_cost:
            best_cost = current_cost

        # --- TELEMETRY CALCULATIONS ---
        # Calculate velocity (improvement since last report)
        velocity = last_reported_cost - best_cost
        last_reported_cost = best_cost

        # Get memory in MB
        mem = process.memory_info().rss / (1024 * 1024)

        # Send to C++: DATA|step|cost|mem|velocity
        print(f"DATA|{iteration}|{best_cost:.2f}|{mem:.2f}|{velocity:.2f}", flush=True)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/benchmark_large.json"
    data = load_benchmark(path)
    solve_tabu(data)