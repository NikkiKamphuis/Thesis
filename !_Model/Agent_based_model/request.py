class Request:
    """Class of a request for shipment of medical material"""

    def __init__(self, model, deadline, urgency, client, target, id,
                 mass, volume):

        self.id = id
        self.model = model
        self.parent = client
        self.starting_time = self.model.time
        self.deadline = deadline
        self.target = target
        self.urgency = urgency
        self.parent.open_demand += 1
        self.mass = mass
        self.volume = volume


    def complete_request(self, arrival_time, risk, emmission, cost, delivery_type, delay, vehicle):
        """
        Complete the order and update all model KPIs

        :param arrival_time: time of arrival
        :param risk: risk associated with the request
        :param emmission: emissions associated with the request
        :param cost: costs associated with the request
        :param delivery_type: fast or safe
        :param delay: delay incurred
        :param vehicle: agent
        :return:
        """

        self.delay = delay
        self.parent.open_demand -= 1
        self.complete_time = arrival_time - self.starting_time
        self.margin = self.deadline - self.model.time

        self.delivery_type = delivery_type

        if self.model.time > self.deadline:
            self.overdue = True
            self.model.overdue[vehicle.type] += 1

        elif self.delivery_type != 'No delivery needed':
            self.overdue = False

        #############################################################
        # Concept of speed of delivery is not correct, but is interesting
        #
        # if self.speedOfDelivery < 33.3:
        #     self.model.fastDeliveries += 1
        #
        # elif 33.3 <= self.speedOfDelivery and  self.speedOfDelivery < 66.6:
        #     self.model.mediumDeliveries +=1
        #
        # elif 66.6 <= self.speedOfDelivery and self.speedOfDelivery <= 100:
        #     self.model.lateDeliveries += 1
        #############################################################

        self.parent.fulfilled_demands.append(self.margin)

        if self.delivery_type == 'No delivery needed':
            self.model.directly_performed += 1

        else:
            self.model.deliveries[vehicle.type][self.delivery_type].append(self.complete_time)
            self.model.total_delivery_time += self.complete_time
            self.model.total_deliveries += 1

        self.model.completed_requests.append(self)
        self.model.requests.remove(self)
        
 