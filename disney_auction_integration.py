from disney_visitors import Agent
from disney_activities import Attraction, Activity
from disney_stats import Park

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
            elif in_agent_section and line.strip() and not line.startswith("Bids:"):  # Collecting bids for the current agent
                agent_bids.append(line)

        # Ensure to process the last agent's bids if any
        if agent_bids:
            sorted_bids = sorted(agent_bids, key=lambda x: float(x.split()[0]), reverse=True)
            selected_bids = sorted_bids[:bids_per_agent]
            new_lines.extend(selected_bids)
            new_lines.append("------------\n")

        with open(output_file, 'w') as file:
            file.writelines(new_lines)

reduce_bids("auction_input.txt", "1.txt", bids_per_agent=5)