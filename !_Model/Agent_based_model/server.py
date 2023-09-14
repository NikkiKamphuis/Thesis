"""
Created on Fri 4 August 2023

@author: Nikki Kamphuis
"""
import pandas as pd

from initialise_dashboard import initialise_dashboard, dashboard_inputs
from Batch_Run.CustomBatchrunner import batch_run
from Local_Mesa.Visualisation.ModularVisualization import ModularServer
from base_model import BaseModel
import pickle
import nest_asyncio


# Determine settings
batch_run_bool = False                       # Boolean that indicates if a batch run is performed
heatmap = False                              # Boolean that indicates if a heatmap should be kept
charts = False                               # Boolean that can add additional charts to the dashboard
random_seed = True                           # Boolean that states if seed should be determined randomly
sensitivity_analysis = False                 # Boolean that states if sensitivity analysis should be conducted


# Retrieve drone and client data
file_path = 'C:/Users/kamph/Desktop/Files/11_MSc_Thesis/!_Model/Agent_based_model/Routes/Output/DroneRoutesMatrices.pkl'

with open(file_path, "rb") as f:  # Python 3: open(..., 'rb')
    (
        client_params,
        drone_distances,
        drone_risk,
        grid,
        direct_drone_distances,
        direct_drone_risks,

    ) = pickle.load(f)

# Retrieve car data
file_path2 = 'C:/Users/kamph/Desktop/Files/11_MSc_Thesis/!_Model/Agent_based_model/Routes/Output/CarRoutesMatrices.pkl'
with open(file_path2, "rb") as f:  # Python 3: open(..., 'rb')
    car_distances, car_times = pickle.load(f)

# Retrieve demand data
file_path3 = 'C:/Users/kamph/Desktop/Files/11_MSc_Thesis/!_Model/Agent_based_model/Demand/Output/Demand_new.csv'
request_list = pd.read_csv(file_path3)
request_list = request_list.set_index('start', drop=True)

# Define model parameters
model_params = {
    "grid": grid,
    "hubs": len(client_params),
    "droneInfraCosts": {
        "landingPlatforms": 30000,              # Fixed costs per year
        "missionControl": 90000,                # Cost of housing te mission control centre
    },
    "labour": {
        "driver_FTE_fulltime": 6,               # Amount of FTE needed to cover a 24/7 driver position
        "min_pilot_FTE_fulltime": 13,
        "pilot_FTE": 60000,                     # Salary of one full time drone pilot
        "driver_FTE": 50000,                    # Salary of one full time driver
        "drones_per_min_pilot_FTE": 20,         # Maximum amount of drones one pilot can operate
    },
    "decisionWeights": {
        "deliveryTime": 1,  # weight of every delivery minute
        "emmissions": 1,  # weight of every kg of Co2
        "risk": 1,  # weight of every injury per 1000000 of these trips
        "cost": 0,  # weight of every euro
    },
}

# Define drone parameters
drone_params = {
    "speed": 60,  # km/h
    "riskMatrix": drone_risk,
    "distanceMatrix": drone_distances,
    "directRiskMatrix": direct_drone_risks,
    "directDistanceMatrix": direct_drone_distances,
    "emmissionPerKm": 0.016,  # kilogram Co2 per km
    "takeOffTime": 30,  # seconds
    "landTime": 30,  # seconds
    "TAT": 300,  # seconds
    # percentages of maximum delay in travel time in different circumstances
    "delayPercentages": {
        "normalTraffic": 0.05,
        "rushHour": 0.05,
    },  #
    "capacity": 5,
    "costs": {
        "fixed": 50000,  # fixed costs per year
        "perKm": 0.1,  # variable costs per km
    },
}

# Define car parameters
car_params = {
    "normalRisk": 2.33 * 10 ** -8,  # injuries/km
    "emergencyRisk": 0.00006,  # injuries/ hour = 60 per million
    "distanceMatrix": car_distances,
    "timeMatrix": car_times,
    "emmissionPerKm": 0.12,  # kilogram Co2 per km
    "leavingTime": 0,  # seconds
    "arrivalTime": 0,  # seconds
    "TAT": 180,  # seconds
    "speedingFactor": 1.5,
    # percentages of maximum delay in travel time in different circumstances
    "delayPercentages": {
        "normalTraffic": 0.05,
        "rushHour": 0.15,
    },
    "capacity": 10,
    "costs": {
        "fixed": 5000,  # fixed costs per year
        "perKm": 0.25,  # variable costs per km
    },
}

# Initialise dashboard
# Does something Python technical with nested loops
nest_asyncio.apply()
dashboard_elements = initialise_dashboard(grid, charts)
num_drones, delivery_mode, repositioning, day_of_week, seed = dashboard_inputs(random_seed)

# Combine all model parameter inputs
full_model_params = {
    "model_params": model_params,
    "drone_params": drone_params,
    "car_params": car_params,
    "client_params": client_params,
    "num_drones": num_drones,
    "request_input": request_list,
    "day_of_week": day_of_week,
    "repositioning": repositioning,
    "delivery_mode": delivery_mode,
    "seed": seed,
    "charts": charts,
}

