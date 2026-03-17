from collections import deque
import json
import os
from typing import Dict, List, Optional
from regex_parser import parse_regex
import networkx as nx
import matplotlib.pyplot as plt


EPSILON = "ε"

class State:
    def __init__(self, state_num: int):
        self.name = f"S{state_num}"
        self.transitions: Dict[str, List["State"]] = {}

    def add_transition(self, next_state: "State", symbol: str = EPSILON):
        if symbol not in self.transitions:
            self.transitions[symbol] = []
        self.transitions[symbol].append(next_state)

class NFA:
    def __init__(self,states_count:int=0,init_state:Optional[State]=None,accept_state:Optional[State]=None):
        self.states_count=states_count
        self.init_state=init_state
        self.accept_state=accept_state

    def add_state(self):
        self.states_count+=1
        return State(self.states_count-1)
    
    # OR
    def union(self,state1:"NFA",state2:"NFA") ->"NFA":
        init_state = self.add_state()
        accept_state = self.add_state()
        
        init_state.add_transition(state1.init_state)
        init_state.add_transition(state2.init_state)
        
        state1.accept_state.add_transition(accept_state)
        state2.accept_state.add_transition(accept_state)
        
        return NFA(
            init_state=init_state,
            accept_state=accept_state
        )
    
    #zero or more operator    
    def star(self,state:"NFA")->"NFA":
        init_state=self.add_state()
        accept_state=self.add_state()

        init_state.add_transition(state.init_state)
        init_state.add_transition(accept_state)

        state.accept_state.add_transition(init_state)
        state.accept_state.add_transition(accept_state)

        return NFA(init_state=init_state,accept_state=accept_state)
    
    #one or more operator 
    def plus(self,state:"NFA")->"NFA":
        init_state=self.add_state()
        accept_state=self.add_state()

        init_state.add_transition(state.init_state)

        state.accept_state.add_transition(init_state)
        state.accept_state.add_transition(accept_state)

        return NFA(init_state=init_state,accept_state=accept_state)
    
    # one or zero 
    def optional(self,state:"NFA")->"NFA":
        init_state=self.add_state()
        accept_state=self.add_state()

        init_state.add_transition(state.init_state)
        init_state.add_transition(accept_state)

        state.accept_state.add_transition(accept_state)

        return NFA(init_state=init_state,accept_state=accept_state)
    
    def concat(self,state1:"NFA",state2:"NFA")->"NFA":
        result = state1
        
        result.accept_state.add_transition(state2.init_state)
        
        result.accept_state = state2.accept_state
        
        return result
    
    def variable_state(self,variable:str)->"NFA":
        init_state = self.add_state()
        accept_state = self.add_state()
        
        init_state.add_transition(accept_state, variable)
        
        return NFA(
            init_state=init_state,
            accept_state=accept_state
        )
    
    def build_regex_nfa(self,regex:str) ->"NFA":
        processed_tokens=[]
        postfix=parse_regex(regex)
        for token in postfix:
            if token == "*":
                subset=self.star(processed_tokens[-1])
                processed_tokens.pop()
                processed_tokens.append(subset)
            elif token == "+":
                subset=self.plus(processed_tokens[-1])
                processed_tokens.pop()
                processed_tokens.append(subset)
            elif token == "?":
                subset=self.optional(processed_tokens[-1])
                processed_tokens.pop()
                processed_tokens.append(subset)
            elif token == "_":
                subset=self.concat(processed_tokens[-2],processed_tokens[-1])
                processed_tokens.pop()
                processed_tokens.pop()
                processed_tokens.append(subset)
            elif token == "|":
                subset=self.union(processed_tokens[-2],processed_tokens[-1])
                processed_tokens.pop()
                processed_tokens.pop()
                processed_tokens.append(subset)
            else:
                processed_tokens.append(self.variable_state(token))
        return processed_tokens[0]

    def to_dict(self) -> dict:
        """Convert the NFA to a dictionary in the specified JSON format"""
        result = {  "startingState": self.init_state.name }
        
        # BFS to collect all states
        visited, queue = set(), deque([self.init_state])
        
        while queue:
            current_state = queue.popleft()
            
            if current_state.name in visited:  continue
            visited.add(current_state.name)
            
            state_entry = {"isTerminatingState": current_state == self.accept_state}
            for edge, next_states in current_state.transitions.items():
                state_entry[edge] = [next_state.name for next_state in next_states]
                for next_state in next_states:
                    if next_state.name not in visited:
                        queue.append(next_state)
            
            result[current_state.name] = state_entry
        
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


    def plot_nfa(self, filename="nfa.png"):
        G = nx.DiGraph()
        visited = set()

        # Build graph
        def dfs(state):
            if state in visited:
                return
            visited.add(state)

            for symbol, next_states in state.transitions.items():
                for nxt in next_states:
                    G.add_edge(state.name, nxt.name, label=symbol)
                    dfs(nxt)

        dfs(self.init_state)

        # --------- LAYERED LAYOUT (clean left→right) ---------
        layers = {}
        queue = [(self.init_state, 0)]

        while queue:
            state, depth = queue.pop(0)
            name = state.name

            if name not in layers:
                layers[name] = depth

                for next_states in state.transitions.values():
                    for nxt in next_states:
                        queue.append((nxt, depth + 1))

        # assign positions
        pos = {}
        layer_nodes = {}

        for node, depth in layers.items():
            layer_nodes.setdefault(depth, []).append(node)

        for depth, nodes in layer_nodes.items():
            for i, node in enumerate(nodes):
                pos[node] = (depth, -i)  # x=depth → left to right

        # --------- Styling ---------
        node_colors = []
        for node in G.nodes():
            if node == self.init_state.name:
                node_colors.append("green")
            elif node == self.accept_state.name:
                node_colors.append("red")
            else:
                node_colors.append("lightblue")

        plt.figure(figsize=(10, 6))

        nx.draw(
            G,
            pos,
            with_labels=True,
            node_color=node_colors,
            node_size=2000,
            arrows=True
        )

        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

        # save
        os.makedirs("outputs/nfa", exist_ok=True)
        path = os.path.join("outputs/nfa", filename)

        plt.savefig(path, bbox_inches='tight')
        plt.close()

        print(f"Saved graph to: {path}")

    def save_nfa_to_json(self, file_name: str, output_folder: str):
        """
        Save the NFA transitions and states to a JSON file.
        """
        nfa_dict = self.to_dict()
        json_path = os.path.join(output_folder, file_name)
        os.makedirs(output_folder, exist_ok=True)  # Ensure the output folder exists
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(nfa_dict, json_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    regex = "[A-Z]+"

    result_nfa = NFA().build_regex_nfa(regex)

    result_nfa.plot_nfa()
    result_nfa.save_nfa_to_json("nfa_json","outputs/nfa")