# -*- coding: utf-8 -*-
"""
Created on Tue Sept 5

@author: Nikki Kamphuis
"""
import geopandas as gdp
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from owslib.wfs import WebFeatureService
from owslib.wms import WebMapService
from pyproj import Proj, transform, Transformer
import numpy as np
from PathFinding import *
import random as rd
from PIL import Image, ImageFilter
import pickle
import datetime, time
import os

# --- Helper functions for code at bottom (line 274)

def coordinates_to_index(minx, maxy, x, y):
    """
    Helper functions to convert coordinates to x and y values

    :param minx:
    :param maxy:
    :param x:
    :param y:
    :return:
    """

    row = int((maxy-y) / 100)
    column = int((x-minx) / 100)

    return row, column

# Helper function that transorms the coordinate system 
def convertProjections(x, y):
    
    transformer = Transformer.from_crs('epsg:28992', 'epsg:4326')
    
    lon, lat = transformer.transform(x, y)
    
    return lon, lat


def get_background_map(bbox):
    """
    Function to download the background map and save it as an image
    :param bbox: Size of map that you want to download in coordinates
    :return: Saved backgroundmap
    """
    background_map_url = "https://geodata.nationaalgeoregister.nl/top250raster/wms?"
    background_map_wms = WebMapService(background_map_url)
    background_map_layer = 'top250raster'
    img = background_map_wms.getmap(size=(500, 500), layers=[background_map_layer], bbox=bbox,
                                  format="image/jpeg", srs='EPSG:28992')
    out = open('Output/backGroundMap.jpg', 'wb')
    out.write(img.read())
    out.close()
    img = Image.open('Output/backGroundMap.jpg')
    white_filter = Image.new("RGB", img.size, (255,255,255))
    out = Image.blend(img, white_filter, 0.7)
    out = out.convert('RGB')
    out.save('Output/backGroundMap.jpg')


#Function to load the population data and return it as a geopandas file 
def load_population_data(bbox):
    """
    Function to load the population data and return it as a geopandas file
    :param bbox: Size of map in coordinates
    :return: Geopandas file of population data
    """
    ignore_fields = ['aantal_mannen', 'aantal_vrouwen', 'aantal_inwoners_0_tot_15_jaar',
                     'aantal_inwoners_15_tot_25_jaar', 'aantal_inwoners_25_tot_45_jaar',
                     'aantal_inwoners_45_tot_65_jaar', 'aantal_inwoners_65_jaar_en_ouder',
                     'percentage_nederlandse_achtergrond', 'percentage_westerse_migr_achtergr',
                     'percentage_niet_westerse_migr_achtergr', 'aantal_part_huishoudens',
                     'aantal_eenpersoonshuishoudens', 'aantal_meerpersoonshuishoudens_zonder_kind',
                     'aantal_eenouderhuishoudens', 'aantal_tweeouderhuishoudens',
                     'gemiddelde_huishoudensgrootte', 'aantal_woningen',
                     'aantal_woningen_bouwjaar_voor_1945', 'aantal_woningen_bouwjaar_45_tot_65',
                     'aantal_woningen_bouwjaar_65_tot_75', 'aantal_woningen_bouwjaar_75_tot_85',
                     'aantal_woningen_bouwjaar_85_tot_95', 'aantal_woningen_bouwjaar_95_tot_05',
                     'aantal_woningen_bouwjaar_05_tot_15', 'aantal_woningen_bouwjaar_15_en_later',
                     'aantal_meergezins_woningen', 'percentage_koopwoningen', 'percentage_huurwoningen',
                     'aantal_huurwoningen_in_bezit_woningcorporaties', 'aantal_niet_bewoonde_woningen',
                     'gemiddelde_woz_waarde_woning', 'aantal_personen_met_uitkering_onder_aowlft',
                     'percentage_geb_nederland_herkomst_nederland','percentage_geb_nederland_herkomst_overig_europa',
                     'percentage_geb_nederland_herkomst_buiten_europa','percentage_geb_buiten_nederland_herkomst_europa',
                     'percentage_geb_buiten_nederland_herkmst_buiten_europa']

    # Load the density data
    population = gdp.read_file("Data/cbs_vk100_2022.gpkg", ignore_fields = ignore_fields,
                               bbox=bbox, ignore_geometry=True,)
    population = population.replace(-99997, 0)
    population = population.rename(columns = {'crs28992res100m':'id'})

    # Load the 100x100 map
    base_map = gdp.read_file('Data/NL_vierkant100m.shp', bbox=bbox)
    base_map = base_map.rename(columns = {'C28992R100':'id'})
    population_map = pd.merge(base_map, population, how='outer', on='id')
    print(population_map.info())

    return population_map

