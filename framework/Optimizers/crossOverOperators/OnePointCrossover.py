# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
  Implementation of One Point Crossover for children crossover in Genetic Algorithm
"""
import numpy as np
from copy import deepcopy
from utils import InputData, InputTypes, randomUtils, mathUtils
from .Crossovers import Crossovers

class OnePointCrossover(Crossovers):
  """
    Uses One Point approach to perform Crossover
  """
  ##########################
  # Initialization Methods #
  ##########################
  @classmethod
  def getInputSpecification(cls):
    """
      Method to get a reference to a class that specifies the input data for class cls.
      @ In, cls, the class for which we are retrieving the specification
      @ Out, specs, InputData.ParameterInput, class to use for specifying input of cls.
    """
    specs = super(OnePoint, cls).getInputSpecification()
    specs.description = r"""if node is present, indicates that."""
    return specs

  ###############
  # Run Methods #
  ###############
  def Cross(self,parents,**kwargs):
    """
      Method designed to perform crossover by swapping chromosome portions before/after specified or sampled location
      @ In, parents, xr.DataArray, parents involved in the mating process.
      @ In, kwargs, dict, dictionary of parameters for this mutation method:
            crossoverProb, float, crossoverProb determines when child takes genes from a specific parent, default is random
            points, integer, point at which the cross over happens, default is random
            variables, list, variables names.
      @ Out, children, np.array, children resulting from the crossover. Shape is nParents x len(chromosome) i.e, number of Genes/Vars
    """
    nParents,nGenes = np.shape(parents)
    # Number of children = 2* (nParents choose 2)
    children = xr.DataArray(np.zeros((int(2*comb(nParents,2)),nGenes)),
                                dims=['chromosome','Gene'],
                                coords={'chromosome': np.arange(int(2*comb(nParents,2))),
                                        'Gene':kwargs['variables']})


    # defaults
    if (kwargs['crossoverProb'] == None) or ('crossoverProb' not in kwargs.keys()):
      crossoverProb = randomUtils.random(dim=1, samples=1)
    else:
      crossoverProb = kwargs['crossoverProb']

    # create children
    parentsPairs = list(combinations(parents,2))

    for ind,parent in enumerate(parentsPairs):
      parent = np.array(parent).reshape(2,-1) # two parents at a time

      if randomUtils.random(dim=1,samples=1) <= crossoverProb:
        if (kwargs['points'] == None) or ('points' not in kwargs.keys()):
          point = list([randomUtils.randomIntegers(1,nGenes-1,None)])
        elif (any(i>=nGenes-1 for i in kwargs['points'])):
          raise ValueError('Crossover point cannot be larger than number of Genes (variables)')
        else:
          point = kwargs['points']
        for i in range(nGenes):
          if len(point)>1:
            raise ValueError('In one Point Crossover a single crossover location should be provided!')
          children[2*ind:2*ind+2,i] = copy.deepcopy(parent[np.arange(0,2)*(i<point[0])+np.arange(-1,-3,-1)*(i>=point[0]),i])
      else:
        # Each child is just a copy of the parents
        children[2*ind:2*ind+2,:] = copy.deepcopy(parent)

    return children
