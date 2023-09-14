import requests
import pdb
import json
from pyproj import Proj, transform, Transformer
import geopandas as gdp
import numpy as np
import datetime
from pytz import timezone, utc
import pickle
import aiohttp
import ujson
import asyncio
import time


#--- Helper functions

def convert_projections(x, y):
    """
    Helper function that transforms the coordinate system from x,y to lon, lat
    :param x:
    :param y:
    :return:
    """
    transformer = Transformer.from_crs("epsg:28992", "epsg:4326")
    lon, lat = transformer.transform(x, y)
    lon = round(lon, 4)
    lat = round(lat, 4)
    return lon, lat


def create_time_strings(week, day):
    """
    Helper function that creates strings that are formatted as the input strings required for the BING API
    :param week:
    :param day:
    :return:
    """

    amsterdam = timezone("Europe/Amsterdam")
    date_string = str("2022 " + str(week) + " " + str(day))
    date = datetime.datetime.strptime(date_string, "%G %V %u")

    start_time = datetime.datetime.combine(date, datetime.time(0, 0, 0))
    start_time.replace(tzinfo=amsterdam)
    utc_start_time = start_time.astimezone(utc)
    start_time_string = utc_start_time.strftime("%Y-%m-%dT%H:%M:%S%z")
    start_time_string = "{0}:{1}".format(start_time_string[:-2], start_time_string[-2:])

    end_time = datetime.datetime.combine(date, datetime.time(23, 0, 0))
    end_time.replace(tzinfo=amsterdam)
    utc_end_time = end_time.astimezone(utc)
    end_time_string = utc_end_time.strftime("%Y-%m-%dT%H:%M:%S%z")
    end_time_string = "{0}:{1}".format(end_time_string[:-2], end_time_string[-2:])

    return start_time_string, end_time_string

#--- Inputs

#Provide a bing API key here, see: https://docs.microsoft.com/en-us/bingmaps/getting-started/bing-maps-dev-center-help/getting-a-bing-maps-key
#for testing purposes please contact the developer
bing_key = 'AggzIBrC2_la8qPx5pCPI8IWTintjCaI_CGeXnxp_Afwj6sHWbbUDs9VTMac9ZXX'

upper_left_x = 75000                            # Western edge of case study in epsg:28992
upper_left_y = 475000                           # Northern edge of case study in epsg:28992
size = 40000                                    # Size of case study map
minx = upper_left_x
maxx = upper_left_x + size
miny = upper_left_y - size
maxy = upper_left_y
bbox = (minx, maxy, maxx, miny)
bbox2 = (minx, miny, maxx, maxy)                # 'EPSG:28992'

# Indicate if this is for test data set
test = True

# Data fields to ignore when retrieving hospital data
ignoreHospitalFields = [
    "x_nav",
    "y_nav",
    "loc_straat",
    "gemeente",
    "regionr",
    "website",
    "telefoon",
    "bijzonderh",
]

# Read hospital shapefile
# Source: https://esrinl-content.maps.arcgis.com/home/item.html?id=8997462eed994d12a6e32c63a5c64023#data
hospitals = gdp.read_file("Data/Ziekenhuizen.shp", ignore_fields=ignoreHospitalFields,
            ignore_geometry=True)

# Create geo dataframe
# The code field represents the amount of hospital beds
hospitals = gdp.GeoDataFrame(hospitals, geometry=gdp.points_from_xy(hospitals.x, hospitals.y))
hospitals = hospitals.cx[minx:maxx, miny:maxy]
hospitalTypes = ["Ziekenhuis", "Academisch ziekenhuis", "Buitenpolikliniek"]

# Drop all none hospitals like clinics, leaving only 'real' hospitals
hospitals = hospitals[hospitals["loc_type"].isin(hospitalTypes)]
hospitals = hospitals.reset_index(drop=True)

if test:
    hospitals = hospitals.loc[[0, 10, 15, 16], :]

params = {"key": bing_key}

hospital_lat_lon = []   #List with the coordinates of the hospitals
original_origins = []  #list with raw coordinate tuples
altered_origins = []  #list with altered coordinates that can be accessed by road

