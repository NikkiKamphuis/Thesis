"""
Created on Thu 3 August 2023

@author: Nikki Kamphuis
"""
from Local_Mesa import Agent
import numpy as np
from helper_functions import errorMessage


class CommandCenter(Agent):
    """Agent representing the command center"""

    def __init__(self, unique_id, model, car_params, drone_params):

        super().__init__(unique_id, model)


        self.time_matrices = {"Car": self.model.matrices["Car"]["Time"]["fast"][0],
                             "Drone": self.model.matrices["Drone"]["Time"]["fast"]}

        self.TATs = {"Car": round(car_params["TAT"] / 60),
                     "Drone": round(drone_params["TAT"] / 60)}

        self.scheduled_deliveries = []
        self.supply_overview = []

        # dict of arrays stating the time it takes to supply hospital 1 [first index] from hospital 2 [second index]
        self.travel_times = ( {} )

        for type in model.agent_types:

            self.travel_times[type] = np.zeros((self.model.num_locations, self.model.num_locations))

            # If no other lead times are found assume that it takes two hours to get within range
            self.travel_times[type][:] = 120

        self.compute_costs()

    def new_demand(self, request):

        """
        Receive a request for delivery from a hospital

        :param request: Request to ship medical material from location A to location B
        :return:
        """
        origin = request.parent
        destination = request.target

        # Check if the new demand can be added to already planned (delivery) rides
        if self.assign_to_existing_schedule(request, origin, destination) == False:
            # Create a new task allocation auction
            self.auction(origin, destination, request)

    def compute_costs(self):
        """
        Compute the costs of the delivery system

        :return:
        """
        # Only add cost of command center if drones are used
        if self.model.num_drones > 0:

            self.model.fixed_costs += self.model.drone_infra_costs["missionControl"]

            if self.model.labour_cost_params["drones_per_min_pilot_FTE"] < self.model.num_drones:
                errorMessage("Not enough pilots to handle all drones")
            else:
                pilot_costs = self.model.labour_cost_params["min_pilot_FTE_fulltime"] * \
                             self.model.labour_cost_params["pilot_FTE"]

            self.model.labour_costs += pilot_costs


    def assign_to_existing_schedule(self, request, origin, destination):
        """
        Sees whether it is possible to assign a request to an existing ride

        :param request: Object representing a request to ship medical material
        :param origin: Origin of the request
        :param destination: Destination of the request

        :return: Assigned: Whether the request has been assigned to an existing ride
        """

        assigned = False

        # Check if the order can be added to current schedule items
        for item in self.scheduled_deliveries:
            if (
                item.eta > self.model.time
                and item.eta < request.deadline
                and item.origin == origin
                and item.destination == destination
                and assigned == False
            ):
                # Check if the timing and route matches
                # Check if additional capacity is present so deliveries can be combined
                if item.vehicle.capacity > len(item.requests):
                    item.requests.append(request)
                    assigned = True
                    request.assignedVehicle = item.vehicle

        # Return true if the order is succesfully assigned to an already existing schedule item
        return assigned

    def auction(self, origin, destination, request):
        """
        Function that creates a new task allocation auction

        :param origin: Origin of the request
        :param destination: Destination of the request
        :param request: Request object
        :return:
        """
        # List that will contain all incoming bids
        bids = []

        # Boolean that helps analyse if an idle vehicle is picked when one is available
        idle_vehicles = False

        # Let all vehicles make a bid and add to list if possible
        for vehicle in self.model.vehicles:

            if vehicle.status == "Idle":
                idle_vehicles = True

            bid = vehicle.create_bid(origin, destination, request)

            if bid != False:
                bids.append(bid)

        # Order the bids
        bids.sort()

        # No vehicle can perform the delivery
        if len(bids) == 0:
            self.model.no_delivery_possible.append(request)
            self.model.demands.remove(request)
            request.parent.openDemand -= 1

        # Pick the winning bid
        else:
            best_bid = bids[0]
            request.assigned_vehicle = best_bid.vehicle

            if best_bid.vehicle.status != "Idle" and idle_vehicles:
                self.model.no_idle_vehicle_chosen += 1

            for item in best_bid.schedule_items:
                self.scheduled_deliveries.append(item)

                best_bid.vehicle.schedule.append(item)
                best_bid.vehicle.nextTimeAvailable = item.eta
                best_bid.vehicle.currentEndLocation = item.destination

    def step(self):
        self.scheduled_deliveries.sort(key=lambda x: x.etd)

