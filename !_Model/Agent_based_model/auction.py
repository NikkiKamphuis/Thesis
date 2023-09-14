"""
Created on Tue August 1 2023

@author: Nikki Kamphuis
"""


class Bid:
    """Class of bid, containing all relevant bid KPIs and information"""

    def __init__(self, model, eta, emissions, cost, risk, schedule_items, mode, vehicle, order):

        self.eta = eta
        self.model = model
        self.delivery_mode = model.delivery_mode
        self.schedule_items = schedule_items
        self.mode = mode
        self.vehicle = vehicle
        self.delivery_time = eta - self.vehicle.model.time
        self.order = order
        self.emissions = emissions
        self.cost = cost
        self.risk = risk
        self.decision_weights = model.decision_weights

        # Compute the score of a bid used to compare different bids
        self.score = self.determine_score()

    def determine_score(self):
        """
        Compute the score of a bid based on the decision weights

        Method by Jelle van Haasteren

        :return: score
        """
        score = 0

        # Why multiply by 1000000?
        weighted_risk = self.risk * self.decision_weights["risk"] * 1000000
        weighted_emissions = self.emissions * self.decision_weights["emmissions"]
        weighted_delivery_time = self.delivery_time * self.decision_weights["deliveryTime"]
        weighted_costs = self.cost * self.decision_weights["cost"]

        if self.eta > self.order.deadline:
            # Orders coming in too late are always discouraged
            score += 10000000

        if self.delivery_mode == "safe":
            # In safe modus only TPR levels are compared
            score += self.risk

        elif self.delivery_mode == "fast":
            # In fast modus only delivery times are compared
            score += self.delivery_time

        elif self.delivery_mode == "combi":
            # In combi modus multiple KPIs can be weighed into the score
            score += weighted_risk
            score += weighted_emissions
            score += weighted_delivery_time
            score += weighted_costs

        return score

    def __lt__(self, other):
        """
        Function that compares the quality of 2 bids in order to sort later

        :param other: other bid
        :return:
        """
        return self.score < other.score