# Batchrun to conduct experiments
if batch_run_bool:
    model_reporters = {
        "Fulfilled demand": lambda m: m.fulfilled_request,
        "Car overdue": lambda m: m.overdue["Car"],
        "Drone overdue": lambda m: m.overdue["Drone"],
        "Total overdue": lambda m: m.total_overdue,
        "Drone fast Deliveries": lambda m: m.drone_fast_deliveries,
        "Drone safe Deliveries": lambda m: m.drone_safe_deliveries,
        "Total drone deliveries": lambda m: m.total_drone_deliveries,
        "Car fast Deliveries": lambda m: m.car_fast_deliveries,
        "Car safe Deliveries": lambda m: m.car_safe_deliveries,
        "Total Car deliveries": lambda m: m.total_car_deliveries,
        "Directly performed": lambda m: m.directly_performed,
        "Average deliverytime": lambda m: m.average_delivery_time,
        "Average drone delivery time": lambda m: m.drone_delivery_time,
        "Average drone fast delivery time": lambda m: m.drone_fast_delivery_time,
        "Average drone safe delivery time": lambda m: m.drone_safe_delivery_time,
        "Average car delivery time": lambda m: m.car_delivery_time,
        "Average car fast delivery time": lambda m: m.car_fast_delivery_time,
        "Average car safe delivery time": lambda m: m.car_safe_delivery_time,
        "Drone variablecost": lambda m: m.variable_costs["Drone"],
        "Car variablecost": lambda m: m.variable_costs["Car"],
        "Fixed configuration cost": lambda m: m.fixed_costs,
        "Labour costs": lambda m: m.labour_costs,
        "Medical facility costs": lambda m: m.medical_facility_costs,
        "Drone risk": lambda m: m.risk["Drone"],
        "Car risk": lambda m: m.risk["Car"],
        "Drone emmissions": lambda m: m.emmissions["Drone"],
        "Car emmissions": lambda m: m.emmissions["Car"],
        "Total costs": lambda m: m.total_costs,
        "Total risk": lambda m: m.total_risk,
        "Emmissions": lambda m: m.total_emmissions,
        "Fast deliveries": lambda m: m.fast_deliveries,
        "Medium deliveries": lambda m: m.medium_deliveries,
        "Late deliveries": lambda m: m.late_deliveries,
        "Drone Idle time": lambda m: m.idle_time["Drone"],
        "Car Idle time": lambda m: m.idle_time["Car"],
        "Drone safe flying empty time": lambda m: m.empty_time["Drone"]["safe"],
        "Drone fast flying empty time": lambda m: m.empty_time["Drone"]["fast"],
        "Drone safe flying filled time": lambda m: m.delivery_time["Drone"]["safe"],
        "Drone fast flying filled time": lambda m: m.delivery_time["Drone"]["fast"],
        "Car safe driving empty time": lambda m: m.empty_time["Car"]["safe"],
        "Car fast driving empty time": lambda m: m.empty_time["Car"]["fast"],
        "Car safe driving filled time": lambda m: m.delivery_time["Car"]["safe"],
        "Car fast driving filled time": lambda m: m.delivery_time["Car"]["fast"],
        "Drone delay time": lambda m: m.delay_time["Drone"],
        "Car delay time": lambda m: m.delay_time["Car"],
        "Repositionings": lambda m: m.repositionings,
        "Non idle vehicle choosen": lambda m: m.non_idle_vehicle_chosen,
        "Day of week": lambda m: m.day,
        "Total demand check": lambda m: m.total_request_check,
    }

    # ------Change the variables that are changed and kept throughout the experiment, (un)comment what should be tested

    variable_params = {
        "repositioning": True,
        "seed": range(7 * 10),
        "delivery_mode": ["combi"],
        # 'droneSpeed': [40,45,50,60,65,70,75,80,90,95,100],
        # 'TAT': [60,120,180,240,300,360,420,480,540,600],
        # 'takeOffTime': [0,30,60],
        # 'dailyDemandPer1000Beds': [15,20,25]  # [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17],
        # 'numDrones': [5,10,15],
        # 'droneRiskMultiplier': [0.0625,0.125,0.25,0.5,1,2,4,8,16],
        # "centralization":  [3,6,9],
        # 'distribution': ['Centralized', 'Distributed','Double'],
        # 'supplyPreference': ['Distance', 'Both','Beds'],
    }
    fixed_params = {
        "model_params": model_params,
        "repositioning": False,
        # 'numCars': 9,
        'num_drones': 3,
        "drone_params": drone_params,
        "car_params": car_params,
        "client_params": client_params,
        "visualization": False,
        "day_of_week": "Random",
        "track_heatmap": heatmap,
        'request_input': request_list

    }

    if __name__ == "__main__":
        writes = batch_run(
            BaseModel,
            variable_parameters=variable_params,
            fixed_parameters=fixed_params,
            max_steps=5000,
            display_progress=True,
            createHeatmaps=heatmap,
        )
        print(f"Done, with a total of {writes} writes")

# Start the dashboard if no batch run is conducted
else:
    server = ModularServer(BaseModel, dashboard_elements, "MDS simulation model", full_model_params)
    server.port = 1261
