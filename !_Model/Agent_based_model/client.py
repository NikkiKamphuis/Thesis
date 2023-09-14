"""
Created on Thu Jul 27 2023

@author: Nikki Kamphuis
"""
from Local_Mesa import Agent
from request import Request

class Client(Agent):
    """Agent representing a client of Medical Drone Service"""

    def __init__(self, unique_id, model, location, requests, name):
        super().__init__(unique_id, model)
        self.type = "Client"
        self.name = name
        self.matrix_index = unique_id

        self.open_demand = 0
        self.fulfilled_demands = []

        # Difference ??
        self.demand_schedule = requests

        self.pos = location


    def step(self):
        """
        Defines what happens each step of the model.

        Here: client checks its demand schedule and creates an order if needed.
        :return:
        """

        if self.model.time < self.model.max_steps:

            if self.model.time in list(self.demand_schedule.index):

                request = self.demand_schedule.loc[self.model.time]

                # For a single request
                if request.__class__.__name__ == 'Series':
                    # Retrieve order specifications
                    target = request['destination']
                    target = next((client for client in self.model.clients if client.name == target), None)
                    deadline_type = request['type']
                    deadline = request['deadline']
                    mass = request['mass']
                    volume = request['volume']
                    id = 5000 + request['id']

                    # model, deadline, urgency, hospital, id
                    request = Request(self.model, deadline, deadline_type, self, target, id, mass, volume)
                    self.model.requests.append(request)
                    self.model.request_counter += 1

                    self.model.command_center.new_demand(request)

                # For multiple requests at the same time
                else:
                    for index, row in request.iterrows():
                        # Retrieve order specifications
                        target = row['destination']
                        target = next((client for client in self.model.clients if client.name == target), None)
                        deadline_type = row['type']
                        deadline = row['deadline']
                        mass = row['mass']
                        volume = row['volume']
                        id = row['id']

                        # model, deadline, urgency, hospital, id
                        request = Request(self.model, deadline, deadline_type, self, target, id, mass, volume)
                        self.model.requests.append(request)
                        self.model.request_counter += 1

                        self.model.command_center.new_demand(request)




