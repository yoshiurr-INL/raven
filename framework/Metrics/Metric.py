#External Modules------------------------------------------------------------------------------------
import os
import copy
import shutil
import math
import numpy as np
import abc
import importlib
import inspect
import atexit
#External Modules End--------------------------------------------------------------------------------

#Internal Modules------------------------------------------------------------------------------------
from BaseClasses import BaseType
from Assembler import Assembler
import SupervisedLearning
import PostProcessors #import returnFilterInterface
import CustomCommandExecuter
import utils
import mathUtils
import TreeStructure
import Files

#Internal Modules End--------------------------------------------------------------------------------

class Metric(utils.metaclass_insert(abc.ABCMeta,BaseType)):

  def __init__(self):
    BaseType.__init__(self)
    self.type = self.__class__.__name__
    self.name = self.__class__.__name__

  def initialize(self,inputDict):
    pass

  def _readMoreXML(self,xmlNode):
    pass

  def readMoreXML(self,xmlNode):
    pass

  def distance(self,x,y,weights=None,paramDict=None):
    pass


