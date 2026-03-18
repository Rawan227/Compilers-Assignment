import os
import json
import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
 
EPSILON = "ε"
 
 
# parse NFA dict
 
def parse_nfa(nfa_dict: dict):
    start_state   = nfa_dict["startingState"]
    transitions   = {}
    accept_states = set()
 
    for key, value in nfa_dict.items():
        if key == "startingState":
            continue
        transitions[key] = {}
        for symbol, dest in value.items():
            if symbol == "isTerminatingState":
                if dest:
                    accept_states.add(key)
            else:
                transitions[key][symbol] = dest
 
    return start_state, transitions, accept_states
 
 
# BFS over epsilon transitions only
 
def epsilon_closure(states: frozenset, transitions: dict) -> frozenset:
    closure = set(states)
    queue   = list(states)
 
    while queue:
        current = queue.pop()
        for next_state in transitions.get(current, {}).get(EPSILON, []):
            if next_state not in closure:
                closure.add(next_state)
                queue.append(next_state)
 
    return frozenset(closure)
 
 
# subset construction where each DFA state is a set of NFA states
 
def nfa_to_dfa(nfa_dict: dict) -> dict:
    start_state, transitions, accept_states = parse_nfa(nfa_dict)
 
    all_symbols = {
        sym
        for state_trans in transitions.values()
        for sym in state_trans
        if sym != EPSILON
    }
 
    dfa_start = epsilon_closure(frozenset({start_state}), transitions)
 
    subset_to_name = {dfa_start: "S0"}
    dfa_transitions = {dfa_start: {}} #stores dfa structure
    worklist = deque([dfa_start])
    counter  = 1
 
 # dfa states that need processing
    while worklist:
        current_subset = worklist.popleft()
 
        for symbol in all_symbols:
            moved = set()
            for nfa_state in current_subset:
                moved.update(transitions.get(nfa_state, {}).get(symbol, []))
 
            if not moved:
                continue
 
            next_subset = epsilon_closure(frozenset(moved), transitions)
 
            if next_subset not in subset_to_name:
                subset_to_name[next_subset] = f"S{counter}"
                counter += 1
                dfa_transitions[next_subset] = {}
                worklist.append(next_subset)
 
            dfa_transitions[current_subset][symbol] = subset_to_name[next_subset]
 
    result = {"startingState": subset_to_name[dfa_start]}
    for subset, name in subset_to_name.items():
        state_entry = {"isTerminatingState": bool(subset & accept_states)}
        for symbol, dest_name in dfa_transitions[subset].items():
            state_entry[symbol] = dest_name
        result[name] = state_entry
 
    return result
 
 
# minimization using table-filling algorithm
 
def minimize_dfa(dfa_dict: dict) -> dict:
    start  = dfa_dict["startingState"]
    states = [k for k in dfa_dict if k != "startingState"]
    accept = {s for s in states if dfa_dict[s]["isTerminatingState"]}
 
    def get_trans(state, symbol):
        return dfa_dict[state].get(symbol)
 
    all_symbols = {
        k
        for s in states
        for k in dfa_dict[s]
        if k != "isTerminatingState"
    }
 
    # mark accept, non-accept pairs as distinguishable
    distinguished = set()
    for p in accept:
        for q in set(states) - accept:
            distinguished.add(frozenset({p, q}))
 
    # if two states lead to a distinguished pair they are distinguished
    changed = True
    while changed:
        changed = False
        for i, p in enumerate(states):
            for q in states[i + 1:]:
                pair = frozenset({p, q})
                if pair in distinguished:
                    continue
                for symbol in all_symbols:
                    p_next = get_trans(p, symbol)
                    q_next = get_trans(q, symbol)
                    if (p_next is None) != (q_next is None):
                        distinguished.add(pair)
                        changed = True
                        break
                    if p_next and q_next and frozenset({p_next, q_next}) in distinguished:
                        distinguished.add(pair)
                        changed = True
                        break
 
    # merge states that are not distinguished
    parent = {s: s for s in states}
 
    def find(s):
        while parent[s] != s:
            parent[s] = parent[parent[s]]
            s = parent[s]
        return s
 
    def union(a, b):
        parent[find(b)] = find(a)
 
    for i, p in enumerate(states):
        for q in states[i + 1:]:
            if frozenset({p, q}) not in distinguished:
                union(p, q)
 
    groups = {}
    for s in states:
        groups.setdefault(find(s), set()).add(s)
 
    # keep start state's group as S0
    start_rep   = find(start)
    ordered_reps = [start_rep] + [r for r in groups if r != start_rep]
    rep_to_name  = {rep: f"S{i}" for i, rep in enumerate(ordered_reps)}
 
    def new_name(s):
        return rep_to_name[find(s)]
 
    result = {"startingState": new_name(start)}
    for rep, members in groups.items():
        state_entry = {"isTerminatingState": bool(members & accept)}
        for symbol in all_symbols:
            dest = get_trans(rep, symbol)
            if dest is not None:
                state_entry[symbol] = new_name(dest)
        result[rep_to_name[rep]] = state_entry
 
    return result
 
 
 # plot state diagram

def plot_dfa(dfa_dict: dict, filepath: str):
    start  = dfa_dict["startingState"]
    states = [k for k in dfa_dict if k != "startingState"]
    accept = {s for s in states if dfa_dict[s]["isTerminatingState"]}
 
    G = nx.DiGraph()
    G.add_nodes_from(states)
    edge_labels = {}
    for state in states:
        for symbol, dest in dfa_dict[state].items():
            if symbol == "isTerminatingState":
                continue
            key = (state, dest)
            edge_labels[key] = (edge_labels[key] + ", " + symbol) if key in edge_labels else symbol
            G.add_edge(state, dest)
 
    layers = {}
    queue  = deque([(start, 0)])
    while queue:
        node, depth = queue.popleft()
        if node not in layers:
            layers[node] = depth
            for nb in G.successors(node):
                queue.append((nb, depth + 1))
 
    layer_nodes = {}
    for node, depth in layers.items():
        layer_nodes.setdefault(depth, []).append(node)
 
    pos = {}
    for depth, nodes in layer_nodes.items():
        for i, node in enumerate(nodes):
            pos[node] = (depth * 2.5, -i * 2)
 
    node_colors = []
    for node in G.nodes():
        if node in accept and node == start:
            node_colors.append("orange")
        elif node == start:
            node_colors.append("green")
        elif node in accept:
            node_colors.append("red")
        else:
            node_colors.append("lightblue")
 
    fig, ax = plt.subplots(figsize=(max(8, len(states) * 3), 5))
 
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, ax=ax)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=10, font_weight="bold")
 
    if accept:
        nx.draw_networkx_nodes(
            G, {n: pos[n] for n in accept}, nodelist=list(accept),
            node_color="none", node_size=2600,
            linewidths=2.5, edgecolors="black", ax=ax
        )
 
    nx.draw_networkx_edges(
        G, pos, ax=ax, arrows=True, arrowsize=20,
        connectionstyle="arc3,rad=0.1", node_size=2000
    )
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, ax=ax)
 
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - 1.5, max(xs) + 1.5)
    ax.set_ylim(min(ys) - 1.5, max(ys) + 1.5)
 
    ax.set_title("Minimized DFA", fontsize=13)
    ax.axis("off")
 
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    plt.savefig(filepath, bbox_inches="tight", dpi=150)
    plt.close()
 
 
 
def save_dfa_json(dfa_dict: dict, filepath: str):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(dfa_dict, f, indent=2, ensure_ascii=False)