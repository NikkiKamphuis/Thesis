"""
Created on Mon July 2023

@author: Nikki Kamphuis
"""
from Local_Mesa import Agent
from schedule import ScheduleItem
from auction import Bid
import numpy as np
from helper_functions import errorMessage


class Drone(Agent):
    "Agent representing a drone"

    def __init__(self, unique_id, model, drone_params, origin_hub):

        super().__init__(unique_id, model)

        self.matrices = self.model.matrices["Drone"]
        self.mode = "safe"
        self.speed = drone_params["speed"] / 3.6  # km/h to m/s
        self.origin_hub = origin_hub
        self.location = origin_hub
        self.pos = self.location.pos
        self.schedule = []
        self.type = "Drone"
        self.emmission = drone_params["emmissionPerKm"]
        self.take_off_time = drone_params["takeOffTime"]
        self.landing_time = drone_params["landTime"]
        self.TAT = drone_params["TAT"]  # in seconds
        self.delay_percentages = drone_params["delayPercentages"]
        self.cost_per_km = drone_params["costs"]["perKm"]  # € per km
        self.status = "Idle"
        self.status_since = 0
        self.empty = True
        self.eta = None
        self.last_departure_location = None
        self.travel_variance = 0.1
        self.capacity = drone_params["capacity"]
        self.current_end_location = self.location
        self.next_time_available = 0

    def determine_flight_details(self, origin, destination, mode):
        """
        Functions that extracts the KPIs of a flight between origin and destination
        :param origin: Origin of planned flight
        :param destination: Destination of flight
        :param mode: Safe or fast (which route matrices should be used)
        :return: Dict containing distance, time, risk, emission, cost, type
        """

        # Check first whether flight is possible
        if self.matrices["Time"][mode][origin.matrix_index, destination.matrix_index] == -1:

            return False
        else:

            distance = self.matrices["Distance"][mode][origin.matrix_index, destination.matrix_index]
            time = round(self.matrices["Time"][mode][origin.matrix_index, destination.matrix_index] / 60)
            risk = self.matrices["Risk"][mode][origin.matrix_index, destination.matrix_index]
            emmission = self.matrices["Emission"][mode][origin.matrix_index, destination.matrix_index]
            cost = distance * self.cost_per_km

            # Why is this adjusted?
            if time == 0:
                time = 1

            return {
                "distance": distance,
                "time": time,
                "risk": risk,
                "emmission": emmission,
                "cost": cost,
                "type": mode,
            }

    def create_bid(self, origin, destination, request):
        """
        Create a bid between origin and destination for a specific request

        :param origin: Origin of request
        :param destination: Destination of request
        :param request: Request object
        :return: Best bid value
        """
        # If a schedule already exists, continue from where the current schedule ends
        if len(self.schedule) > 0:

            dep_time = self.schedule[-1].eta + round(self.TAT / 60)
            dep_loc = self.schedule[-1].destination

        # If it is idle its bid can start from current time and location
        else:

            dep_time = self.model.time + round(self.TAT / 60)
            dep_loc = self.location

        # List that will contain all possible bids
        bids = []

        # Create bids for all considered delivery modes: safe,fast or both
        for mode in self.model.considered_delivery_modes:

            bid_dep_time = dep_time

            # Determine KPIs of delivery flight
            flight_to_destination_details = self.determine_flight_details(origin, destination, mode)

            # Only consider a bid when a flight is possible
            if flight_to_destination_details != False:

                # List that will contain all schedule items that together compromise the bid
                schedule_items = []

                # Bid KPIs
                cost, emmissions, risk, eta = 0, 0, 0, 0

                bid_possible = True

                # Flight to pickup point is needed. Get the flight KPIs and update bid values
                # accordingly and add schedule_item to bid
                if origin != dep_loc:

                    flight_to_origin_details = self.determine_flight_details(dep_loc, origin, mode)

                    if flight_to_origin_details != False:

                        flight_to_origin = ScheduleItem(self.model, dep_loc, origin, bid_dep_time,
                                                                bid_dep_time + flight_to_origin_details["time"],
                                                                flight_to_origin_details, self, None)

                        bid_dep_time += flight_to_origin_details["time"] + round(self.TAT / 60)
                        cost += flight_to_origin_details["cost"]
                        emmissions += flight_to_origin_details["emmission"]
                        risk += flight_to_origin_details["risk"]
                        schedule_items.append(flight_to_origin)

                    else:
                        # Can't get to the pick up location
                        bid_possible = False

                # Get the delivery flight KPIs and update bid values accordingly and add scheduleItem to bid
                flight_to_destination = ScheduleItem(self.model, origin, destination, bid_dep_time,
                                                                bid_dep_time + flight_to_destination_details["time"],
                                                                flight_to_destination_details, self, request)

                eta = bid_dep_time + flight_to_destination_details["time"]
                bid_dep_time += flight_to_destination_details["time"] + round(self.TAT / 60)
                emmissions += flight_to_destination_details["emmission"]
                risk += flight_to_destination_details["risk"]
                cost += flight_to_destination_details["cost"]

                schedule_items.append(flight_to_destination)

                # Create the total bid and add it to the list
                if bid_possible:
                    bid = Bid(self.model, eta, emmissions, cost, risk, schedule_items,
                                        mode, self, request)

                    bids.append(bid)

        # If bids are possible, sort the bids and return the best bid to the command center
        if len(bids) > 0:
            bids.sort()
            return bids[0]
        else:
            return False

    def step(self):
        """
        Each step the agents checks its current status and if something needs to happen

        :return:
        """

        if len(self.schedule) > 0:

            self.next_time_available = self.schedule[-1].eta
            self.current_end_location = self.schedule[-1].destination

            if self.status == "Idle":

                # The departure of the next flight
                if self.model.time == self.schedule[0].etd:
                    self.depart()

            elif self.status == "Delayed":

                if self.model.time == self.eta:
                    self.arrive()

            # The drone is in the air
            else:
                if self.eta == self.model.time:

                    # Potentially add delay if this is considered in the model
                    if self.model.delays:
                        flight = self.schedule[0]
                        delay = flight.travel_delay(self.delay_percentages)

                        if delay == 0:
                            self.arrive()

                        elif delay < 0:
                            self.arrive()

                        # readjust the rest of the schedule
                        else:
                            self.eta = flight.eta + delay
                            self.delay_schedule(delay)
                            self.status = "Delayed"
                            self.status_since = self.model.time
                    else:
                        self.arrive()
                else:
                    self.update_position()
        else:

            if self.status != "Idle":
                errorMessage("Drone has no schedule but is has {} status".format(self.status))

        self.update_model_variables()

    def arrive(self):
        """
        Function that is activated at the end of a flight

        :return:
        """
        flight = self.schedule.pop(0)

        self.location = flight.destination
        self.model.grid.move_agent(self, self.location.pos)
        self.status = "Idle"
        self.empty = True

        # If it arrived earlier then planned it is actually already idle
        self.status_since = flight.eta
        flight.complete()
        self.eta = None

        ############################################################
        # ! Originally a part on repositioning followed here, however this has been removed for now
        ############################################################

    def depart(self):
        """
        Function that is activated at the start of a flight

        :return:
        """
        flight = self.schedule[0]

        self.mode = flight.delivery_type
        self.eta = flight.eta
        self.status = "Flying"
        self.status_since = self.model.time

        # Only update the last departure location if it was no repositioning flight
        self.last_departure_location = flight.origin

    def update_position(self):
        """
        Update the position of a drone during flight
        => Computes new x and y

        :return:
        """
        flight = self.schedule[0]
        flight_progress = (self.model.time - flight.etd) / flight.duration

        x_pos_origin, y_pos_origin = flight.origin.pos
        x_pos_destination, y_pos_destination = flight.destination.pos

        x = round(x_pos_origin + (x_pos_destination - x_pos_origin) * flight_progress)
        y = round(y_pos_origin + (y_pos_destination - y_pos_origin) * flight_progress)

        self.model.grid.move_agent(self, (x, y))

    def delay_schedule(self, delay):
        """
        Function that delays all flights in the schedule if delay is propogated

        :param delay: delay in time
        :return:
        """

        propagating_delay = delay
        i = 0

        while propagating_delay > 0:
            flight = self.schedule[i]
            new_eta = flight.delay_schedule_item(propagating_delay)
            new_first_departure_time = new_eta + round(self.TAT / 60)

            if i == len(self.schedule) - 1:
                propagating_delay = 0

            else:
                i += 1
                propagating_delay = new_first_departure_time - self.schedule[i].etd

                if i > len(self.schedule) + 1:
                    errorMessage("Infinite while loop in drone.py, delay_schedule()")

    def update_model_variables(self):
        """
        Update the model KPIs

        :return:
        """
        if self.status == "Idle":
            self.model.idle_time[self.type] += 1

        elif self.status == "Delayed":
            self.model.delay_time[self.type] += 1

        elif self.status == "Flying":

            if self.empty:
                self.model.empty_time[self.type][self.mode] += 1

            else:
                self.model.delivery_time[self.type][self.mode] += 1

        else:
            errorMessage("Drone status error")


