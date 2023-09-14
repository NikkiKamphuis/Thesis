# -*- coding: utf-8 -*-
"""
Created on Mon Jul 19 08:49:39 2021

@author: jelle
"""
from local_mesa.visualization.ModularVisualization import VisualizationElement
from collections import defaultdict
import numpy as np
import os




class HistogramModule(VisualizationElement):

    package_includes = ["Chart.min.js"]
    local_includes = ["HistogramModule.js"]
    canvas_height = 200
    canvas_width = 500

    def __init__(self, bins, canvas_height, canvas_width):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.bins = bins
        new_element = "new HistogramModule({}, {}, {})"
        new_element = new_element.format(bins, canvas_width, canvas_height)
        self.js_code = "elements.push(" + new_element + ");"

    def render(self, model):
        values = [agent.speedOfDelivery for agent in model.completedDemands]
        hist = np.histogram(values, bins=self.bins)[0]
        print(hist)
        return [int(x) for x in hist]
 
class CanvasGrid(VisualizationElement):
    """Optimized grid visualization for runningtime minimization 
    """ 

    #package_includes = ["GridDraw.js", "CanvasModule.js", "InteractionHandler.js"]
    #local_includes = ["local_mesa/visualization/templates/js/CustomGridDraw.js", "local_mesa/visualization/templates/js/CustomCanvasModule.js", "local_mesa/visualization/templates/js/CustomInteractionHandler.js"] 
    package_includes = ["CustomGridDraw.js", "CustomCanvasModule.js", "customInteractionHandler.js"] 
 
    def __init__(
        self,
        portrayal_method,
        grid_width,
        grid_height,
        canvas_width=500,
        canvas_height=500,
    ):

        self.portrayal_method = portrayal_method
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height 
  
           

        new_element = "new CustomCanvasModule({}, {}, {}, {})".format(
            self.canvas_width, self.canvas_height, self.grid_width, self.grid_height
        )
 
        self.js_code = "elements.push(" + new_element + ");"
 
    def render(self, model):  #this function is altered for optimization reasons
        grid_state = defaultdict(list)
        for agent in model.vehicles:
            portrayal = self.portrayal_method(agent)
            if portrayal:
                x,y = agent.pos
                portrayal["x"] = x 
                portrayal["y"] = y 
                grid_state[portrayal["Layer"]].append(portrayal)
 
        for agent in model.medHubs:
            portrayal = self.portrayal_method(agent)
            if portrayal:
                x,y = agent.pos
                portrayal["x"] = x
                portrayal["y"] = y   
                grid_state[portrayal["Layer"]].append(portrayal)
        # for x in range(model.grid.width):
        #     for y in range(model.grid.height):
        #         cell_objects = model.grid.get_cell_list_contents([(x, y)])
        #         for obj in cell_objects:
        #             portrayal = self.portrayal_method(obj)
        #             if portrayal:
        #                 portrayal["x"] = x   
        #                 portrayal["y"] = y
        #                 grid_state[portrayal["Layer"]].append(portrayal)

        return grid_state

    
    

