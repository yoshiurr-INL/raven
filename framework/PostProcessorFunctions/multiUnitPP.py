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
    
    if 'metadata' in inputDic.keys():
      if 'ProbabilityWeight' in inputDic['metadata'].keys():
        pbWeights = copy.deepcopy(inputDic['metadata']['ProbabilityWeight'])/np.sum(inputDic['metadata']['ProbabilityWeight'])

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
    for index,PC in enumerate(plantConfiguration):
      if list(PC) in dataRestructuredToList:
        indexes = np.where(np.all(dataRestructured == np.asarray(PC),axis=1))[0]
        PCprobValues[index] = np.sum(pbWeights[indexes])
        
    for idx,var in enumerate(self.variables):
      outputDict['data']['input'][var] = np.asarray(plantConfiguration)[:,idx]
    
    outputDict['data']['output']['probability'] = PCprobValues
    
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