def load_no_fly_zones(bbox):
    """
    Function to load the No-Flyzones and return it as a geopandas file
    :param bbox: Size of Netherlands in coordinates
    :return:
    """
    noflyzone_url ='https://geodata.nationaalgeoregister.nl/dronenoflyzones/wfs?'

    # Initialize web service
    noflyzone_wfs = WebFeatureService(url=noflyzone_url, version='2.0.0')
    noflyzone_layer = 'dronenoflyzones:luchtvaartgebieden'
    noflyzone_data = noflyzone_wfs.getfeature(typename = noflyzone_layer, bbox=bbox, outputFormat='application/json')

    # Write to file
    fn = 'noflyzone_output.geojson'
    with open(fn, 'wb') as fh:
        fh.write(noflyzone_data.read())

    no_flyzone_map = gdp.read_file(fn)
    
    return no_flyzone_map

def load_hospital_data(minx, maxx, miny, maxy, test):
    """
    Load the hospital data and return a list with all hospitals, not including clinics

    :param minx:
    :param maxx:
    :param miny:
    :param maxy:
    :return:
    """
        
    ignore_hospital_fields = ['x_nav', 'y_nav',  'loc_straat',  'gemeente', 'regionr',
                              'website', 'telefoon',  'bijzonderh']

    # bron: https://esrinl-content.maps.arcgis.com/home/item.html?id=8997462eed994d12a6e32c63a5c64023#data
    hospitals = gdp.read_file('Data/Ziekenhuizen.shp',  ignore_fields = ignore_hospital_fields, ignore_geometry=True)
    hospitals = gdp.GeoDataFrame(hospitals, geometry=gdp.points_from_xy(hospitals.x, hospitals.y))
    hospitals = hospitals.cx[minx:maxx,miny:maxy]

    hospitalTypes = ["Ziekenhuis", "Academisch ziekenhuis", "Buitenpolikliniek" ]

    # Drop all none ziekenhuizen
    hospitals = hospitals[hospitals['loc_type'].isin(hospitalTypes)]
    hospitals = hospitals.reset_index(drop=True)

    if test:
        hospitals = hospitals.loc[[0, 10, 15, 16], :]

    return hospitals


def create_risk_map(population_map, no_flyzone_map, no_flyzone_weight, population_weight, no_flyzone_verboden_weight,
                  no_flyzone_beperkt_n_weight, no_flyzone_else_weight, probability_of_events, impact_areas, shelter_factors):
    """
    Combine the different maps into a risk map

    :param population_map: Map containing population data
    :param no_flyzone_map: Map containing flyzone data
    :param no_flyzone_weight: Map containing data on no flyzones
    :param population_weight: Weight of population size in risk determination
    :param no_flyzone_verboden_weight: Weight of flyzone type in risk determination
    :param no_flyzone_beperkt_n_weight: Weight of flyzone type in risk determination
    :param no_flyzone_else_weight: Weight of flyzone type in risk determination
    :param probability_of_events: Proability of certain types of UAV failure
    :param impact_areas: Impact area of certain type of UAV failure
    :param shelter_factors: Also used for UAV fialure risk determination

    :return: Map containing risk factor for each geometry point, the risk level in a cell with a population of 1
    """
    
    p_injury = 0

    # Create a risk factor per capita, by combining the different crash models and corresponding shelterfactors,
    # proabilitiy of events and impact areas

    for index, p_event in enumerate(probability_of_events):
        p_injury += shelter_factors[index] * p_event * impact_areas[index] / (100*100)

    # Create gridmap from risk_map
    riskmap = population_map.copy()
    riskmap['aantal_inwoners'] = riskmap['aantal_inwoners'].fillna(0)
    riskmap['geometry'] = riskmap['geometry'].centroid
    riskmap.plot(column='aantal_inwoners', cmap='YlOrRd', marker='s', markersize=0.1, norm=matplotlib.colors.LogNorm())
    riskmap['noflyzone'] = 0
    
    # PriLoop over the no flyzones and update the weights to all gridmap cells within the no fly zone
    # Loop over no fly zones. Different no fly zones have different weights
    for index, zone in no_flyzone_map.iterrows():
        danger_number = 0

        if zone.localtype == 'Verboden':
            danger_number = no_flyzone_verboden_weight

        elif zone.localtype == 'Beperkt toegestaan':
            danger_number = no_flyzone_beperkt_n_weight

        else:
            danger_number = no_flyzone_else_weight

        within = riskmap[riskmap.geometry.within(zone.geometry)]
        # Update risk map
        riskmap['noflyzone'] = riskmap['noflyzone'] + danger_number * (riskmap['id'].isin(within['id'])).astype(int)
    
    # Create the risk map by combining the no flyzones and population maps according to their corresponding weights
    # Combine into single Risk factor
    riskmap['riskfactor'] = riskmap['noflyzone'] * no_flyzone_weight + (riskmap['aantal_inwoners']) * \
                            p_injury * population_weight

    # The risk level in a cell with a population of 1
    min_risk = p_injury * population_weight

    return riskmap, min_risk

