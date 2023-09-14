import random as rd

class ScheduleItem:

    """Class that represent an item within a vehicle schedule"""

    def __init__(self, model, origin, destination, etd, eta, details, vehicle, request):

        self.model = model
        self.vehicle = vehicle
        self.origin = origin
        self.destination = destination
        self.etd = etd                                  # estimated time of departure
        self.eta = eta                                  # estimated time of arrival
        self.risk = details['risk']
        self.distance = details['distance']
        self.emmission = details['emmission']
        self.cost = details['cost']
        self.delivery_type = details['type']
        self.duration = self.eta - self.etd
        self.delay = 0
        self.total_delay = 0

        if request == None:

            self.requests = []

        else:

            self.requests = [request]

        rd.seed(self.model.seed)
        
    def complete(self):
        """
        Function that processes the completion of a schedule item

        :return:
        """

        # Update model KPIs
        self.model.risk[self.vehicle.type] += self.risk
        self.model.emmissions[self.vehicle.type] += self.emmission
        self.model.variable_costs[self.vehicle.type] += self.cost

        if self.model.track_heatmap:
            self.model.track_movement_matrix[self.origin.matrix_index, self.destination.matrix_index] += 1

        n = len(self.requests)

        if n > 0:

            if self.model.track_heatmap:
                self.model.track_deliveries_matrix[self.origin.matrix_index, self.destination.matrix_index] += n

            if self.vehicle.type == 'Car':

                if n < 4:
                    self.model.car_combination_deliveries[n] += 1

                else:
                    self.model.car_combination_deliveries['more'] += 1

            risk = self.risk / n
            emmission = self.emmission / n
            cost = self.cost / n

            for request in self.requests:
                request.complete_request(self.eta, risk, emmission, cost, self.delivery_type,
                                            self.total_delay, self.vehicle)

    def travel_delay(self, delay_percentages):
        """
        Applies randomness to flight time

        :param delay_percentages: percentage by which a flight time can vary
        :return: incurred delay
        """

        mean = self.duration

        if self.model.currently_rush_hour:
            var = delay_percentages['rushHour'] * mean

        else:
            var = delay_percentages['normalTraffic'] * mean

        actual_travel_time = round(rd.uniform(mean - var, mean + var))

        delay = actual_travel_time - self.duration

        self.delay += delay 
        self.eta = self.etd + actual_travel_time
        
        return delay

    def delay_schedule_item(self, delay):
        """
        Delays a schedule item

        :param delay: Delay in time
        :return: New eta
        """
        self.etd += delay
        self.eta += delay
        self.total_delay += delay

        return self.eta 
  
 
 

 
