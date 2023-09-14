import pandas as pd
import numpy as np
import random
import math
import seaborn as sns
import matplotlib.pyplot as plt

# Seed
random.seed(9)

# Obtain list of input hospital
input = pd.read_pickle('Input/DroneRoutesMatrices.pkl')
hospitals = pd.DataFrame(input[0])

# Determine relative sizes
size = dict()

for hospital in hospitals[2]:
	size[hospital] = 1

# Create O&D matrix
# Each row determines the probability of an outgoing order going to one of the hospitals in the columns
# Note that this is cumulative probability
# Note this one is pre-determined, for case study these values should reflect more realism
O_D = [[0, 1/3, 1/3, 1/3],
       [1/3, 0, 1/3, 1/3],
       [1/3, 1/3, 0, 1/3],
       [1/3, 1/3, 1/3, 0]]
O_D = pd.DataFrame(O_D)
O_D.columns = list(hospitals[2])
O_D.index = list(hospitals[2])

# Parameter for intensity of use of network in orders per minute
orders_per_minute = 0.013888

# Deadlines types
deadline_types = ['urgent', 'semi-urgent', 'same-day']
deadline_times = {'urgent': 60, 'semi-urgent': range(120, 240), 'same-day': None}

# Enter probability information for mass and volume below (empty for now)
#
#
#

# Initialize demand generation
request_list = list()

for hospital in hospitals[2]:
	arrival_time = 0

	while arrival_time < 1440:
		# Get the next probability value from Uniform(0,1)
		p = random.random()

		# Plug it into the inverse of the CDF of Exponential(_lamnbda)
		inter_arrival_time = -1 * math.log(1.0 - p) / (orders_per_minute * size[hospital])

		# Add the inter-arrival time to the running sum
		arrival_time = int(round(arrival_time + inter_arrival_time, 0))

		destination = np.random.choice(list(O_D.columns), size = 1, p = list(O_D.loc[hospital]))[0]

		deadline_type = random.choice(deadline_types)
		if deadline_type == 'urgent':
			deadline = arrival_time + deadline_times[deadline_type]

		elif deadline_type == 'semi-urgent':
			interval = random.choice(deadline_times[deadline_type])
			deadline = arrival_time + interval

		else:
			deadline = 1440

		request = {'origin': hospital, 'destination': destination, 'start': arrival_time,
					'deadline': deadline, 'type': deadline_type,'volume': 10, 'mass': 20}

		if deadline <= 1440 and arrival_time <= 1440 and deadline - arrival_time >= 60:
			request_list.append(request)

request_list = pd.DataFrame(request_list)
request_list = request_list.sort_values(by = ['start'])
request_list = request_list.reset_index(drop=False)
request_list = request_list.set_index('start')
request_list = request_list.rename(columns={'index':'id'})

#sns.scatterplot(data=request_list, x = 'start', y = request_list.index, hue = 'origin', style = 'type')
#plt.grid()
#plt.show()

request_list.to_csv('Output/Demand_new.csv')