def create_grid_matrix(riskmap, hospitals, min_risk):
    """
    Convert the created riskmap to a matrix and create a grid

    :param riskmap: map containing risk factors for each geometry point
    :param hospitals: list of hospitals
    :param min_risk: minimum risk
    :return:
    """

    # Obtain map bounds
    minx, miny, maxx, maxy = riskmap.geometry.total_bounds

    # Initialize grid matrix with all lowest values
    grid = np.full((int((maxx-minx) / 100+1), int((maxy-miny) / 100+1)), min_risk)
    hospital_grid = np.full((int((maxx-minx) / 100+1), int((maxy-miny) / 100+1)), False)
    hospital_coordinate_list = []
    hospital_lon_lat = []
    hospital_names =[]
    hospital_list = []
    
    # Loop over the riskmap datastructure and convert to the right matrix grid cell
    for index, node in riskmap.iterrows():
        row, column = coordinates_to_index(minx, maxy, node.geometry.x, node.geometry.y)
        grid[row, column] = grid[row, column] + node['riskfactor']

    #Loop over all hospitals retreiving both name and location and storing them into a list
    for index, hospital in hospitals.iterrows():
        row, column = coordinates_to_index(minx, maxy, hospital.geometry.x, hospital.geometry.y)
        hospital_grid[row,column] = True
        hospital_coordinate_list.append((row, column))
        lat, lon = convertProjections(hospital.geometry.x, hospital.geometry.y)
        hospital_lon_lat.append([lon, lat])
        hospital_names.append(str(hospital['Organisati']+str(hospital['loc_naam'])))
        hospital_list.append({'Name': str(hospital['Organisati']+ " "+str(hospital['loc_naam'])),
                              'GridCoordinates': (row, column), 'LatLonCoordinates': (lon, lat),
                              'beds':hospital['code']})
        
    return grid, hospital_grid, hospital_list, hospital_coordinate_list, hospital_lon_lat


def find_routes(grid, hospital_list, hospital_coordinate_list, drone_speed, drone_range):
    """
    Function that finds the optimal routes

    :param grid:
    :param hospital_list:
    :param hospital_coordinate_list:
    :param drone_speed:
    :param drone_range:
    :return:
    """
    graph = GridGraph(grid, drone_speed)
    n = len(hospital_list)

    # Initialise matrices
    distance_matrix = np.zeros((n, n))
    risk_matrix = np.zeros((n, n))
    routes_matrix = np.zeros((n, n), dtype=object)
    
    for i, hospital in enumerate(hospital_list):
        print("Start searching risk optimal routes for from "+ str(hospital['Name']))
        routes, distances, risks = graph.a_star(hospital_coordinate_list[i], hospital_coordinate_list[:], drone_range, 1)
    
        for j in range(n):

            if risk_matrix[i, j] == 0 or risk_matrix[i, j] > risks[j]:
    
                distance_matrix[i, j] = distances[j]
                risk_matrix[i, j] = risks[j]
                routes_matrix[i, j] = routes[j]

    direct_distance_matrix = np.zeros((n, n))
    direct_risk_matrix = np.zeros((n, n))
    direct_routes_matrix = np.zeros((n, n), dtype=object)

    for i, hospital in enumerate(hospital_list):
        print("Start searching direct routes  for from "+str(hospital['Name']))
        routes, distances, risks = graph.a_star(hospital_coordinate_list[i], hospital_coordinate_list[:], drone_range,0)
    
        for j in range(n):
            if direct_risk_matrix[i, j] == 0 or direct_risk_matrix[i, j] > risks[j]:
    
                direct_distance_matrix[i, j] = distances[j]
                direct_risk_matrix[i, j] = risks[j]
                direct_routes_matrix[i, j] = routes[j]

    return distance_matrix, risk_matrix, routes_matrix, direct_distance_matrix, direct_risk_matrix, direct_routes_matrix

