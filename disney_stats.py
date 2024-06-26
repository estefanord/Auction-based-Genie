import numpy as np
import pandas as pd
import seaborn as sns
from tabulate import tabulate
import matplotlib.pyplot as plt
import random
import os
import json
from disney_visitors import Agent
from disney_activities import Attraction, Activity

class Park:
    """ Park simulation class """

    def __init__(self, attraction_list, activity_list, plot_range, version=1.0, random_seed=0, verbosity=0):
        """ 
        Required Inputs:
            attraction_list: list of attractions dictionaries
            activity_list: list of activity dictionaries
        Optional Inputs:
            random_seed: seeds random number generation for reproduction
            version: specify the version
            verbosity: display metrics
        """

        # static
        self.attraction_list = attraction_list
        self.activity_list = activity_list
        self.plot_range = plot_range
        self.random_seed = random_seed
        self.version = version
        self.verbosity = verbosity

        # dynamic
        self.schedule = {}
        self.agents = {}
        self.attractions = {}
        self.activities = {}
        self.history = {"total_active_agents": {}, "distributed_passes": 0, "redeemed_passes": 0}
        self.time = 0
        self.arrival_index = 0
        self.park_close = None
    
    def generate_arrival_schedule(self, arrival_seed, total_daily_agents, perfect_arrivals):
        """ 
        Builds a schedule that determines how many agents arrive each minute throughout the day.
        Each minute of the day is assigned from a Poisson distribution. A Poisson distribution generally
        characterizes arrivals in many different settings. It is good to use if the arrivals are all
        random and independent of each other.

        Required Inputs:
            arrival_seed: Dictionary of arrival distributions
            total_daily_agents: Total agents visiting during the day
        Optional Inputs:
            perfect_arrivals: Enforces the exact number of daily agents to visit
        """

        if sum(arrival_seed.values()) != 100:
            raise AssertionError(
                "The percent of hourly arrivals does not add up to 100%"
            )

        # determine how many hours the park is open
        operating_hours = len(arrival_seed)
        if operating_hours > 24:
            raise AssertionError(f"Arrival Schedule suggests park is open more than 24 hours ({operating_hours})")

        # generate arrivals per minute by drawing from poisson distribution
        for hour, key in zip(range(operating_hours), arrival_seed):
            arrival_pct = arrival_seed[key]
            # The first hour with 0 arrivals dictates the park is closed
            if arrival_pct == 0 and not self.park_close:
                self.park_close = hour * 60

            total_hour_agents = total_daily_agents * arrival_pct * 0.01 # convert integer pct to decimal
            expected_minute_agents = total_hour_agents/60

            # enforces randomness across hours but retains reproducibilty
            rng = np.random.default_rng(self.random_seed+hour) 
            minute_arrivals = list(rng.poisson(lam=expected_minute_agents, size=60))


            for minute, arrivals in zip(range(60), minute_arrivals):
                exact_minute = hour*60 + minute
                self.schedule.update({exact_minute: arrivals})
        
        # enfore perfect arrivals
        random.seed(self.random_seed)
        if perfect_arrivals:
            actual_total_daily_agents = sum(self.schedule.values())
            dif = actual_total_daily_agents - total_daily_agents
            if dif > 0:
                for _ in range(dif):
                    rng_key = random.choice(list(key for key, val in self.schedule.items() if val>0))
                    self.schedule[rng_key] -= 1
            if dif < 0:
                for _ in range(dif*-1):
                    rng_key = random.choice(list(key for key, val in self.schedule.items() if val>0))
                    self.schedule[rng_key] += 1
                    
            assert sum(self.schedule.values()) == total_daily_agents

    def generate_agents(self, behavior_archetype_distribution, exp_ability_pct, exp_wait_threshold, exp_limit):
        """ Take a dictionary of agent behavior archetype distributions. Initializes agents. """

        if sum(behavior_archetype_distribution.values()) != 100:
            raise AssertionError(
                "The percent of behavior archetypes does not add up to 100%"
            )

        total_agents = sum(self.schedule.values())
        for agent_id in range(total_agents):
            random.seed(self.random_seed + agent_id)
            exp_ability = random.uniform(0,1) < exp_ability_pct

            agent = Agent(random_seed=self.random_seed)
            agent.initialize_agent(
                agent_id=agent_id,
                behavior_archetype_distribution=behavior_archetype_distribution,
                exp_ability=exp_ability,
                exp_wait_threshold=exp_wait_threshold,
                exp_limit=exp_limit,
                attraction_names=[attraction["name"] for attraction in self.attraction_list], 
                activity_names=[activity["name"] for activity in self.activity_list], 
            ) 
            self.agents.update({agent_id: agent})

    def generate_attractions(self):
        """ Initializes attractions """

        self.attraction_list = sorted(self.attraction_list, key=lambda k: k['popularity']) 
        for attraction in self.attraction_list:
            self.attractions.update(
                {
                    attraction["name"]: Attraction(attraction_characteristics=attraction)
                }
            )
    
    def generate_activities(self):
        """ Initializes activities """

        self.activity_list = sorted(self.activity_list, key=lambda k: k['popularity']) 
        for activity in self.activity_list:
            self.activities.update(
                {
                    activity["name"]: Activity(activity_characteristics=activity, random_seed=self.random_seed)
                }
            )

    def step(self):
        """ A minute of time passes, update all agents and attractions. """

        # allow new arrivals to enter
        total_arrivals = self.schedule[self.time]
        for new_arrival_index in range(total_arrivals):
            agent_index = self.arrival_index + new_arrival_index
            self.agents[agent_index].arrive_at_park(time=self.time)
        
        self.arrival_index += total_arrivals

        # get idle agents
        idle_agent_ids = self.get_idle_agent_ids()

        # get idle activity action
        for agent_id in idle_agent_ids:
            action, location = self.agents[agent_id].make_state_change_decision(
                attractions_dict=self.attractions, 
                activities_dict=self.activities, 
                time=self.time,
                park_closed=self.park_close<=self.time,
            )
            if action == "get pass":
                self.history["distributed_passes"] += 1
            self.update_park_state(
                agent=self.agents[agent_id], 
                action=action, 
                location=location, 
                time=self.time,
                attractions=self.attractions
            )
            
        # process attractions
        for attraction_name, attraction in self.attractions.items():
            exiting_agents, loaded_agents = attraction.step(time=self.time, park_close=self.park_close)
            for agent_id in exiting_agents:
                self.agents[agent_id].agent_exited_attraction(name=attraction_name, time=self.time)
            for agent_id in loaded_agents:
                if self.agents[agent_id].state["current_action"] == "browsing":
                    # force exit if expedited queue estimate was too high
                    self.activities[self.agents[agent_id].state["current_location"]].force_exit(agent_id=agent_id)
                    self.agents[agent_id].agent_exited_activity(
                        name=self.agents[agent_id].state["current_location"],
                        time=self.time
                    )
                redeem = self.agents[agent_id].agent_boarded_attraction(name=attraction_name, time=self.time)
                if redeem:
                    self.history["redeemed_passes"] += 1

        # process activities
        for activity_name, activity in self.activities.items():
            exiting_agents = activity.step(time=self.time)
            for agent_id in exiting_agents:
                self.agents[agent_id].agent_exited_activity(name=activity_name, time=self.time)

        # update time counters and history
        for agent in self.agents.values():
            agent.pass_time()
        for attraction in self.attractions.values():
            attraction.pass_time()
            attraction.store_history(time=self.time)
        for activity in self.activities.values():
            activity.pass_time()
            activity.store_history(time=self.time)

        self.calculate_total_active_agents()

        if self.verbosity == 1 and self.time % 60 == 0:
            self.print_metrics()
        if self.verbosity == 2:
            self.print_metrics()

        self.time += 1

    def get_idle_agent_ids(self):
        """ Identifies agents within park who have just arrived, who have exited a ride or who have left an activity """

        idle_agent_ids = [
            agent_id for agent_id, agent_dict in self.agents.items()
            if agent_dict.state["within_park"] and agent_dict.state["current_action"] == "idling"
        ]

        return idle_agent_ids
    
    def update_park_state(self, agent, action, location, time, attractions):
        """ Updates the agent state, attraction state and activity state based on the action """

        if action == "leaving":
            if agent.state["expedited_pass"]:
                for attraction in agent.state["expedited_pass"]:
                    self.attractions[attraction].return_pass(agent.agent_id)
                    agent.return_exp_pass(attraction=attraction)
            agent.leave_park(time=time)
            
        if action == "traveling":
            if location in self.attractions:
                agent.enter_queue(attraction=location, time=time)
                self.attractions[location].add_to_queue(agent_id=agent.agent_id)

            if location in self.activities:
                agent.begin_activity(activity=location, time=time)
                self.activities[location].add_to_activity(
                    agent_id=agent.agent_id, 
                    expedited_return_time=agent.state["expedited_return_time"]
                )

        if action == "get pass":
            agent.get_pass(attraction=location, time=time)
            self.attractions[location].remove_pass()
            expedited_wait_time = self.attractions[location].add_to_exp_queue(agent_id=agent.agent_id)
            agent.assign_expedited_return_time(expedited_wait_time=expedited_wait_time)

    def calculate_total_active_agents(self):
        """ Counts how many agents are currently active within the park """

        active_agents = len([agent_id for agent_id, agent in self.agents.items() if agent.state["within_park"]])
        self.history["total_active_agents"].update({self.time: active_agents})

    def print_metrics(self):
        """ Prints park metrics """

        print(f"Time: {self.time}")
        print(f"Total Visitors in Park: {self.history['total_active_agents'][self.time]}")
        print(f"Attraction Wait Times (Minutes):")
        for attraction_name, attraction in self.attractions.items():
            print(f"     {attraction_name}: {attraction.history['queue_wait_time'][self.time]}")
        print(f"Activity Visitor (Visitors):")
        for activity_name, activity in self.activities.items():
            print(f"     {activity_name}: {activity.history['total_vistors'][self.time]}")
        print(f"{'-'*50}\n")

    @staticmethod
    def make_lineplot(dict_list, x, y, hue, title, location, show=False, y_max=None):
        """ Create a hued lineplot derived from a list of dictionaries """
        
        df = pd.DataFrame(dict_list)
        l = [time for ind, time in enumerate(list(df['Time'].unique())) if ind%60==0]
        plt.figure(figsize=(15,8))
        ax = sns.lineplot(data=df, x=x, y=y, hue=hue)
        ax.set(xticks=l, xticklabels=l, title=title)
        ax.tick_params(axis='x', rotation=45)
        if y_max:
            ax.set(ylim=(0, y_max))
        plt.savefig(location, transparent=False, facecolor="white", bbox_inches="tight")
        plt.savefig(f"{location} Transparent", transparent=True, bbox_inches="tight")
        plt.show()
        if not show:
            plt.close()
    
    @staticmethod
    def make_histogram(dict_list, x, title, location, show=False):
        """ Create a histogram derived from a list of dictionaries """
        
        df = pd.DataFrame(dict_list)
        l = sorted(list(set(val for val in df[x])))
        plt.figure(figsize=(15,8))
        ax = sns.histplot(data=df, x=x, stat="percent", bins=np.arange(-0.5, len(l))) # weird trick to align labels
        ax.set(title=title, xticks=l, xticklabels=l)
        plt.savefig(location, transparent=False, facecolor="white", bbox_inches="tight")
        plt.savefig(f"{location} Transparent", transparent=True, bbox_inches="tight")
        plt.show()
        if show:
            disp_df = pd.DataFrame(df[x].describe()).reset_index()
            disp_df.columns = ["Metric", x]
            print(
                tabulate(
                    disp_df, 
                    headers='keys', 
                    tablefmt='psql', 
                    showindex=False,
                    floatfmt=('.2f')
                )
            )
        if not show:
            plt.close()
    
    @staticmethod
    def make_barplot(dict_list, x, y, hue, y_max, title, location, estimator=None, show=False):
        """ Create a hued barplot derived from a list of dictionaries """

        df = pd.DataFrame(dict_list)
        plt.figure(figsize=(15,8))
        if estimator:
            ax = sns.barplot(data=df, x=x, y=y, hue=hue, ci=None, estimator=estimator)
        else:
            ax = sns.barplot(data=df, x=x, y=y, hue=hue)
        ax.set(title=title)
        if y_max:
            ax.set(ylim=(0, y_max))
        plt.savefig(location, transparent=False, facecolor="white", bbox_inches="tight")
        plt.savefig(f"{location} Transparent", transparent=True, bbox_inches="tight")
        plt.show()
        if show and not estimator:
            print(
                tabulate(
                    df.sort_values(hue), 
                    headers='keys', 
                    tablefmt='psql', 
                    showindex=False,
                    floatfmt=('.2f')
                )
            )
        if show and estimator==sum:
            print(
                tabulate(
                    df.groupby(x).sum().reset_index(),
                    headers='keys', 
                    tablefmt='psql', 
                    showindex=False,
                )
            )
        if not show:
            plt.close()
             

    def make_plots(self, show=False):
        """ Plots key park information, save to version folder """

        version_path = os.path.join(f"{self.version}")
        if not os.path.exists(version_path):
            os.mkdir(version_path)

        # Attractions
        queue_length = []
        queue_wait_time = []
        exp_queue_length = []
        exp_queue_wait_time = []
        for attraction_name, attraction in self.attractions.items():
            for time, val in attraction.history["queue_length"].items():
                queue_length.append({"Time": time, "Visitors": val, "Attraction": attraction_name})
            for time, val in attraction.history["queue_wait_time"].items():
                queue_wait_time.append({"Time": time, "Minutes": val, "Attraction": attraction_name})
            for time, val in attraction.history["exp_queue_length"].items():
                exp_queue_length.append({"Time": time, "Visitors": val, "Attraction": attraction_name})
            for time, val in attraction.history["exp_queue_wait_time"].items():
                exp_queue_wait_time.append({"Time": time, "Minutes": val, "Attraction": attraction_name})
        
        avg_queue_wait_time = []
        for attraction_name, attraction in self.attractions.items():
            queue_wait_list = [
                val for time, val in attraction.history["queue_wait_time"].items()
                if time <= self.park_close
            ]
            exp_queue_wait_list = [
                val for time, val in attraction.history["exp_queue_wait_time"].items()
                if time <= self.park_close
            ]
            avg_queue_wait_time.append(
                {
                    "Attraction": attraction_name,
                    "Average Wait Time": sum(queue_wait_list)/len(queue_wait_list),
                    "Queue Type": "Standby"
                }
            )
            avg_queue_wait_time.append(
                {
                    "Attraction": attraction_name,
                    "Average Wait Time": sum(exp_queue_wait_list)/len(exp_queue_wait_list),
                    "Queue Type": "Expedited"
                }
            )

        # Activities
        total_vistors = []
        for activity_name, activity in self.activities.items():
            for time, val in activity.history["total_vistors"].items():
                total_vistors.append({"Time": time, "Visitors": val, "Activity": activity_name})

        # Agent Distribution
        broad_agent_distribution = []
        for time, total_agents in self.history["total_active_agents"].items():
            broad_agent_distribution.append(
                {
                    "Time": time,
                    "Approximate Percent": sum(
                        [attraction.history["queue_length"][time] for attraction in self.attractions.values()]
                    )/total_agents if total_agents > 0 else 0,
                    "Type": "Attractions"
                }
        )
            broad_agent_distribution.append(
                {
                    "Time": time,
                    "Approximate Percent": sum(
                        [activity.history["total_vistors"][time] for activity in self.activities.values()]
                    )/total_agents if total_agents > 0 else 0,
                    "Type": "Activities"
                }
        )
            
        specific_agent_distribution = []
        for time, total_agents in self.history["total_active_agents"].items():
            for attraction_name, attraction in self.attractions.items():
                specific_agent_distribution.append(
                    {
                        "Time": time,
                        "Approximate Percent": attraction.history["queue_length"][time]/total_agents if total_agents > 0 else 0,
                        "Type": attraction_name
                    }
            )
            for activity_name, activity in self.activities.items():
                specific_agent_distribution.append(
                    {
                        "Time": time,
                        "Approximate Percent": activity.history["total_vistors"][time]/total_agents if total_agents > 0 else 0,
                        "Type": activity_name
                    }
            )


        attraction_counter = []
        attraction_density = []
        for agent_id, agent in self.agents.items():
            attraction_counter.append(
                {
                    "Agent": agent_id,
                    "Behavior": agent.behavior["archetype"],
                    "Total Attractions Visited": sum(
                        attraction['times_completed'] for attraction in agent.state["attractions"].values()
                    )
                }
            )
            for attraction, attraction_dict in agent.state["attractions"].items():
                attraction_density.append(
                    {
                        "Attraction": attraction,
                        "Visits": attraction_dict["times_completed"]
                    }
                )

        self.make_lineplot(
            dict_list=queue_length, 
            x="Time", 
            y="Visitors", 
            hue="Attraction",
            y_max=self.plot_range["Attraction Queue Length"], 
            title="Ride Queue Length",
            location=f"{self.version}/Attraction Queue Length",
            show=show,
        )

        self.make_lineplot(
            dict_list=queue_wait_time, 
            x="Time", 
            y="Minutes", 
            hue="Attraction",
            y_max=self.plot_range["Attraction Wait Time"],  
            title="Ride Wait Time",
            location=f"{self.version}/Attraction Wait Time",
            show=show,
        )

        self.make_lineplot(
            dict_list=exp_queue_length, 
            x="Time", 
            y="Visitors", 
            hue="Attraction",
            y_max=self.plot_range["Attraction Expedited Queue Length"],  
            title="Ride Queue Length (Fastpass)",
            location=f"{self.version}/Attraction Expedited Queue Length",
            show=show,
        )

        self.make_lineplot(
            dict_list=exp_queue_wait_time, 
            x="Time", 
            y="Minutes", 
            hue="Attraction",
            y_max=self.plot_range["Attraction Expedited Wait Time"],  
            title="Ride Wait Time (Fastpass)",
            location=f"{self.version}/Attraction Expedited Wait Time",
            show=show,
        )

        self.make_lineplot(
            dict_list=total_vistors, 
            x="Time", 
            y="Visitors", 
            hue="Activity",
            y_max=self.plot_range["Activity Vistors"],  
            title="Non-ride Tourists",
            location=f"{self.version}/Activity Vistors",
            show=show,
        )

        self.make_lineplot(
            dict_list=broad_agent_distribution, 
            x="Time", 
            y="Approximate Percent", 
            hue="Type",
            y_max=self.plot_range["Approximate Agent Distribution (General)"],  
            title="Agent Distribution (General)",
            location=f"{self.version}/Approximate Agent Distribution (General)",
            show=show,
        )

        self.make_lineplot(
            dict_list=specific_agent_distribution, 
            x="Time", 
            y="Approximate Percent", 
            hue="Type",
            y_max=self.plot_range["Approximate Agent Distribution (Specific)"],  
            title="Agent Distribution (Specific)",
            location=f"{self.version}/Approximate Agent Distribution (Specific)",
            show=show,
        )

        self.make_barplot(
            dict_list=avg_queue_wait_time, 
            x="Attraction", 
            y="Average Wait Time", 
            hue="Queue Type",
            y_max=self.plot_range["Attraction Average Wait Times"],
            title="Average Ride Waiting Time", 
            location=f"{self.version}/Attraction Average Wait Times", 
            show=show
        )

        self.make_histogram(
            dict_list=attraction_counter, 
            x="Total Attractions Visited", 
            title="Rides per Visitor Percentage", 
            location=f"{self.version}/Agent Attractions Histogram",
            show=show,
        )

        self.make_barplot(
            dict_list=attraction_density, 
            x="Attraction", 
            y="Visits", 
            hue=None,
            y_max=self.plot_range["Attraction Total Visits"],
            estimator=sum,
            title="Ride Total Visits", 
            location=f"{self.version}/Attraction Total Visits", 
            show=show
        )

        self.make_barplot(
            dict_list= [
                {   
                    "Expedited Passes": " ",
                    "Total Passes": self.history["distributed_passes"],
                    "Type": "Distributed"
                },
                {
                    "Expedited Passes": " ",
                    "Total Passes": self.history["redeemed_passes"],
                    "Type": "Redeemed"
                }
            ], 
            x="Expedited Passes", 
            y="Total Passes",
            hue="Type", 
            y_max=self.plot_range["Expedited Pass Distribution"],
            title="Fast Pass Distribution", 
            location=f"{self.version}/Expedited Pass Distribution", 
            show=show
        )
        self.make_barplot(
            dict_list= [
                {   
                    "Age Class": " ",
                    "Visitors": len([agent_id for agent_id, agent in self.agents.items() if agent.state["age_class"] == "no_child_rides"]),
                    "Type": "No Child Rides"
                },
                {
                    "Age Class": " ",
                    "Visitors": len([agent_id for agent_id, agent in self.agents.items() if agent.state["age_class"] == "no_adult_rides"]),
                    "Type": "No Adult Rides"
                },
                {
                    "Age Class": " ",
                    "Visitors": len([agent_id for agent_id, agent in self.agents.items() if agent.state["age_class"] == "no_preference"]),
                    "Type": "No Preference"
                },
            ], 
            x="Age Class", 
            y="Visitors",
            hue="Type", 
            y_max=self.plot_range["Age Class Distribution"],
            title="Age Distribution", 
            location=f"{self.version}/Age Class Distribution", 
            show=show
        )

    def print_logs(self, N=None, selected_agent_ids=None):
        """ Prints the logs of random agents or a list of agents """

        if N:
            all_agent_ids = list(self.agents.keys())
            random.seed(self.random_seed)
            selected_agent_ids = random.sample(all_agent_ids, N)
        for agent_id in selected_agent_ids:
            print(f"Agent ID: {agent_id}")
            print(f"Agent Archetype: {self.agents[agent_id].behavior['archetype']}")
            print(f"{self.agents[agent_id].log}\n")

    @staticmethod
    def write_data_to_file(data, output_file_path, output_file_format):
        """ Takes a data object, writes and saves as a pickle or json. """

        full_path = output_file_path + "." + output_file_format
        if isinstance(full_path, str):
            if output_file_format not in {"json"}:
                raise ValueError(f"Incompatible file format :{output_file_format}")
            # Create folder if not already present
            folder = os.path.dirname(full_path)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            mode = "wt"
            file_writer = open(full_path, mode)
        else:
            raise ValueError("full_path must be specified")

        writers = {
            "json": lambda file_writer: json.dump(data, file_writer, indent=2),
        }
        writers[output_file_format](file_writer)
        file_writer.close()

    def generate_auction_file(self):
        output = ["ITEMS TO SELL:"]
        # List attractions as items for sale
        for attraction_name, attraction in self.attractions.items():
            time_slots = int((60 / attraction.run_time) * 12)
            num_passes = int((attraction.capacity * attraction.exp_queue_ratio)) 
            passes_per_time = int((num_passes * (time_slots / 3) / 30))
            output.append(f" {passes_per_time} {attraction.name} T=morning")
            output.append(f" {passes_per_time} {attraction.name} T=afternoon")
            output.append(f" {passes_per_time} {attraction.name} T=evening")
        
        
        output.append("---------------")
        
        # Generate bids section for each agent
        selected_agents = random.sample(list(self.agents.items()), min(350, len(self.agents)))

        for agent_id, agent in selected_agents:
            output.append(f"Name: Agent {agent_id}")
            output.append("Bids:")
            
            for attraction_name, attraction in self.attractions.items():
                unique_seed = self.random_seed + agent.agent_id * 5
                random.seed(unique_seed)
                random_term = random.uniform(-15, 15)
                time_slots = int((60 / attraction.run_time) * 12)
                num_passes = int((attraction.capacity * attraction.exp_queue_ratio))
                times = {3: "morning", 10: "afternoon", 30: "evening"}
                for i in times.keys():
                    bid_value = (0.45 * attraction.popularity) + 0.20* (agent.behavior['attraction_preference'] + agent.behavior['wait_threshold']) - 0.10 * i + random_term
                    bid_value = int(max(bid_value, 1))
                    output.append(f"  {bid_value}  {attraction_name} T={times[i]}")
            
            output.append("------------")

        # Write the structured data to a file
        with open('auction_input.txt', 'w') as file:
            for line in output:
                file.write(line + "\n")
    
    
    def allocate_passes_from_auction_results(self):
        with open("extended_auction_results.txt", 'r') as file:
            lines = file.readlines()

        current_agent_id = None
        for line in lines:
            if line.startswith('Agent_'):
                # Extract the agent ID from the line
                agent_id = int(line.split()[1])
                current_agent_id = agent_id
                parts = line.split()
                ride = int(parts[2])
                time = parts[3][2:]
                # Assign the pass to the agent
                if time in ["morning", "afternoon", "evening"]:
                    time = convert_time_slot_to_minutes(self, time, ride)  
                    self.agents[current_agent_id].assign_expedited_return_time(time)
                    self.agents[current_agent_id].get_pass(ride, time)


def convert_time_slot_to_minutes(self, time, ride):
        # Example conversion, adjust based on your simulation setup
    unique_seed = self.random_seed
    random.seed(unique_seed)
    ride = "ride " + str(ride)
    for attraction_name, attraction in self.attractions.items():
        if attraction == ride:
            attraction = self.attractions[ride]
            time_slots = int((60 / attraction.run_time) * 12)
            if time == 'morning':
                random_term = random.uniform(0, int(time_slots / 3))
                return random_term  
            elif time == 'afternoon':
                random_term = random.uniform(int(time_slots / 3), int(2 * time_slots / 3))
                return random_term
            elif time == 'evening':
                random_term = random.uniform(int(2 * time_slots / 3), time_slots)
                return random_term
            return 0


        
    



        
    

    

