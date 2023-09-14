"""
Created on Fri 4 August 2023

@author: Nikki Kamphuis
"""
import sys
import os

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from client import Client
from drone import Drone
from car import Car
from helper_functions import errorMessage

def agent_portrayal(agent):
    """
    Defines portrayal of an agent in the visualisation

    :param agent:
    :return:
    """
    portrayal = {}
    
    if type(agent) is Drone:

        if agent.status == "Idle":
            portrayal["Shape"] = "drone_empty_safe"

        elif agent.status == "Flying" or agent.status == 'delayed':

            if agent.empty:

                if agent.mode == 'fast':
                    portrayal["Shape"] = "drone_empty_fast"

                else:
                    portrayal["Shape"] = "drone_empty_safe"

            else:

                if agent.mode == 'fast':
                    portrayal["Shape"] = "drone_filled_fast"

                else:
                    portrayal["Shape"] = "drone_filled_safe"  
        else:
            errorMessage("Drone Portrayal satus")

        portrayal["Layer"] = 1
        portrayal["scale"] = 20

    elif type(agent) is Car:

        if agent.status == "Idle":
            portrayal["Shape"] = "car_empty_safe"

        elif agent.status == "Driving" or agent.status == 'delayed':

            if agent.empty:

                if agent.mode == 'fast':
                    portrayal["Shape"] = "car_empty_fast"

                else:
                    portrayal["Shape"] = "car_empty_safe"

            else:
                if agent.mode == 'fast':
                    portrayal["Shape"] = "car_filled_fast"

                else:
                    portrayal["Shape"] = "car_filled_safe"  
        else:
            print(agent.status)
            errorMessage("Car Portrayal satus")

        portrayal["Layer"] = 1
        portrayal["scale"] = 20

    elif type(agent) is Client:
        colors = []

        if agent.open_demand > 0:
            colors.append("Red")

        else:
            colors.append('White')

        while len(colors) < 3: 
            colors.append("Grey")

        portrayal["Shape"] = colors 
        portrayal["Layer"] = 2
        portrayal["w"] = 18
        portrayal["h"] = 8
        portrayal["matrixIndex"] = str(agent.matrix_index)

    return portrayal
