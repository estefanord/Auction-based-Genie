import numpy as np

class Attraction:

    def __init__(self, attraction_characteristics):
        """  
        Required Inputs:
            attraction_characteristics: dictionary of characteristics for the attraction        
        """

        self.attraction_characteristics = attraction_characteristics
        self.state = {} # characterizes attractions current state
        self.history = {} 

        if (
            type(self.attraction_characteristics["popularity"]) != int 
            or self.attraction_characteristics["popularity"] < 1
            or self.attraction_characteristics["popularity"] > 10
        ):
            raise AssertionError(
                f"Attraction {self.attraction_characteristics['name']} 'popularity' value must be an integer between"
                "1 and 10"
            )
        self.initialize_attraction()

    
    def initialize_attraction(self):
        """ Sets up the attraction """ 

        #characteristics
        self.name = self.attraction_characteristics["name"]
        self.run_time = self.attraction_characteristics["run_time"]
        self.capacity = self.attraction_characteristics["hourly_throughput"] * (self.attraction_characteristics["run_time"]/60) 
        self.popularity = self.attraction_characteristics["popularity"]
        self.child_eligible = self.attraction_characteristics["child_eligible"]
        self.adult_eligible = self.attraction_characteristics["adult_eligible"]
        self.run_time_remaining = 0
        self.expedited_queue = self.attraction_characteristics["expedited_queue"]
        self.exp_queue_ratio = self.attraction_characteristics["expedited_queue_ratio"]
        self.exp_queue_passes = 0

        #state
        self.state["agents_in_attraction"] = []
        self.state["queue"] = []
        self.state["exp_queue"] = []
        self.state["exp_queue_passes_distributed"] = 0

        # history
        self.history["queue_length"] = {}
        self.history["queue_wait_time"] = {}
        self.history["exp_queue_length"] = {}
        self.history["exp_queue_wait_time"] = {}
           

    def get_wait_time(self):
        """ Returns the expected queue wait time according the the equation
        """

        if self.expedited_queue:
            queue_len = len(self.state["queue"])
            exp_queue_len = len(self.state["exp_queue"])
            exp_seats = int(self.capacity * self.exp_queue_ratio)
            standby_seats = self.capacity - exp_seats

            runs = 0
            while queue_len >= self.capacity:    
                if exp_queue_len > exp_seats:
                    exp_queue_len -= exp_seats
                    if queue_len > standby_seats:
                        queue_len -= standby_seats
                    else:
                        queue_len = 0
                else:
                    queue_len -= self.capacity - exp_queue_len
                    exp_queue_len = 0
                
                runs += 1

            return runs * self.run_time + self.run_time_remaining
        else:
            return (len(self.state["queue"]) // self.capacity) * self.run_time + self.run_time_remaining
    
    def get_exp_wait_time(self):
        """ Returns the expected queue wait time according the the equation
        """

        if self.expedited_queue:
            queue_len = len(self.state["queue"])
            exp_queue_len = len(self.state["exp_queue"])
            exp_seats = int(self.capacity * self.exp_queue_ratio)
            standby_seats = self.capacity - exp_seats

            runs = 0
            while exp_queue_len >= self.capacity:    
                if exp_queue_len > exp_seats:
                    exp_queue_len -= exp_seats
                    if queue_len > standby_seats:
                        queue_len -= standby_seats
                    else:
                        queue_len = 0
                else:
                    queue_len -= self.capacity - exp_queue_len
                    exp_queue_len = 0
                
                runs += 1

            return runs * self.run_time + self.run_time_remaining
        else:
            return 0
    
    def add_to_queue(self, agent_id):
        """ Adds an agent to the queue """

        self.state["queue"].append(agent_id)
    
    def add_to_exp_queue(self, agent_id):
        """ Adds an agent to the expeditied queue """

        self.state["exp_queue"].append(agent_id)
        expedited_wait_time = self.get_exp_wait_time()
        return expedited_wait_time

    def remove_pass(self):
        """ Removes a expedited pass """

        self.exp_queue_passes -= 1
        self.state["exp_queue_passes_distributed"] += 1
        
    def return_pass(self, agent_id):
        """ Removes an expedited pass without redeeming it """

        self.exp_queue_passes += 1
        self.state["exp_queue_passes_distributed"] -= 1
        self.state["exp_queue"].remove(agent_id)

    def step(self, time, park_close):
        """ Handles the following actions:
            - Allows agents to exit attraction if the run is complete
            - Loads expedited queue agents
            - Loads queue agents
            - Begins Ride
        """
        
        exiting_agents = []
        loaded_agents = []

        # calculate total exp queue passes available
        if self.expedited_queue:
            if time < park_close:
                remaining_operating_hours = (park_close - time) // 60
                passed_operating_hours = time // 60
                self.exp_queue_passes = (
                    (self.capacity * (60/self.run_time) * self.exp_queue_ratio * remaining_operating_hours) 
                    - max(
                            (
                                self.state["exp_queue_passes_distributed"] - 
                                (self.capacity * (60/self.run_time) * self.exp_queue_ratio * passed_operating_hours)
                            )
                        , 0
                    )
                )
            else:
                self.exp_queue_passes = 0 

        if self.run_time_remaining == 0:
            # left agents off attraction
            exiting_agents = self.state["agents_in_attraction"]
            self.state["agents_in_attraction"] = []
            self.run_time_remaining = self.run_time

            # devote seats to queue and expedited queue
            max_exp_queue_agents = int(self.capacity * self.exp_queue_ratio)
            # Handle case where expedited queue has fewer agents than the maximum number of expedited queue spots
            if len(self.state["exp_queue"]) < max_exp_queue_agents:
                max_queue_agents = int(self.capacity - len(self.state["exp_queue"]))
            else:
                max_queue_agents = int(self.capacity - max_exp_queue_agents)
            
            # load expeditied queue agents
            expedited_agents_to_load = [agent_id for agent_id in self.state["exp_queue"][:max_exp_queue_agents]]
            self.state["agents_in_attraction"] = expedited_agents_to_load
            self.state["exp_queue"] = self.state["exp_queue"][max_exp_queue_agents:]

            # load queue agents
            agents_to_load = [agent_id for agent_id in self.state["queue"][:max_queue_agents]]
            self.state["agents_in_attraction"].extend(agents_to_load)
            self.state["queue"] = self.state["queue"][max_queue_agents:]

            loaded_agents = self.state["agents_in_attraction"]
        
        return exiting_agents, loaded_agents

    def pass_time(self):
        """ Pass 1 minute of time """

        self.run_time_remaining -= 1

    def store_history(self, time):
        """ Stores metrics """

        self.history["queue_length"].update(
            {
                time: len(self.state["queue"])
            }
        ) 
        self.history["queue_wait_time"].update(
            {
                time: self.get_wait_time()
            }
        )
        self.history["exp_queue_length"].update(
            {
                time: len(self.state["exp_queue"])
            }
        ) 
        self.history["exp_queue_wait_time"].update(
            {
                time: self.get_exp_wait_time()
            }
        ) 




class Activity:

    def __init__(self, activity_characteristics, random_seed=None):
        """  
        Required Inputs:
            activity_characteristics: dictionary of characteristics for the activity        
        """

        self.activity_characteristics = activity_characteristics
        self.state = {} # characterizes activity current state
        self.history = {} 
        self.random_seed = random_seed

        if (
            type(self.activity_characteristics["popularity"]) != int 
            or self.activity_characteristics["popularity"] < 0
            or self.activity_characteristics["popularity"] > 10
        ):
            raise AssertionError(
                f"activity {self.activity_characteristics['name']} 'popularity' value must be an integer between"
                "1 and 10"
            )
        self.initialize_activity()

    
    def initialize_activity(self):

        #characteristics
        self.name = self.activity_characteristics["name"]
        self.popularity = self.activity_characteristics["popularity"]
        self.mean_time = self.activity_characteristics["mean_time"]
       
        #state
        self.state["visitors"] = []
        self.state["visitor_time_remaining"] = []

        # history
        self.history["total_vistors"] = {}
           

    def add_to_activity(self, agent_id, expedited_return_time):
        """ Adds an agent to the activity and generates the time they will spend there. """

        self.state["visitors"].append(agent_id)

        if self.random_seed:
            rng = np.random.default_rng(self.random_seed+agent_id)
            stay_time = int(
                max((rng.normal(self.mean_time, self.mean_time/2, 1))[0], 1)
            )
        else:
            stay_time = int(
                max((np.random.normal(self.mean_time, self.mean_time/2, 1))[0], 1)
            )
        
        # if agent has is waiting in exp queue, make them leave before they need to board ride
        if expedited_return_time:
            stay_time = min(max(1, min(expedited_return_time)), stay_time)
        
        self.state["visitor_time_remaining"].append(stay_time)

    def force_exit(self, agent_id):
        """ Handles case where agent is forced to leave an activity to get on their
        expedited queue attraction """

        ind = self.state["visitors"].index(agent_id)
        del self.state["visitors"][ind]
        del self.state["visitor_time_remaining"][ind]

    def step(self, time):
        """ Handles the following actions:
            - Allows agents to exit activity if they've spent all their time there
        """

        exiting_agents = [
            (ind, agent_id) for ind, agent_id in enumerate(self.state["visitors"])
            if self.state["visitor_time_remaining"][ind] == 0
        ]

        # remove from visitor list, going in reverse maintins indices
        exiting_agents.reverse()
        for ind, agent_id in exiting_agents:
            del self.state["visitors"][ind]
            del self.state["visitor_time_remaining"][ind]

        exiting_agents = [agent_id for ind, agent_id in exiting_agents]

        return exiting_agents

    def pass_time(self):
        """ Pass 1 minute of time """

        self.state["visitor_time_remaining"] = [visitor_time-1 for visitor_time in self.state["visitor_time_remaining"]]

    def store_history(self, time):
        """ Stores metrics """

        self.history["total_vistors"].update(
            {
                time: len(self.state["visitors"])
            }
        ) 