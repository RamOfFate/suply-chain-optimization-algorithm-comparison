import sys
import json
import os
import psutil
import time

def load_data(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

class BranchAndBoundSolver:
    def __init__(self, data):
        self.data = data
        self.n_wh = data['n_warehouses']
        self.n_cl = data['n_clients']
        self.best_cost = 120000.0 # Start with a sane ceiling
        self.last_reported_cost = 120000.0
        self.nodes_explored = 0
        self.process = psutil.Process(os.getpid())

    def get_lower_bound(self, current_status):
        bound = 0.0
        for i in range(self.n_wh):
            if current_status[i] == 1:
                bound += self.data['wh_fixed_cost'][i]

        for c in range(self.n_cl):
            possible_costs = []
            for w in range(self.n_wh):
                if current_status[w] != 0:
                    possible_costs.append(self.data['transport_costs'][w][c])
            if not possible_costs:
                return float('inf')
            bound += min(possible_costs)
        return bound

    def report(self):
        mem = self.process.memory_info().rss / (1024 * 1024)
        velocity = self.last_reported_cost - self.best_cost
        self.last_reported_cost = self.best_cost

        display_cost = min(self.best_cost, 120000.0)
        print(f"DATA|{self.nodes_explored}|{display_cost:.2f}|{mem:.2f}|{velocity:.2f}", flush=True)

    def solve(self, wh_index, current_status):
        self.nodes_explored += 1

        if self.nodes_explored % 50 == 0:
            self.report()

        if wh_index == self.n_wh:
            if not any(s == 1 for s in current_status): return

            current_total = 0.0
            for i in range(self.n_wh):
                if current_status[i] == 1:
                    current_total += self.data['wh_fixed_cost'][i]

            open_indices = [i for i, s in enumerate(current_status) if s == 1]
            for c in range(self.n_cl):
                current_total += min(self.data['transport_costs'][w][c] for w in open_indices)

            if current_total < self.best_cost:
                self.best_cost = current_total
            return

        lb = self.get_lower_bound(current_status)
        if lb >= self.best_cost:
            return

        current_status[wh_index] = 1
        self.solve(wh_index + 1, current_status)

        current_status[wh_index] = 0
        self.solve(wh_index + 1, current_status)

        current_status[wh_index] = -1

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/benchmark_large.json"
    problem_data = load_data(path)

    solver = BranchAndBoundSolver(problem_data)
    initial_status = [-1] * solver.n_wh

    solver.report()

    solver.solve(0, initial_status)

    solver.report()