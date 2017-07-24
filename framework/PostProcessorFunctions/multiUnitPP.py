'''
Created on May 22, 2017

'''
 
#for future compatibility with Python 3--------------------------------------------------------------
from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)
if not 'xrange' in dir(__builtins__):
  xrange = range
#End compatibility block for Python 3----------------------------------------------------------------

#External Modules------------------------------------------------------------------------------------
import numpy as np
import copy
import itertools
from scipy.stats import beta
#External Modules End--------------------------------------------------------------------------------

from PostProcessorInterfaceBaseClass import PostProcessorInterfaceBase

class multiUnitPP(PostProcessorInterfaceBase):
  """ This class inherits form the base class PostProcessorInterfaceBase and it ... :
      - initialize
      - run
      - readMoreXML
  """

  def initialize(self):
    """
     Method to initialize the Interfaced Post-processor
     @ In, None,
     @ Out, None,

    """
    PostProcessorInterfaceBase.initialize(self)
    self.inputFormat  = 'PointSet'
    self.outputFormat = 'PointSet'
    self.estimator    = None

  def run(self,inputDic):
    """
    This method ....
     @ In, inputDic, list, list of dictionaries which contains the data inside the input DataObjects
     @ Out, inputDic, dict, same inputDic dictionary

    """
    if len(inputDic)>1:
      self.raiseAnError(IOError, 'multiUnitPP Interfaced Post-Processor ' + str(self.name) + ' accepts only one dataObject')
    
    inputDic = inputDic[0]
    
    numberSamples        = inputDic['data']['output'][self.variables[0]].size
    numberVariables      = len(self.variables)
    numberConfigurations = 2**numberVariables
    PCprobValues         = np.zeros(numberConfigurations)
    percentiles_5        = np.zeros(numberConfigurations)
    percentiles_95       = np.zeros(numberConfigurations)
    
    if 'metadata' in inputDic.keys():
      if 'ProbabilityWeight' in inputDic['metadata'].keys():
        pbWeights = copy.deepcopy(inputDic['metadata']['ProbabilityWeight'])/np.sum(inputDic['metadata']['ProbabilityWeight'])
      else:
        pointCount = len(inputDic['data']['input'].values()[0])
        pbWeights  = np.ones(pointCount)/float(pointCount) 

    dataRestructured = np.zeros((numberSamples,numberVariables))
    
    for idx,var in enumerate(self.variables):
      if inputDic['data']['output'][var].checkBool():
        dataRestructured[:,idx] = inputDic['data']['output'][var]
      else:
        self.raiseAnError(IOError, 'multiUnitPP Interfaced Post-Processor ' + str(self.name) + '; output variable ' + str(var) + ' contains values other than 0 or 1')
    
    dataRestructuredToList = dataRestructured.tolist()
    
    # see https://stackoverflow.com/questions/14931769/how-to-get-all-combination-of-n-binary-value    
    plantConfiguration = list(itertools.product([0, 1], repeat=numberVariables)) 
    outputDict = {'data':{}, 'metadata':{}}
    outputDict['data']['input']  = {}
    outputDict['data']['output'] = {}
    
    label=np.zeros(numberConfigurations)
    
    for index,PC in enumerate(plantConfiguration):
      if list(PC) in dataRestructuredToList:
        indexes = np.where(np.all(dataRestructured == np.asarray(PC),axis=1))[0]
        if self.estimator is None:
          PCprobValues[index] = np.sum(pbWeights[indexes])
        elif self.estimator == "MC":
          if pbWeights[indexes].size > 0:
            aPrior = pbWeights[indexes].size
            bPrior = pbWeights.size - pbWeights[indexes].size + 0.5
            PCprobValues[index]   = aPrior/(aPrior+bPrior)
            percentiles_5[index]  = beta.ppf(.05, aPrior, bPrior)
            percentiles_95[index] = beta.ppf(.95, aPrior, bPrior)
          else:
            PCprobValues[index]   = 0.0
            percentiles_5[index]  = 0.0
            percentiles_95[index] = 0.0            
          
      label[index] = index
        
    for idx,var in enumerate(self.variables):
      outputDict['data']['input'][var] = np.asarray(plantConfiguration)[:,idx]
    
    outputDict['data']['output']['probability']    = PCprobValues
    outputDict['data']['output']['percentiles_5']  = percentiles_5
    outputDict['data']['output']['percentiles_95'] = percentiles_95
    outputDict['data']['output']['label'] = label
    
    return outputDict
    
  def readMoreXML(self,xmlNode):
    """
      Function that reads elements this post-processor will use
      @ In, xmlNode, ElementTree, Xml element node
      @ Out, None
    """
    for child in xmlNode:
      if child.tag == 'variables':
        self.variables = child.text.split(',')
      elif child.tag == "estimator":
        self.estimator = child.text
        