def plot_drone_routes(grid, drone_routes, drone_distances, drone_risks, pic_name):
    """
    Plots the constructed routes

    :param grid:
    :param drone_routes:
    :param drone_distances:
    :param drone_risks:
    :param pic_name:
    :return:
    """

    cm = plt.get_cmap('gist_rainbow')
    plt.figure(figsize=(15, 15))
    plt.imshow(grid, cmap='Greys', norm=matplotlib.colors.LogNorm())
    
    n, m = drone_routes.shape
    
    for i in range(n):

        for j in range(m):

            if drone_distances[j,i] != float('inf') and drone_distances[i,j] != float('inf'):

                # Check if other route is safer
                if (drone_risks[i, j] - drone_risks[j, i]) >= 1:
                    print('Other route is faster')
                    drone_distances[i, j] = drone_distances[j, i]
                    drone_risks[i, j] = drone_risks[j, i]
                    drone_routes[i, j] = drone_routes[j, i]

                # Obtain entire route
                x_val = [x.location[1] for x in drone_routes[i,j]]
                y_val = [x.location[0] for x in drone_routes[i,j]]
                plt.plot(x_val,y_val, color=cm(1.*i/n),  linewidth=2)

    # Plot the hosptials
    for i, hospital in enumerate(hospital_coordinate_list):
        plt.plot(hospital[1], hospital[0], color=cm(1.*i/n), markersize=20, marker='P',
                 label=str(hospitals.iloc[i]['Organisati']))

    # Add legend
    plt.legend(loc='upper right',bbox_to_anchor=(0., 1.02, 1., .102),ncol=4, mode="expand")
    plt.savefig(pic_name)



def export_matrices(drone_distances, drone_risk, hospital_list, direct_drone_distances, direct_drone_risks, grid):
    """
    Exports the matrices

    :param drone_distances:
    :param drone_risk:
    :param hospital_list:
    :param direct_drone_distances:
    :param direct_drone_risks:
    :param grid:
    :return:
    """

    hospital_input = []
    rd.seed(1)

    for i, hospital in enumerate(hospital_list):
        beds = hospital['beds']

        # The default is 250 beds
        if beds == 0:
            beds = 250

        hospital_input.append([hospital['GridCoordinates'], beds, hospital['Name']])

    # Save the matrices in an output file
    doc_name = str("DroneRoutesMatrices.pkl")

    with open(doc_name, 'wb') as f:  # Python 3: open(..., 'wb')
        pickle.dump([hospital_input, drone_distances, drone_risk, grid, direct_drone_distances, direct_drone_risks], f)


# --- Input parameters for route determination

# No-fly zones - unused
no_fly_zone_verboden_weight = 5
no_fly_zone_beperkt_weight = 3
no_fly_zone_else_weight = 1

no_flyzone_weight = 0  # No-fly zones are not included
population_weight = 1

# Spatial parameters
# Use http://projfinder.com/ to find
upper_left_x = 75000    # Western edge of case study in epsg:28992
upper_left_y = 475000   # Northern edge of case study in epsg:28992
size = 40000            # Size of case study map
minx = upper_left_x
maxx = upper_left_x + size
miny = upper_left_y - size
maxy = upper_left_y  
bbox = (minx, maxy, maxx, miny)
bbox2 = (minx, miny, maxx,maxy)         # 'EPSG:28992'


# Risk parameters
# Ballistic, Uncontrolled Glide, Parachute, Fly Away, events per hour
shelter_factors = [0.3, 0.3, 0.6, 0.3]
probability_of_events = [1/125, 1/150, 1/100, 1/200]
impactAreas = [0.3, 0.6, 0.3, 0.6]          # m^2/person

# Drone parameters
drone_speed = 90                                    # km/h
drone_range = 100                                   # km
drone_flight_time = drone_range / drone_speed       # h

# Test set
test = True                                         # indicates if this is for a test hospital set

# --- Code to run

get_background_map(bbox2)
population_map = load_population_data(bbox)
no_fly_zone_map = load_no_fly_zones(bbox)
hospitals = load_hospital_data(minx, maxx, miny, maxy, test)

riskmap, min_risk = create_risk_map(population_map, no_fly_zone_map, no_flyzone_weight, population_weight,
                                 no_fly_zone_verboden_weight, no_fly_zone_beperkt_weight, no_fly_zone_else_weight,
                                 probability_of_events, impactAreas, shelter_factors)

grid, hospital_grid, hospital_list, \
    hospital_coordinate_list , hospital_lon_lat = create_grid_matrix(riskmap, hospitals, min_risk)

drone_distances, drone_risks, drone_routes, direct_drone_distances, direct_drone_risks, \
    direct_drone_routes = find_routes(grid, hospital_list, hospital_coordinate_list, drone_speed, drone_range)

plot_drone_routes(grid, drone_routes, drone_distances, drone_risks, "Output/risk_routes.png")
plot_drone_routes(grid, direct_drone_routes, direct_drone_distances, direct_drone_risks, "Output/direct_routes.png")

export_matrices(drone_distances, drone_risks, hospital_list, direct_drone_distances, direct_drone_risks, grid)

