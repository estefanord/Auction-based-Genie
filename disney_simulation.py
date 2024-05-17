from disney_stats import Park
from disney_visitors import BEHAVIOR_ARCHETYPE_PARAMETERS

TOTAL_DAILY_AGENTS = 1000
PERFECT_ARRIVALS = True
HOURLY_PERCENT = {
    "10:00 AM": 10,
    "11:00 AM": 20,
    "12:00 AM": 17,
    "3:00 PM": 20,
    "4:00 PM": 15,
    "5:00 PM": 10,
    "6:00 PM": 1,
    "7:00 PM": 5,
    "8:00 PM": 1,
    "9:00 PM": 1,
    "10:00 PM": 0,
    "11:00 PM": 0,
    "12:00 PM": 0
}
EXP_ABILITY_PCT = 0.7
EXP_THRESHOLD = 1
EXP_LIMIT = 1

AGENT_ARCHETYPE_DISTRIBUTION = {
    "ride_enthusiast": 30,
    "ride_favorer": 15,
    "park_tourer": 20,
    "park_visitor": 20,
    "activity_favorer": 10,
    "activity_enthusiast": 5,
}

ATTRACTIONS = [
    {
        "name": "ride 1",
        "run_time": 10,
        "hourly_throughput": 100,
        "popularity": 10,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.9,
        "child_eligible": True,
        "adult_eligible": True,
    },
    {
        "name": "ride 2",
        "run_time": 5,
        "hourly_throughput": 80,
        "popularity": 9,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.8,
        "child_eligible": True,
        "adult_eligible": True,
    },
    {
        "name": "ride 3",
        "run_time": 15,
        "hourly_throughput": 80,
        "popularity": 8,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.8,
        "child_eligible": True,
        "adult_eligible": True,
    },
    {
        "name": "ride 4",
        "run_time": 5,
        "hourly_throughput": 90,
        "popularity": 7,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.85,
        "child_eligible": True,
        "adult_eligible": True,
    },
    {
        "name": "ride 5",
        "run_time": 10,
        "hourly_throughput": 70,
        "popularity": 6,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.8,
        "child_eligible": False,
        "adult_eligible": True,
    },
    {
        "name": "ride 6",
        "run_time": 6,
        "hourly_throughput": 80,
        "popularity": 5,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.7,
        "child_eligible": True,
        "adult_eligible": True,
    },
    {
        "name": "ride 7",
        "run_time": 12,
        "hourly_throughput": 60,
        "popularity": 4,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.8,
        "child_eligible": False,
        "adult_eligible": True,
    },
    {
        "name": "ride 8",
        "run_time": 5,
        "hourly_throughput": 90,
        "popularity": 9,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.8,
        "child_eligible": True,
        "adult_eligible": True,
    },
    {
        "name": "ride 9",
        "run_time": 15,
        "hourly_throughput": 90,
        "popularity": 8,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.8,
        "child_eligible": True,
        "adult_eligible": True,
    },
    {
        "name": "ride 10",
        "run_time": 5,
        "hourly_throughput": 80,
        "popularity": 7,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.85,
        "child_eligible": True,
        "adult_eligible": True,
    },
    {
        "name": "ride 11",
        "run_time": 10,
        "hourly_throughput": 60,
        "popularity": 6,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.8,
        "child_eligible": False,
        "adult_eligible": True,
    },
    {
        "name": "ride 12",
        "run_time": 6,
        "hourly_throughput": 70,
        "popularity": 5,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.7,
        "child_eligible": True,
        "adult_eligible": True,
    },
    {
        "name": "ride 13",
        "run_time": 12,
        "hourly_throughput": 80,
        "popularity": 4,
        "expedited_queue": True,
        "expedited_queue_ratio": 0.8,
        "child_eligible": False,
        "adult_eligible": True,
    }
]

ACTIVITIES = [
    {
      "name": "sightseeing",
      "popularity": 5,
      "mean_time": 10
    },
    {
      "name": "show",
      "popularity": 5,
      "mean_time": 30
    },
    {
      "name": "merchandise",
      "popularity": 5,
      "mean_time": 30
    },
    {
      "name": "food",
      "popularity": 5,
      "mean_time": 45
    }
  ]

PLOT_RANGE = {
    "Attraction Queue Length": 1800,
    "Attraction Wait Time": 200,
    "Attraction Expedited Queue Length": 6000,
    "Attraction Expedited Wait Time": 500,
    "Activity Vistors": 20000,
    "Approximate Agent Distribution (General)": 1.0,
    "Approximate Agent Distribution (Specific)": 1.0,
    "Attraction Average Wait Times": 120,
    "Agent Attractions Histogram": 1.0,
    "Attraction Total Visits": 46000,
    "Expedited Pass Distribution": 150000,
    "Age Class Distribution": 20000,
}

VERSION = "#AGENTS - 1"
VERBOSITY = 3
SHOW_PLOTS = True

RNG_SEED = 3

park = Park(
    attraction_list=ATTRACTIONS,
    activity_list=ACTIVITIES,
    plot_range=PLOT_RANGE,
    random_seed=RNG_SEED,
    version=VERSION,
    verbosity=VERBOSITY
)

# Build Arrivals

park.generate_arrival_schedule(
    arrival_seed=HOURLY_PERCENT, 
    total_daily_agents=TOTAL_DAILY_AGENTS, 
    perfect_arrivals=PERFECT_ARRIVALS,
)

# Build Agents
park.generate_agents(
    behavior_archetype_distribution=AGENT_ARCHETYPE_DISTRIBUTION,
    exp_ability_pct=EXP_ABILITY_PCT,
    exp_wait_threshold=EXP_THRESHOLD,
    exp_limit=EXP_LIMIT
)

# Build Attractions + Activities
park.generate_attractions()
park.generate_activities()

# Pass Time
for _ in range(len(HOURLY_PERCENT.keys()) * 60):
    park.step()

# Save Parameters of Current Run
sim_parameters = {
    "VERSION": VERSION,
    "VERBOSITY": VERBOSITY,
    "SHOW_PLOTS": SHOW_PLOTS,
    "RNG_SEED": RNG_SEED,
    "TOTAL_DAILY_AGENTS": TOTAL_DAILY_AGENTS,
    "PERFECT_ARRIVALS": PERFECT_ARRIVALS,
    "HOURLY_PERCENT": HOURLY_PERCENT,
    "EXP_ABILITY_PCT": EXP_ABILITY_PCT,
    "EXP_THRESHOLD": EXP_THRESHOLD,
    "EXP_LIMIT": EXP_LIMIT,
    "AGENT_ARCHETYPE_DISTRIBUTION": AGENT_ARCHETYPE_DISTRIBUTION,
    "ATTRACTIONS": ATTRACTIONS,
    "ACTIVITIES": ACTIVITIES,
    "BEHAVIOR_ARCHETYPE_PARAMETERS": BEHAVIOR_ARCHETYPE_PARAMETERS,
}
park.write_data_to_file(
    data=sim_parameters, 
    output_file_path=f"{VERSION}/parameters", 
    output_file_format="json"
)

# Store + Print Data
#park.make_plots(show=SHOW_PLOTS)
#park.print_logs(N = 5)
#park.print_logs(selected_agent_ids = [778])
park.generate_auction_file()




