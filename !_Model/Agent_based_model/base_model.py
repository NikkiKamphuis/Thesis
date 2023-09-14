"""
Created on Tue Jul 25 2023

@author: Nikki Kamphuis
"""
from Local_Mesa import Model
from Local_Mesa.space import MultiGrid
from Local_Mesa.time import RandomActivation
from Local_Mesa.datacollection import DataCollector
import numpy as np
import random as rd
from helper_functions import (compute_open_requests,
                              compute_late_open_requests,
                              compute_average_delivery_time,
                              create_client_names,
                              rowColtoXY)
from client import Client
from drone import Drone
from car import Car
from command_center import CommandCenter


class BaseModel(Model):
    """Class that represents the core model"""

    # Function that takes input parameters
    def __init__(
        self,
        model_params,
        drone_params,
        car_params,
        client_params,
        request_input,
        num_drones,
        day_of_week="Random",  # ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        delivery_mode='safe',                     # ['safe', 'fast', 'combi'], -> route type
        repositioning=False,
        seed=2808,
        visualization=True,
        max_steps=1440,
        charts=False,
        track_heatmap=False
    ):

        ############################################ Time parameters ###################################################

        self.running = True
        self.time = 0
        self.request_counter = 0
        self.seed = seed
        rd.seed(seed)

        ############################################### Spatial parameters #############################################

        grid = model_params["grid"]
        width, height = grid.shape
        self.grid = MultiGrid(width, height, False)
        self.matrices = {}
        self.averages = {}

        ############################################# Model characteristics ############################################

        self.delivery_mode = delivery_mode                                              # fast or safe routes
        self.decision_weights = model_params["decisionWeights"]
        self.num_locations = int(len(client_params))                                    # client locations, could potentially introduce more hubs
        self.num_drones = num_drones
        self.schedule = RandomActivation(self)                                          # should this be RandomActivationByType?
        self.reposition_mode = "safe"                                                   # by default repositioning is done using the safe option
        if self.delivery_mode == "fast":                                                # only reposition using the fast option when deliverymode is set to fast
            self.reposition_mode = "fast"
        self.considered_delivery_modes = []                                             # List that contains the deliverymodes that should
                                                                                        # be used when making bids, this list only contains
                                                                                        # safe or fast for their respective modes, and contains
                                                                                        # both when using combi, thus a list is needed
        if self.delivery_mode == "fast" or self.delivery_mode == "combi":
            self.considered_delivery_modes.append("fast")

        if self.delivery_mode == "safe" or self.delivery_mode == "combi":
            self.considered_delivery_modes.append("safe")

        self.possible_delivery_modes = ["safe", "fast"]
        self.agent_types = ["Drone", "Car"]
        self.drone_infra_costs = model_params["droneInfraCosts"]
        self.labour_cost_params = model_params["labour"]
        self.delays = False                                                             # Boolean that can be activate if one were to include
                                                                                        # unexpected delays into deliveries
        self.repositioning = repositioning
        self.visualization = visualization
        self.charts = charts
        self.max_steps = max_steps
        self.fixed_costs = 0
        self.labour_costs = 0
        self.spawn_locations = []
        self.request_input = request_input

        if day_of_week == "Random":
            self.day = rd.choice([1, 2, 3, 4, 5, 6, 7])
        else:
            self.day = day_of_week

        self.track_heatmap = track_heatmap                                               # Boolean that states if a heatmap should
                                                                                         # be created tracking which routes are used
        if self.track_heatmap:
            self.track_movement_matrix = np.zeros_like(drone_params["distanceMatrix"])
            self.track_deliveries_matrix = np.zeros_like(drone_params["distanceMatrix"])

        else:
            self.track_movement_matrix = 0
            self.track_deliveries_matrix = 0

        # To save computation time, the data collector is only used when charts are displayed on the dashboard
        if self.visualization and self.charts:
            self.dc = DataCollector(
                model_reporters={
                    "Unfulfilled demand": compute_open_requests,
                    "LateUnfulfilled demand": compute_late_open_requests,
                    "Fulfilled demand": lambda m: len(m.completed_requests),
                    "overdue": lambda m: m.overdue,
                    "deliveryTime": compute_average_delivery_time,
                    "Fast drone deliveries": lambda m: m.deliveries["Drone"]["fast"],
                    "Safe drone deliveries": lambda m: m.deliveries["Drone"]["safe"],
                    "Fast car deliveries": lambda m: m.deliveries["Car"]["fast"],
                    "Safe car deliveries": lambda m: m.deliveries["Car"]["safe"],
                    "Directly performed": lambda m: m.directly_performed,
                    "Fast deliveries": lambda m: m.fast_deliveries,
                    "Medium deliveries": lambda m: m.medium_deliveries,
                    "Late deliveries": lambda m: m.late_deliveries,
                },
            )

        ######################## Initiate all value tracking parameters, lists and dicts ###############################

        self.empty_time = {}
        self.delivery_time = {}
        self.idle_time = {}
        self.delay_time = {}
        self.deliveries = {}
        self.variable_costs = {}
        self.risk = {}
        self.overdue = {}
        self.emmissions = {}

        for agent_type in self.agent_types:
            self.delay_time[agent_type] = 0
            self.idle_time[agent_type] = 0
            self.variable_costs[agent_type] = 0
            self.risk[agent_type] = 0
            self.overdue[agent_type] = 0
            self.emmissions[agent_type] = 0
            self.delivery_time[agent_type] = {}
            self.empty_time[agent_type] = {}
            self.deliveries[agent_type] = {}

            for mode in self.possible_delivery_modes:
                self.delivery_time[agent_type][mode] = 0
                self.empty_time[agent_type][mode] = 0
                self.deliveries[agent_type][mode] = []
        (
            self.clients,
            self.vehicles,
            self.requests,
            self.completed_requests,
            self.no_delivery_possible,
        ) = (
            [],
            [],
            [],
            [],
            [],
        )
        self.total_delivery_time = 0
        (
            self.fulfilled_demand,
            self.total_overdue,
            self.total_costs,
            self.total_risk,
            self.total_emissions,
            self.average_delivery_time,
            self.drone_fast_deliveries,
            self.drone_safe_deliveries,
            self.total_drone_deliveries,
            self.car_fast_deliveries,
            self.car_safe_deliveries,
            self.total_car_deliveries,
            self.car_fast_delivery_time,
            self.car_safe_delivery_time,
            self.drone_fast_delivery_time,
            self.drone_safe_delivery_time,
            self.drone_delivery_time,
            self.car_delivery_time,
        ) = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        self.directly_performed, self.total_deliveries, self.repositionings = 0, 0, 0
        self.fast_deliveries, self.medium_deliveries, self.late_deliveries = 0, 0, 0
        self.open_request_locations, self.vehicle_locations = [0] * self.num_locations, [0] * self.num_locations
        self.delivery_time_q1, self.delivery_time_median, self.delivery_time_q3 = 0, 0, 0
        self.no_idle_vehicle_chosen = 0
        self.total_demand_check, self.total_beds = 0, 0

        ###################################### Create items within model ###############################################

        # Create drone and car route matrices
        self.matrices["Drone"] = self.create_drone_time_matrix(drone_params)
        self.matrices["Car"] = self.create_car_matrices(car_params)

        # Place medical clients in model
        self.create_client_locations(client_params, width, height)

        # Determine where vehicles should be spawned (at which clients)
        self.determine_spawn_locations()

        # Place drones in model
        self.create_drones(self.num_drones, drone_params)

        # Place cars
        self.create_cars(1, car_params, self.clients)

        # Create Control center
        self.command_center = CommandCenter(-1, self, car_params, drone_params)
        self.schedule.add(self.command_center)

        # To safe computation time, the datacollector is only used when charts are displayed on the dashboard
        if self.visualization and self.charts:
            self.client_dc = self.create_client_data_collector()
        else:
            self.client_dc = None

    def create_drone_time_matrix(self, drone_params):
        """
        Function that processes and complements the route matrices created in the pre-processing module

        :param drone_params: dictionary containing drone specifics
        :return: time matrix
        """

        # Matrix containing the route travel time when taking the risk minimized option
        risk_drone_matrix = np.zeros_like(drone_params["distanceMatrix"])
        # Matrix containing the route travel time when taking the fast route
        fast_drone_matrix = np.zeros_like(drone_params["directDistanceMatrix"])

        drone_speed = drone_params["speed"] / 3.6                           # convert km/h to m/s
        take_off_time = drone_params["takeOffTime"]
        landing_time = drone_params["landTime"]

        for i in range(self.num_locations):                                 # loop over all locations (medical and MDS hubs)
            for j in range(self.num_locations):
                if i == j:                                                  # No route is needed when location A = location B
                    risk_drone_matrix[i, j] = 0
                    risk_drone_matrix[i, j] = 0
                else:
                    # Check if a risk-averse route exists between these hospitals
                    if drone_params["distanceMatrix"][i, j] > 10000000:
                        risk_drone_matrix[i, j] = -1
                    else:
                        # Compute travel time in seconds from route distance
                        risk_drone_matrix[i, j] = round(
                            drone_params["distanceMatrix"][i, j] / drone_speed
                            + take_off_time
                            + landing_time
                        )

                    # Check if a fast route exists between these hospitals
                    if drone_params["directDistanceMatrix"][i, j] > 10000000:
                        fast_drone_matrix[i, j] = -1
                    else:
                        # Compute traveltime in seconds from route distance
                        fast_drone_matrix[i, j] = round(
                            drone_params["directDistanceMatrix"][i, j] / drone_speed
                            + take_off_time
                            + landing_time
                        )
        # Set up dictionary to contain all matrices
        matrices = dict()
        matrices["Distance"] = {}
        matrices["Time"] = {}
        matrices["Risk"] = {}
        matrices["Emission"] = {}

        # convert distance to kilometers
        matrices["Distance"]["safe"] = (
            drone_params["distanceMatrix"].astype(float) / 1000
        )
        matrices["Distance"]["fast"] = (
            drone_params["directDistanceMatrix"].astype(float) / 1000
        )

        matrices["Time"]["safe"] = risk_drone_matrix.astype(float)
        matrices["Time"]["fast"] = fast_drone_matrix.astype(float)
        matrices["Risk"]["safe"] = drone_params["riskMatrix"]
        matrices["Risk"]["fast"] = drone_params["directRiskMatrix"]
        matrices["Emission"]["safe"] = (drone_params["distanceMatrix"] / 1000
                                        * drone_params["emmissionPerKm"]).astype(float)
        matrices["Emission"]["fast"] = (drone_params["directDistanceMatrix"] / 1000 *
                                        drone_params["emmissionPerKm"]).astype(float)

        return matrices

    def create_car_matrices(self, car_params):
        """
        Function that processes and complements the route matrices created in the pre-processing module

        :param car_params: dictionary containing car parameters
        :return: car matrices
        """

        # Get the matrices of the modeled day of week
        original_time_matrices = car_params["timeMatrix"][self.day]
        distance_matrices = car_params["distanceMatrix"][self.day]

        # initialise dictionaries
        risk_matrix_safe = {}
        time_matrix_safe = {}
        risk_matrix_fast = {}
        time_matrix_fast = {}

        # Loop over all hours of the day
        for hour in range(24):
            risk_matrix_safe[hour] = np.zeros_like(distance_matrices[hour], dtype=float)
            time_matrix_safe[hour] = np.zeros_like(distance_matrices[hour])
            risk_matrix_fast[hour] = np.zeros_like(distance_matrices[hour], dtype=float)
            time_matrix_fast[hour] = np.zeros_like(distance_matrices[hour])

            leaving_time = car_params["leavingTime"]
            arrival_time = car_params["arrivalTime"]
            emergency_risk = car_params["emergencyRisk"]                        # injuries/ hour
            normal_risk = car_params["normalRisk"]                              # injuries/km
            speeding_factor = car_params["speedingFactor"]                      # The factor with which travel time is
                                                                                # reduced when using lights and sirens
            for i in range(self.num_locations):
                for j in range(self.num_locations):
                    if i == j:
                        risk_matrix_safe[hour][i, j] = 0
                        time_matrix_safe[hour][i, j] = 0
                        risk_matrix_fast[hour][i, j] = 0
                        time_matrix_fast[hour][i, j] = 0
                        distance_matrices[hour][i, j] = 0
                    else:
                        time = original_time_matrices[hour][i, j]
                        distance = distance_matrices[hour][i, j]
                        fast_time = time / speeding_factor

                        risk_matrix_safe[hour][i, j] = (distance * normal_risk)
                        time_matrix_safe[hour][i, j] = round(time + leaving_time + arrival_time)
                        risk_matrix_fast[hour][i, j] = (fast_time * emergency_risk / (60 * 60))
                        time_matrix_fast[hour][i, j] = round(fast_time + leaving_time + arrival_time)

        # Create dict that will contain all matrices, similar to drones
        matrices = dict()
        matrices["Distance"] = {}
        matrices["Time"] = {}
        matrices["Risk"] = {}
        matrices["Emission"] = {}
        matrices["Distance"]["safe"] = {}
        matrices["Distance"]["fast"] = {}
        matrices["Time"]["safe"] = {}
        matrices["Time"]["fast"] = {}
        matrices["Risk"]["safe"] = {}
        matrices["Risk"]["fast"] = {}
        matrices["Emission"]["safe"] = {}
        matrices["Emission"]["fast"] = {}

        # All matrices are specified for each hour of the day
        for hour in range(24):
            matrices["Distance"]["safe"][hour] = distance_matrices[hour].astype(float)
            matrices["Distance"]["fast"][hour] = distance_matrices[hour].astype(float)
            matrices["Time"]["safe"][hour] = time_matrix_safe[hour].astype(float)
            matrices["Time"]["fast"][hour] = time_matrix_fast[hour].astype(float)
            matrices["Risk"]["safe"][hour] = risk_matrix_safe[hour].astype(float)
            matrices["Risk"]["fast"][hour] = risk_matrix_fast[hour].astype(float)
            matrices["Emission"]["safe"][hour] = (distance_matrices[hour] * car_params["emmissionPerKm"]).astype(float)
            matrices["Emission"]["fast"][hour] = (distance_matrices[hour] * car_params["emmissionPerKm"]).astype(float)

        return matrices

    def create_client_locations(self, client_params, width, height):
        """
        Function that creates the hospital agents and places them in the model

        :param client_params: Client details
        :param width: Model grid width
        :param height: Model height width

        :return:
        """

        # Changes:
        # this part determines self.spawnLocations --> seem to be indexes of locations that should be spawned
        # also determines self.suppliers[useCase]
        # demand is removed here since demand will be defined beforehand

        # Obtain hospital names
        client_names = create_client_names(client_params)

        # Create clients
        for i, client in enumerate(client_params):

            # Place the client on the grid
            position = rowColtoXY(client[0], width, height)
            name = client_names[i]
            requests = self.request_input[self.request_input['origin'] == name]

            client_agent = Client(i, self, position, requests, name)

            self.schedule.add(client_agent)
            self.clients.append(client_agent)
            self.grid.place_agent(client_agent, position)

            if self.num_drones > 0:
                self.fixed_costs += self.drone_infra_costs["landingPlatforms"]

    def determine_spawn_locations(self):
        """
        Function that determines where vehicles should be spawned
        """
        total_vehicles = self.num_drones

        self.spawn_locations = rd.sample(self.clients, total_vehicles)

    def create_drones(self, num_drones, drone_params):
        """
        Function that creates the drone agents and places them in the model

        :param num_drones: Number of drones
        :param drone_params: Drone specifications
        :return:
        """

        # Loop over the total number of drones
        for i in range(num_drones):
            # Determine the spawn location
            spawn_location = self.spawn_locations[i]

            drone = Drone(100 + i, self, drone_params, spawn_location)

            self.schedule.add(drone)
            self.vehicles.append(drone)
            self.grid.place_agent(drone, spawn_location.pos)
            self.fixed_costs += drone_params["costs"]["fixed"]

    def create_cars(self, num_cars, car_params, client_params):
        """
        Function that creates the car agents and places them in the model

        :param num_cars: Number of cars
        :param car_params: Car specifications
        :return:
        """
        # Loop over the total number of cars
        for i in range(num_cars):

            spawn_location = rd.choice(client_params)

            # Create the agent
            car = Car(200 + i, self, car_params, spawn_location)

            self.schedule.add(car)
            self.grid.place_agent(car, spawn_location.pos)
            self.fixed_costs += car_params["costs"]["fixed"]

    def create_client_data_collector(self):
        """
        Creates a datacollector that can keep track of hospital specific performance

        :return: DataCollector object
        """
        table = {}

        for i, client in enumerate(self.clients):
            table[client.name] = []

        return DataCollector(tables={"Open demand": table})

    def step(self):
        """Advance the model by one step"""

        # Check if the day has ended and all orders have been completed
        if len(self.requests) == 0 and self.time > self.max_steps:
            self.compute_model_outputs()
            self.running = False

        self.schedule.step()

        if self.visualization and self.charts:
            self.dc.collect(self)

        self.time += 1

    def compute_model_outputs(self):
        """
        Function that is called at the end of the simulation to compute all desired KPIs

        :return:
        """
        self.fulfilled_demand = len(self.completed_requests)
        self.total_overdue = self.overdue["Drone"] + self.overdue["Car"]
        self.total_costs = (
            self.fixed_costs
            + self.labour_costs
            + self.variable_costs["Drone"]
            + self.variable_costs["Car"]
        )

        # Risk and emissions
        self.total_risk = self.risk["Drone"] + self.risk["Car"]
        self.total_emissions = self.emmissions["Drone"] + self.emmissions["Car"]


        # Number of drone deliveries
        self.drone_fast_deliveries = len(self.deliveries["Drone"]["fast"])
        self.drone_safe_deliveries = len(self.deliveries["Drone"]["safe"])
        self.total_drone_deliveries = self.drone_fast_deliveries + self.drone_safe_deliveries

        # Number of car deliveries
        self.car_fast_deliveries = len(self.deliveries["Car"]["fast"])
        self.car_safe_deliveries = len(self.deliveries["Car"]["safe"])
        self.total_car_deliveries = self.car_fast_deliveries + self.car_safe_deliveries

        # Delivery time
        self.average_delivery_time = self.total_delivery_time / max(self.total_deliveries, 1)
        self.car_fast_delivery_time = sum(self.deliveries["Car"]["fast"]) / max(self.car_fast_deliveries, 1)
        self.car_safe_delivery_time = sum(self.deliveries["Car"]["safe"]) / max(self.car_safe_deliveries, 1)
        self.drone_fast_delivery_time = sum(self.deliveries["Drone"]["fast"]) / max(self.drone_fast_deliveries, 1)
        self.drone_safe_delivery_time = sum(self.deliveries["Drone"]["safe"]) / max(self.drone_safe_deliveries, 1)

        self.drone_delivery_time = (self.drone_fast_delivery_time * self.drone_fast_deliveries
                                + self.drone_safe_delivery_time * self.drone_safe_deliveries) \
                                 / max(self.drone_safe_deliveries + self.drone_fast_deliveries, 1)

        self.car_delivery_time = (self.car_fast_delivery_time * self.car_fast_deliveries
                                + self.car_safe_delivery_time * self.car_safe_deliveries) \
                                 / max(self.car_safe_deliveries + self.car_fast_deliveries, 1)

        self.model_reporters = {
            "Fulfilled demand": self.fulfilled_demand,
            "Car overdue": self.overdue["Car"],
            "Drone overdue": self.overdue["Drone"],
            "Total overdue": self.total_overdue,
            "Drone fast Deliveries": self.drone_fast_deliveries,
            "Drone safe Deliveries": self.drone_safe_deliveries,
            "Total drone deliveries": self.total_drone_deliveries,
            "Car fast Deliveries": self.car_fast_deliveries,
            "Car safe Deliveries": self.car_safe_deliveries,
            "Total Car deliveries": self.total_car_deliveries,
            "Total deliveries": self.total_car_deliveries + self.total_drone_deliveries,
            "Directly performed": self.directly_performed,
            "Average deliverytime": self.average_delivery_time,
            "Average drone delivery time": self.drone_delivery_time,
            "Average drone fast delivery time": self.drone_fast_delivery_time,
            "Average drone safe delivery time": self.drone_safe_delivery_time,
            "Average car delivery time": self.car_delivery_time,
            "Average car fast delivery time": self.car_fast_delivery_time,
            "Average car safe delivery time": self.car_safe_delivery_time,
            "Drone variable cost": self.variable_costs["Drone"],
            "Car variable cost": self.variable_costs["Car"],
            "Fixed configuration cost": self.fixed_costs,
            "Labour costs": self.labour_costs,
            "Drone risk": self.risk["Drone"],
            "Drone emissions": self.emmissions["Drone"],
            "Total costs": self.total_costs,
            "Total risk": self.total_risk,
            "Emissions": self.total_emissions,
            "Fast deliveries": self.fast_deliveries,
            "Medium deliveries": self.medium_deliveries,
            "Late deliveries": self.late_deliveries,
            "Drone Idle time": self.idle_time["Drone"],
            "Drone safe flying empty time": self.empty_time["Drone"]["safe"],
            "Drone fast flying empty time": self.empty_time["Drone"]["fast"],
            "Drone safe flying filled time": self.delivery_time["Drone"]["safe"],
            "Drone fast flying filled time": self.delivery_time["Drone"]["fast"],
            "Car fast driving filled time": self.delivery_time["Car"]["fast"],
            "Num drones": self.num_drones,
            "Repositionings": self.repositionings,
            "Non idle vehicle chosen": self.no_idle_vehicle_chosen,
            "Day of week": self.day,
            "Percentage overdue": self.total_overdue / self.fulfilled_demand,
            "Movement matrix": self.track_movement_matrix,
            "Deliveries matrix": self.track_deliveries_matrix,
        }

    def print_step_state(self):
        """
        Helper function that can be used to evaluate simulation functioning
        :return:
        """

        print(
            "{:<15} {:<5} {:<5} {:<8} {:<8} {:<8} {:<8}".format(
                "Agent", "Ori", "Des", "ETD", "ETA", "Use case", "Orders"
            )
        )
        for item in self.command_center.scheduled_deliveries:
            print(
                "{:<15} {:<5} {:<5} {:<8} {:<8} {:<8} {:<8}".format(
                    item.vehicle.type + " " + str(item.vehicle.unique_id),
                    str(item.origin.matrixIndex),
                    str(item.destination.matrixIndex),
                    str(item.etd),
                    str(item.eta),
                    str(item.useCase),
                    str(len(item.orders)),
                )
            )