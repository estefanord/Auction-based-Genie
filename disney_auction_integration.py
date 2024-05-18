import numpy as np
import numpy as np
import re
from collections import Counter, namedtuple
from disney_VCG import Auction, Bidder

def reduce_bids(input_file, output_file, bids_per_agent=5):
        with open(input_file, 'r') as file:
            lines = file.readlines()
    
        new_lines = []
        in_agent_section = False
        agent_bids = []
        collecting_items = True  # Flag to collect items until agents start

        for line in lines:
            if line.startswith("ITEMS TO SELL:") or collecting_items:
                new_lines.append(line)
                if line.startswith("---------------"):  # End of items section
                    collecting_items = False
                continue

            if line.startswith("Name:"):  # Start of a new agent's bids
                if agent_bids:  # If there are bids collected, process and append them
                    # Sort bids based on the numerical value in descending order
                    sorted_bids = sorted(agent_bids, key=lambda x: float(x.split()[0]), reverse=True)
                    # Select top bids
                    selected_bids = sorted_bids[:bids_per_agent]
                    new_lines.extend(selected_bids)
                    new_lines.append("------------\n")
                new_lines.append(line)
                new_lines.append("Bids:\n")  # Ensure the Bids line is added after agent name
                agent_bids = []  # Reset bids list for the new agent
                in_agent_section = True
            elif line.startswith("------------") and in_agent_section:  # Marks the end of an agent's bids
                if agent_bids:
                    # Sort and select top bids for the last collected agent
                    sorted_bids = sorted(agent_bids, key=lambda x: float(x.split()[0]), reverse=True)
                    selected_bids = sorted_bids[:bids_per_agent]
                    new_lines.extend(selected_bids)
                new_lines.append("------------\n")
                in_agent_section = False
                agent_bids = []
            elif in_agent_section and line.strip() and not line.startswith("Bids:"):  # Collect bids for the current agent
                agent_bids.append(line)

        # Process the last agent's bids if any
        if agent_bids:
            sorted_bids = sorted(agent_bids, key=lambda x: float(x.split()[0]), reverse=True)
            selected_bids = sorted_bids[:bids_per_agent]
            new_lines.extend(selected_bids)
            new_lines.append("------------\n")

        with open(output_file, 'w') as file:
            file.writelines(new_lines)

reduce_bids("auction_input.txt", "1.txt", bids_per_agent=10)

