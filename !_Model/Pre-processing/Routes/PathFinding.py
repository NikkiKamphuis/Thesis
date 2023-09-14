"""
Created on Thu Apr 22 14:21:10 2021

@author: jelle
"""
from heapq import heappop, heappush
import math
import sys
import numpy as np

class Node:
    """
    Represents a node in de network
    """
    def __init__(self, location, risk):
        self.location = location
        self.risk = risk   #injuries per hour
        self.neighbors = []
        self.parent = None
        self.distance = float('inf')
        self.g = float('inf')
        self.f = None

    def clear(self, nodes_to_find):
        infinity = sys.float_info.max
        self.parent = None
        self.g = infinity
        self.distance = infinity
        self.f = [infinity] * nodes_to_find

    def addneighbor(self, cost, other, distance):
        # add edge in both directions
        self.neighbors.append((cost, other, distance))
        other.neighbors.append((cost, self, distance))

    def __gt__(self, other):  # make nodes comparable
        return min(self.f) > min(other.f)

    def __repr__(self):
        return str(self.location)

class GridGraph:
    def __init__(self, grid, droneSpeed): #drone speed in km/h
        
        timePerHectometer = (100 / (droneSpeed /3.6)) / (60*60)
        self.minCost = np.min(grid) * timePerHectometer
        width = len(grid[0])
        height = len(grid)

        nodes = []
        for i in range(height):
            noderow = []
            nodes.append(noderow)
            for j in range(width):
                node = Node((i, j), grid[i,j])
                noderow.append(node) 
                for di, dj in ((0, -1), (-1, -1), (-1, 0), (-1, 1)):  # 4 directions: W, NW, N, NE 
                 
                    #check of neighbour would we in range
                    if i + di > (height - 1) or i + di < 0 or j+dj > (width -1) or j+dj < 0:
                        continue                        
                    cost = math.sqrt(di**2 + dj**2)*(0.5*grid[i,j] + 0.5*grid[i+di,j+dj])*timePerHectometer   #the time over each grid square times the time over the square
                    distance = math.sqrt(di**2 + dj**2) * 100 #convert distance to meters
                    node.addneighbor(cost, nodes[i+di][j+dj], distance)
        self.nodes = nodes

    @staticmethod
    def reconstructpath(node):
        path = []
        distance = node.distance
        cost = node.g
        while node is not None:
            path.append(node)
            node = node.parent
        path.reverse()
        return path, distance, cost

    
    def heuristic(self, a, b):
        # optimistic score, assuming every risk is the minimum
        dy = abs(a[0] - b[0])
        dx = abs(a[1] - b[1])
        return math.sqrt(dx**2 + dy**2) * self.minCost
    
    @staticmethod
    def minDistance(a,b):
        dy = abs(a[0] - b[0])
        dx = abs(a[1] - b[1])
        return math.sqrt(dx**2 + dy*82) * 100 #convert distance to meters

    def clear(self, nodes_to_find):
        # remove search data from graph 
        for row in self.nodes:
            for node in row:
                node.clear(nodes_to_find)

    def a_star(self, start, goals, uavrange, riskWeightInput):
        
        uavrange = uavrange * 1000 #convert range to meters
        startnode = self.nodes[start[0]][start[1]]

        n = len(goals) #amount of goals to reach
        end_nodes=[0]* n
        nodes_to_find = []
        paths = [0] * n
        lengths = [0] * n
        risks = [0] * n
        found = 0

        for i, goal in enumerate(goals): 
            end_nodes[i] = self.nodes[goal[0]][goal[1]]
            d = self.minDistance(startnode.location, self.nodes[goal[0]][goal[1]].location)
            if d < uavrange:
                nodes_to_find.append(self.nodes[goal[0]][goal[1]])
            else:
                paths[i] = "Out of range"
                lengths[i] = float('inf')
                risks[i] = float('inf')
                found += 1
        
        #print(str(found)+ ' out of '+str(n)+ ' Goals out of reach')
        riskweight = riskWeightInput

       
        while found <= n:
            distanceweight = 1 - riskweight
            self.clear(len(nodes_to_find))
            startnode.g = 0
            startnode.distance= 0
            openlist = [startnode] 
            closed = set()

            while openlist:
                node = heappop(openlist)
                if node in closed:
                    continue
                closed.add(node)
                if node in nodes_to_find:                
                    index = end_nodes.index(node)
                    if paths[index] == 0:
                        found += 1
                        #print(str(found)+' out of '+ str(n) + ' goals found')
                        paths[index], lengths[index], risks[index] = self.reconstructpath(node)                   
                if found == n:
                    return paths, lengths, risks     
                
                for weight, neighbor, distance in node.neighbors:                    
                    g = node.g + weight
                    d = node.distance + distance
                    if ((g * riskweight + d * distanceweight) < (neighbor.g * riskweight + neighbor.distance * distanceweight) ) and (d < uavrange):  #compare node with its neigbour
                        neighbor.distance = d
                        neighbor.g = g
                        for i, endnode in enumerate(nodes_to_find):
                            neighbor.f[i] = (g * riskweight + d * distanceweight) + self.heuristic(neighbor.location, endnode.location)                       
                        neighbor.parent = node
                        heappush(openlist, neighbor)

            riskweight = riskweight / 10 #by emphasizing risk less and distance more, feasible routes are always found
            #print("Not all goals were found optimally, lowering risk weight")

         
        return paths, lengths, risks       