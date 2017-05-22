'''
Created on May 22, 2017

'''
from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)

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
     
    numberSamples        = inputDic['data']['output'][self.variables[0]].size
    numberVariables      = len(self.variables)
    numberConfigurations = 2**numberVariables
    
    dataRestructured = np.zeros((numberSamples,1))
    
    for idx,var in self.variables:
      if np.array_equal(inputDic['data']['output'][var], inputDic['data']['output'][var].astype(bool)):
        dataRestructured[:,idx] = inputDic['data']['output'][var]
      else:
        self.raiseAnError(IOError, 'multiUnitPP Interfaced Post-Processor ' + str(self.name) + '; output variable ' + str(var) + ' contains values other than 0 or 1')
    
    # see https://stackoverflow.com/questions/14931769/how-to-get-all-combination-of-n-binary-value
    
    plantConfiguration = list(itertools.product([0, 1], repeat=numberVariables)) 
    
    inputDict = {'data':{}, 'metadata':{}}
    
    for PC in plantConfiguration:
      indexes = np.unique(np.where(b==np.asarray(PC))[0])
      
    
  def readMoreXML(self,xmlNode):
    """
      Function that reads elements this post-processor will use
      @ In, xmlNode, ElementTree, Xml element node
      @ Out, None
    """
    for child in xmlNode:
      if child.tag == 'variables':
        self.variables = child.text.split(',').strip()