# Reimplementation still in process - GA
'''''

class Bidder:
    def __init__(self, name):
        self.name = name
        self.bids = []

    def add_bid(self, items, bid):
        self.bids.append((items, bid))

class Auction:
    def __init__(self):
        self.items = Counter()

    def add_item(self, name, qty):
        self.items[name] += qty

def parse_auction_specs(file_path):
    num_str_re = re.compile(
        r'^\s*(?P<num>(\d+(\.\d*)?)|(\.\d+))?\s*(?P<name>[a-zA-Z].*?)\s*$')
    midx_num = num_str_re.groupindex['num']
    midx_name = num_str_re.groupindex['name']
    key_val_re = re.compile(
        r'^\s*(?P<key>\w[\w\s]*?)\s*:\s*(?P<val>\w[\w\s.]*?)\s*$')
    midx_key = key_val_re.groupindex['key']
    midx_val = key_val_re.groupindex['val']

    auction = Auction()
    bidders = []
    this_bidder = Bidder("Bidder #{}".format(len(bidders) + 1))
    parser_state = 'expecting item list'

    with open(file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        errmsg = 'Could not parse line "{}"'.format(line.rstrip('\n'))

        if line.isspace() or line.startswith('#'):
            pass
        elif parser_state == 'expecting item list':
            if line.lower().startswith('items to sell'):
                parser_state = 'item list'
            else:
                raise ValueError(errmsg)
        elif parser_state == 'item list':
            if line.startswith('---'):
                parser_state = 'bidder header'
                continue
            m = num_str_re.match(line)
            if m is None:
                raise ValueError(errmsg)
            name = m.group(midx_name)
            qty = int(m.group(midx_num)) if m.group(midx_num) else 1
            auction.add_item(name, qty)
        elif parser_state == 'bidder header':
            if line.lower().startswith('bids'):
                parser_state = 'bids'
                continue
            m = key_val_re.match(line)
            if m is None:
                raise ValueError(errmsg)
            attr = m.group(midx_key).lower()
            val = m.group(midx_val)
            if attr.startswith('name'):
                this_bidder.name = val
            else:
                raise ValueError(errmsg)
        elif parser_state == 'bids':
            if line.startswith('---'):
                bidders.append(this_bidder)
                this_bidder = Bidder("Bidder #{}".format(len(bidders) + 1))
                parser_state = 'bidder header'
                continue
            m = num_str_re.match(line)
            if m is None:
                raise ValueError(errmsg)
            bid = m.group(midx_num)
            if bid is None:
                raise ValueError(errmsg)
            bid = float(bid)
            items = m.group(midx_name).split('&')
            items = [item.strip().lower() for item in items]
            this_bidder.add_bid(items, bid)
        else:
            raise AssertionError('Unknown state "{}"'.format(parser_state))

    if parser_state == 'bidder header':
        if not bidders:
            raise ValueError("No bidders found")
    elif parser_state == 'bids':
        bidders.append(this_bidder)
    else:
        raise ValueError("Unexpected end of file")

    bidder_name_counts = Counter([b.name for b in bidders])
    [most_common_bidder] = bidder_name_counts.most_common(1)
    if most_common_bidder[1] > 1:
        raise ValueError('Duplicate bidder "{}" found'.format(most_common_bidder[0]))

    return auction, bidders

def initialize_population(bidders, items, population_size):
    population = []
    for _ in range(population_size):
        individual = {bidder.name: np.random.choice(items, size=len(bidder.bids), replace=False) for bidder in bidders}
        population.append(individual)
    return population

def fitness(individual, bidders):
    fitness_value = 0
    for bidder in bidders:
        allocations = individual[bidder.name]
        for bid_items, bid in bidder.bids:
            if any(item in allocations for item in bid_items):
                fitness_value += bid
    return fitness_value

def selection(population, bidders):
    fitnesses = [fitness(individual, bidders) for individual in population]
    probabilities = fitnesses / np.sum(fitnesses)
    selected_indices = np.random.choice(len(population), size=len(population), p=probabilities)
    return [population[i] for i in selected_indices]

def crossover(parent1, parent2):
    child1, child2 = {}, {}
    for agent in parent1.keys():
        if np.random.rand() < 0.5:
            child1[agent], child2[agent] = parent1[agent], parent2[agent]
        else:
            child1[agent], child2[agent] = parent2[agent], parent1[agent]
    return child1, child2

def mutate(individual, items, mutation_rate):
    for agent in individual.keys():
        if np.random.rand() < mutation_rate:
            individual[agent] = np.random.choice(items, size=len(individual[agent]), replace=False)
    return individual

def genetic_algorithm(bidders, items, population_size, num_generations, mutation_rate):
    population = initialize_population(bidders, items, population_size)
    best_allocation = None
    best_fitness = -np.inf
    
    for generation in range(num_generations):
        population = selection(population, bidders)
        new_population = []
        for i in range(0, len(population), 2):
            if i + 1 < len(population):
                parent1, parent2 = population[i], population[i + 1]
                child1, child2 = crossover(parent1, parent2)
                new_population.append(mutate(child1, items, mutation_rate))
                new_population.append(mutate(child2, items, mutation_rate))
        population = new_population
        fitnesses = [fitness(individual, bidders) for individual in population]
        current_best_fitness = max(fitnesses)
        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_allocation = population[np.argmax(fitnesses)]
    
    return best_allocation, best_fitness

# Load data and run the genetic algorithm
input_file = '1.txt'
auction, bidders = parse_auction_specs(input_file)
items = list(auction.items.elements())
population_size = 100
num_generations = 50
mutation_rate = 0.01

best_allocation, best_fitness = genetic_algorithm(bidders, items, population_size, num_generations, mutation_rate)

print(f"Best allocation found: {best_allocation}")
print(f"Best fitness value: {best_fitness}")'''''
