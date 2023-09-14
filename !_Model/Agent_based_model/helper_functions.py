"""
Created on Tue Jul 25 2023

@author: Nikki Kamphuis
"""

import sys
import math

def compute_open_requests(model):
    """
    Compute how many orders are open at that time

    :param model: agent-based model class
    :return: number of orders
    """
    open_requests = len(model.requests)

    return open_requests

def compute_late_open_requests(model):
    """
    Compute the amount of open orders currently beyond its deadline

    :param model: agent-based model class
    :return: number of late orders
    """

    open_late_requests = 0
    for request in model.requests:
        if request.deadline < model.time:
            open_late_requests += 1
    return open_late_requests


def compute_average_delivery_time(model):
    """
    Compute average time used to complete a delivery

    :param model: agent-based model class
    :return: average time in minutes
    """
    return model.total_delivery_time / max(model.total_deliveries, 1)


def create_client_names(client_input):  # Create a list containing the names of the hospitals
    """
    Create a list containing the names of the hospitals

    :param client_input: input containing all client data
    :return: list of names
    """

    name_list = []
    for i, hospital in enumerate(client_input):
        name_list.append(hospital[2])

    return name_list


def rowColtoXY(rowCol, width, height):
    """
    Generates x,y position within grid

    :param rowCol: client coordinates
    :param width: grid width
    :param height: grid height
    :return: x,y position tuple
    """

    y = height - rowCol[0] - 1
    x = rowCol[1]

    return (x, y)

def errorMessage(msg):
    """
    Program is exited because a certain requirement is violated

    :param msg: Str - error message
    :return:
    """

    sys.exit(msg)


def time_tick_to_hour(time_tick):
    """
    Convert the current time tick into the hour of day

    :param time_tick: time in model units
    :return: time in hours
    """
    hour = math.floor(time_tick / 60)

    if hour > 23:
        hour = 23

    return hour

def time_tick_to_string(time_tick):
    """
    Convert the current time tick into a string indicating the exact time

    :param time_tick: time in model units
    :return: Time string
    """

    hour = math.floor(time_tick / 60)
    minutes = time_tick - hour * 60
    if hour > 23:
        hour = hour - 24

    hour_string = f"{hour:02d}"
    minute_string = f"{minutes:02d}"
    string = hour_string + ":" + minute_string

    return string