for index, hospital in hospitals.iterrows():

    lat, lon = convert_projections(hospital.geometry.x, hospital.geometry.y)
    hospital_lat_lon.append([lat, lon])
    original_origins.append({"latitude": lat, "longitude": lon})
    # This converts the coordinates to points from where routes can be computed
    url = (
        "http://dev.virtualearth.net/REST/v1/Locations/"
        + str(lat)
        + ","
        + str(lon)
        + "?o=json&key="
        + bing_key
    )
    newLoc = requests.get(url).json()
    coordinates = newLoc["resourceSets"][0]["resources"][0]["geocodePoints"][0][
        "coordinates"
    ]
    altered_origins.append({"latitude": coordinates[0], "longitude": coordinates[1]})

# Dictionary that will store route lengths in travel time
output_time_dict = {}
# Dictionary that will store route lengths in distance
output_distance_dict = {}

# Loop over all days in the week
for day in range(1, 8):
    output_time_dict[day] = {}
    output_distance_dict[day] = {}

    output_time_dict[day] = {}
    output_distance_dict[day] = {}

    # Create a new time string for this perticular day, testing showed that travel times are the
    # same no matter the week thus 8 could be any number between 1 and 52
    start_time, end_time = create_time_strings(8, day)

    # Create request json
    # Resolution 4 means one value for every hour
    post_json = {
        "origins": altered_origins,
        "destinations": altered_origins,
        "travelMode": "driving",
        "startTime": start_time,
        "endTime": end_time,
        "resolution": 4,
        "timeUnit": "second",
    }

    url = "https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrixAsync"

    async def api_request():
        """
        Creates API requests
        :return:
        """
        session = aiohttp.ClientSession(json_serialize=ujson.dumps)

        async with session.post(url, params=params, json=post_json) as resp:
            r = await resp.json()
            #print(r)
            call_back_url = r["resourceSets"][0]["resources"][0]["callbackUrl"]
            waiting_time = r["resourceSets"][0]["resources"][0]["callbackInSeconds"]

            return call_back_url, waiting_time

    call_back_url, waiting_time = asyncio.run(api_request())

    # Wait until it is expected that the API has returned the results
    time.sleep(waiting_time)

    resultUrl = 0

    while resultUrl == 0:
        # Check if the API request is completed
        r2 = requests.get(call_back_url).json()

        if r2["resourceSets"][0]["resources"][0]["isCompleted"]:
            # Get the API request result download link
            resultUrl = r2["resourceSets"][0]["resources"][0]["resultUrl"]
        else:
            time.sleep(5)

    #print(json.dumps(r2, indent=4))
    #print(resultUrl)

    # Download the results
    final_results = requests.get(resultUrl)
    # Decode results data
    decoded_data = final_results.content.decode("utf-8-sig")
    data = json.loads(decoded_data)
    data = data["results"]

    num_hubs = len(hospital_lat_lon)

    # Create an empty matrix for every hour of the day
    for i in range(24):
        output_time_dict[day][i] = np.empty((num_hubs, num_hubs))
        output_distance_dict[day][i] = np.empty((num_hubs, num_hubs))

    # Loop trough the result data, retract and convert all the data and strore them in the right Datafield
    for row in data:
        origin = row["originIndex"]
        destination = row["destinationIndex"]
        distance = row["travelDistance"]
        travel_time = row["travelDuration"]
        dep_time = row["departureTime"]
        dep_time = dep_time[:19] + dep_time[-6:]
        dt = datetime.datetime.strptime(dep_time, "%Y-%m-%dT%H:%M:%S%z")
        Dutch_time = dt.astimezone(timezone("Europe/Berlin"))
        hour = Dutch_time.hour
        output_time_dict[day][hour][origin, destination] = travel_time
        output_distance_dict[day][hour][origin, destination] = distance

    print(f"Done with day {day} out of 7")

# Save the matrices in an output file
docName = str("Output/CarRoutesMatrices.pkl")
with open(docName, "wb") as f:
    pickle.dump([output_distance_dict, output_time_dict], f)
