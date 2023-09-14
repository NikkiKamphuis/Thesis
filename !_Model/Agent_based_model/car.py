"""
Created on Thu 3 August 2023

@author: jelle
"""
from Local_Mesa import Agent
from schedule import ScheduleItem
from auction import Bid
from helper_functions import errorMessage, time_tick_to_hour

class Car(Agent):
    """Agent representing a car or other road vehicle"""

    def __init__(self, unique_id, model, car_params, origin_hub):

        super().__init__(unique_id, model)

        self.matrices = self.model.matrices["Car"]
        self.schedule = []
        self.location = origin_hub
        self.origin_hub = origin_hub
        self.pos = self.location.pos
        self.type = model.agent_types[1]
        self.leaving_time = car_params["leavingTime"]
        self.arrival_time = car_params["arrivalTime"]
        self.TAT = car_params["TAT"]
        self.delay_percentages = car_params["delayPercentages"]
        self.emmission = car_params["emmissionPerKm"]  # kilogram Co2 per km
        self.mode = "safe"
        self.cost_per_km = car_params["costs"]["perKm"]
        self.status = "Idle"
        self.empty = True
        self.status_since = 0
        self.last_departure_location = None
        self.eta = None
        self.travel_variance = 0.2
        self.capacity = car_params["capacity"]
        self.current_end_location = self.location
        self.next_time_available = 0

    def determine_ride_details(self, origin, destination, mode, dep_time):
        """
        Functions that extracts the KPIs of the ride between origin and destination

        :param origin: Start of the ride
        :param destination: Destination of the ride
        :param mode: Fast of safe
        :param dep_time: Departure time
        :return: Dict containing distance, time, risk, emission, cost, mode
        """

        hour = time_tick_to_hour(dep_time)

        distance = self.matrices["Distance"][mode][hour][origin.matrix_index, destination.matrix_index]
        emmission = self.matrices["Emission"][mode][hour][origin.matrix_index, destination.matrix_index]

        time = round(self.matrices["Time"][mode][hour][origin.matrix_index, destination.matrix_index] / 60)
        risk = self.matrices["Risk"][mode][hour][origin.matrix_index, destination.matrix_index]
        cost = distance * self.cost_per_km

        return {
            "distance": distance,
            "time": time,
            "risk": risk,
            "emmission": emmission,
            "cost": cost,
            "type": mode
        }


    def create_bid(self, origin, destination, request):
        """
        Create a bid between origin and destination for a specific request

        :param origin:
        :param destination:
        :param order:
        :return:
        """

        # if already a schedule continue from where the current schedule ends
        if len(self.schedule) > 0:
            dep_time = self.schedule[-1].eta + round(self.TAT / 60)
            dep_loc = self.schedule[-1].destination

        # If it is idle its bid can start from current time and location
        else:
            dep_time = self.model.time + round(self.TAT / 60)
            dep_loc = self.location
        bids = []  # List that will contain all possible bids


        # Create bids for all considered deliverymodes: safe,fast or both
        for mode in self.model.considered_delivery_modes:
            bid_dep_time = dep_time

            # List that will contain all schedule items that together comprimise the bid
            schedule_items = []

            # Bid KPIs
            cost, emmissions, risk, eta = 0, 0, 0, 0

            # Ride to pickup point is needed. Get the ride KPIs and update bid values accordingly
            # and add scheduleItem to bid
            if origin != dep_loc:
                ride_to_origin_details = self.determine_ride_details(dep_loc, origin, mode, bid_dep_time)
                ride_to_origin = ScheduleItem(self.model, dep_loc, origin, bid_dep_time,
                                                bid_dep_time + ride_to_origin_details["time"],
                                                ride_to_origin_details, self, None)

                bid_dep_time += ride_to_origin_details["time"] + round(self.TAT / 60)
                cost += ride_to_origin_details["cost"]
                emmissions += ride_to_origin_details["emmission"]
                risk += ride_to_origin_details["risk"]
                schedule_items.append(ride_to_origin)

            # Get the delivery ride KPIs and update bid values accordingly and add scheduleItem to bid
            ride_to_destination_details = self.determine_ride_details(origin, destination, mode, bid_dep_time)

            ride_to_destination = ScheduleItem(self.model, origin, destination, bid_dep_time,
                                                bid_dep_time + ride_to_destination_details["time"],
                                                ride_to_destination_details, self, request)

            eta = bid_dep_time + ride_to_destination_details["time"]
            bid_dep_time += ride_to_destination_details["time"] + round(self.TAT / 60)
            emmissions += ride_to_destination_details["emmission"]
            risk += ride_to_destination_details["risk"]
            cost += ride_to_destination_details["cost"]
            schedule_items.append(ride_to_destination)

            # Create the total bid and add it to the list
            bid = Bid(self.model, eta, emmissions, cost, risk, schedule_items, mode, self, request)
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

                # The departure of the next ride
                if self.model.time == self.schedule[0].etd:
                    self.depart()

            elif self.status == "delayed":

                if self.model.time == self.eta:
                    self.arrive()

            # The car is en route
            else:
                if self.eta == self.model.time:

                    # Potentially add delay if this is considered in the model
                    if self.model.delays:
                        ride = self.schedule[0]
                        delay = ride.travel_delay(self.delay_percentages)

                        if delay == 0:
                            self.arrive()

                        elif delay < 0:
                            self.arrive()

                        # Readjust the rest of the schedule
                        else:
                            self.eta = ride.eta + delay
                            self.delay_schedule(delay)
                            self.status = "delayed"
                            self.status_since = self.model.time
                    else:
                        self.arrive()
                else:
                    self.update_position()
        else:
            if self.status != "Idle":
                errorMessage( "Car has no schedule but is has {} status".format(self.status))

        self.update_model_variables()

    def arrive(self):
        """
        Function that is activated at the end of a ride

        :return:
        """
        ride = self.schedule.pop(0)
        self.location = ride.destination
        self.model.grid.move_agent(self, self.location.pos)
        self.status = "Idle"
        # If it arrived earlier than planned it is actually already idle
        self.status_since = ride.eta
        self.eta = None
        ride.complete()
        self.empty = True

    def depart(self):
        """
        Function that is activated at the start of a ride
        :return:
        """
        ride = self.schedule[0]
        self.mode = ride.delivery_type
        self.eta = ride.eta
        self.status = "Driving"
        self.status_since = self.model.time

        if len(ride.orders) > 0:
            self.empty = False
            self.last_departure_location = ride.origin

        else:
            self.empty = True

    def update_position(self):
        """
        Update the position of the car during the ride

        :return: Move agent
        """
        ride = self.schedule[0]
        ride_progress = (self.model.time - ride.etd) / ride.duration

        x_pos_origin, y_pos_origin = ride.origin.pos
        x_pos_destination, y_pos_destination = ride.destination.pos

        x = round(x_pos_origin + (x_pos_destination - x_pos_origin) * ride_progress)
        y = round(y_pos_origin + (y_pos_destination - y_pos_origin) * ride_progress)

        self.model.grid.move_agent(self, (x, y))

    def delay_schedule(self, delay):  #
        """
        Function that delays all ride in the schedule if delay is propagated

        :param delay: Delay in time
        :return:
        """
        propagating_delay = delay
        i = 0
        while propagating_delay > 0:
            ride = self.schedule[i]
            new_eta = ride.delayScheduleItem(propagating_delay)
            new_first_departure_time = new_eta + round(self.TAT / 60)

            if i == len(self.schedule) - 1:
                propagating_delay = 0

            else:
                i += 1
                propagating_delay = new_first_departure_time - self.schedule[i].etd

    def update_model_variables(self):
        """
        Update the model KPIs

        :return:
        """
        if self.status == "Idle":
            self.model.idle_time[self.type] += 1

        elif self.status == "delayed":
            self.model.delay_time[self.type] += 1

        elif self.status == "Driving":

            if self.empty:
                self.model.empty_time[self.type][self.mode] += 1

            else:
                self.model.delivery_time[self.type][self.mode] += 1
        else:
            print(f"Status {self.status}")
            errorMessage("Car status error")

