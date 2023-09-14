from Local_Mesa.Visualisation.modules import (
                                        CanvasGrid,
                                        ChartModule,
                                        PieChartModule,
                                        BarChartModule
                                        )
from mesa.visualization.modules import TextElement
from Local_Mesa.Visualisation.UserParam import UserSettableParameter
from agent_portrayal import agent_portrayal
import sys
import os
import random as rd

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from helper_functions import time_tick_to_string


class CustomTimeElement(TextElement):
    """
    Dashboard element displaying the time
    """
    def render(self, model):
        """
        Creates a render of the time display

        :param model: Agent-based model
        :return:
        """
        day = model.day
        time = time_tick_to_string(model.time)
        return "<font size='+1'>{} {}</font>".format(day, time)


class CustomHospitalOverview(TextElement):
    """Dashboard element displaying the hospitals"""

    def render(self, model):
        """
        Creates a render of the time display

        :param model: Agent-based model
        :return:
        """
        viz = ""
        for client in model.clients:
            viz += str(client.matrix_index)
            viz += ": "
            viz += client.name
            viz += "<br>"
        return viz


class CustomModelStateOverview(TextElement):
    """
    Dashboard element displaying current KPI levels
    """

    def render(self, model):
        """
        Creates a render of dashboard element displaying current KPI levels

        :param model: Agent-based model
        :return:
        """
        viz = "Labour costs: €" + "{:,}".format(model.labour_costs) + " per year <br>"
        viz += "Fixed costs: €" + "{:,}".format(model.fixed_costs) + " per year <br>"
        viz += (
            "Variable costs: €"
            + "{:.2f}".format(model.variable_costs["Drone"] + model.variable_costs["Car"])
            + "<br>"
        )
        viz += "Open orders: " + str(len(model.requests)) + "<br>"
        viz += "Completed orders: " + str(len(model.completed_requests)) + "<br>"
        viz += (
            "Average delivery time: "
            + "{:.2f}".format(model.total_delivery_time / max(model.total_deliveries, 1))
            + " min <br>"
        )
        viz += (
            "Emissions: "
            + "{:.2f}".format(model.emmissions["Drone"] + model.emmissions["Car"])
            + " kg co2<br>"
        )
        viz += (
            "Risk: "
            + "{:.2f}".format(1000 * (model.risk["Drone"] + model.risk["Car"]))
            + "*10^-3 expected injuries<br>"
        )
        return viz


def initialise_dashboard(grid, charts):
    """
    Defines all elements that should be used within the dashboard

    :param grid: Grid specifications
    :param charts: Boolean that indicates whether charts should be displayed
    :return: list of elements of dashboard
    """

    width, height = grid.shape
    canvas = CanvasGrid(agent_portrayal, width, height, width * 1.7, height * 1.7)
    # List that will contain all elements of the dashboard
    elements = [canvas]
    elements.append(CustomTimeElement())
    elements.append(CustomModelStateOverview())
    elements.append(CustomHospitalOverview())

    # Add additional charts to the dashboard if needed
    if charts:
        demand_chart = ChartModule(
            [
                {"Label": "Unfulfilled demand", "Color": "Yellow"},
                {"Label": "Late Unfulfilled demand", "Color": "Red"},
                {"Label": "Fulfilled demand", "Color": "Black"},
            ],
            data_collector_name="dc",
            canvas_height=100,
            canvas_width=250,
        )

        elements.append(demand_chart)

        pie_chart = PieChartModule(
            [
                {"Label": "Drones", "Color": "Red"},
                {"Label": "Emergency", "Color": "Blue"},
                {"Label": "Normal rides", "Color": "Green"},
                {"Label": "Directly performed", "Color": "Yellow"},
            ],
            data_collector_name="dc",
            canvas_height=250,
            canvas_width=250,
        )

        elements.append(pie_chart)

        bar_chart = BarChartModule(
            [
                {"Label": "Directly performed", "Color": "Grey"},
                {"Label": "Fast deliveries", "Color": "Green"},
                {"Label": "Medium deliveries", "Color": "Yellow"},
                {"Label": "Late deliveries", "Color": "Orange"},
                {"Label": "Overdue", "Color": "Red"},
            ],
            data_collector_name="dc",
            canvas_height=200,
            canvas_width=400,
        )

        elements.append(bar_chart)

        delivery_time = ChartModule(
            [
                {"Label": "Delivery time", "Color": "Yellow"},
            ],
            data_collector_name="dc",
            canvas_height=100,
            canvas_width=250,
        )

        elements.append(delivery_time)

    return  elements

def dashboard_inputs(random_seed):

    """
    Creates all the sliders within the visualisation
    :return:
    """

    num_drones = UserSettableParameter("slider", "Drones", 3, 0, 10, 1)
    delivery_mode = UserSettableParameter(
        "choice", "Delivery mode", value="combi", choices=["fast", "safe", "combi"]
    )
    repositioning = UserSettableParameter(
        "choice",
        "Repositioning strategy",
        value="closest hub",
        choices=[
            "none",
            "simple",
            "closest hub",
            "forced",
        ],
    )
    day_of_week = UserSettableParameter(
        "choice",
        "Day of the week",
        value="Random",
        choices=[
            "Random",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ],
    )

    if random_seed:
        seed = rd.randint(0, 100)
    else:
        seed = 57

    return num_drones, delivery_mode, repositioning, day_of_week, seed
