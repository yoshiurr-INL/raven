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
Created on 2020-Sept-2

This is a CodeInterface for the Presient code.

"""

import os
import re
try:
  import pkg_resources
  prescient = pkg_resources.get_distribution("prescient")
  prescientLocation = prescient.location
except Exception as inst:
  print("Finding Prescient failed with",inst)
  prescientLocation = None

from CodeInterfaceBaseClass import CodeInterfaceBase

class Prescient(CodeInterfaceBase):
  def generateCommand(self, input, exe, clargs=None, fargs=None, preExec=None):
    print(input, exe, clargs, fargs, preExec)
    print("generateCommand")
    runnerInput = []
    for inp in input:
      if inp.getType() == 'PrescientRunnerInput':
        runnerInput.append(("parallel", "runner.py "+inp.getAbsFile()))

    return (runnerInput, os.path.join(input[0].getPath(), "output"))

  def createNewInput(self, inputs, oinputs, samplerType, **Kwargs):
    print(inputs, oinputs, samplerType, Kwargs)
    print("createNewInput")
    self._output_directory = None
    for singleInput in inputs:
      if singleInput.getType() == 'PrescientRunnerInput':
        print("Need to modify", singleInput, "to fix", prescientLocation)
        newLines = []
        for line in open(singleInput.getAbsFile(),"r").readlines():
          if line.lstrip().startswith("--model-directory=") and prescientLocation is not None:
            items = line.split("=",1)[1].split("|")
            newPath = prescientLocation
            started = False
            for item in items:
              if item == "prescient":
                started = True
              if started:
                newPath = os.path.join(newPath, item)
            line = "--model-directory="+newPath
          elif line.lstrip().startswith("--output-directory="):
            self._output_directory = line.split("=",1)[1].rstrip()
          newLines.append(line)
        newFile = open(singleInput.getAbsFile(),"w")
        for line in newLines:
          newFile.write(line)
        newFile.close()
      else:
        print("SampledVars", Kwargs["SampledVars"])
        print("Modifying", singleInput)
        data = open(singleInput.getAbsFile(),"r").read()
        for var in Kwargs["SampledVars"]:
          data = data.replace("$"+var+"$", str(Kwargs["SampledVars"][var]))
        data = self.__process_data(data, Kwargs["SampledVars"])
        open(singleInput.getAbsFile(),"w").write(data)
    return inputs

  def __process_data(self, data, samples):
    """
      Processes the data and does some simple arithmetic
      @ In, data, string, the string to process
      @ In, samples, dict, the dictionary of variable values
      @ Out, retval, string, the string with values replaced
    """
    #"this is a $(a)$ and $(a+2)$ and $(a-2)$ and $(b_var)$ and $(a*-2.0)$"
    #"and $(a*2+1)$"
    splited = re.split("\$\(([a-z0-9._*+-]*)\)\$", data)
    retval = ""
    for i, value in enumerate(splited):
      if i % 2 == 1:
        name, mult, add = re.match("([a-z_][a-z0-9_]*)(\*-?[0-9.]+)?([+-]?[0-9.]+)?", value).groups()
        num = samples[name]
        if mult is not None:
          num *= float(mult[1:])
        if add is not None:
          num += float(add)
        retval += str(num)
      else:
        retval += value
    return retval

  def _readBusData(self, filename):
    """
      Reads the bus data into a dictionary
      @ In, filename, string, the bus_detail.csv file
      @ Out, (retDict,busList), (dictionary,list), dictionary of each time,
        and list of all the busses found.
    """
    inFile = open(filename, "r")
    first = True
    retDict = {}
    busSet = set()
    for line in inFile.readlines():
      line = line.strip()
      if first:
        first = False
        if line != "Date,Hour,Bus,Shortfall,Overgeneration,LMP,LMP DA":
          assert False, "Unexpected first line of bus detail:" + line
          a = 1/0 #because debug might be disabled
        continue
      splited = line.split(",")
      date, hour, bus = splited[:3]
      rest = splited[3:]
      key = (date,hour)
      busSet.add(bus)
      timeDict = retDict.get(key,{})
      timeDict[bus] = rest
      retDict[key] = timeDict
    busList = list(busSet)
    busList.sort()
    return retDict, busList

  def finalizeCodeOutput(self, command, codeLogFile, subDirectory):
    """
      Convert csv information to RAVEN's prefered formats
      @ In, command, ignored
      @ In, codeLogFile, ignored
      @ In, subDirectory, string, the subdirectory where the information is.
      @ Out, directory, string, the base name of the csv file
    """
    print("finalizeCodeOutput", command, codeLogFile, subDirectory)
    toRead = "hourly_summary" #"Daily_summary"
    if self._output_directory is not None:
      directory = os.path.join(subDirectory, self._output_directory)
    else:
      directory = subDirectory
    readFile = os.path.join(directory, toRead)
    if toRead.lower().startswith("hourly"):
      busData, busList = self._readBusData(os.path.join(directory, "bus_detail.csv"))
      #Need to merge the date and hour
      readFileNew = readFile + "_merged"
      outFile = open(readFileNew+".csv","w")
      inFile = open(readFile+".csv","r")
      first = True
      hasNetDemand = False
      for line in inFile.readlines():
        date, hour, rest = line.split(",", maxsplit=2)
        outFile.write(date.rstrip()+"_"+hour.lstrip()+","+rest.rstrip())
        if first:
          if ",RenewablesUsed," in rest and ",Demand," in rest:
            hasNetDemand = True
            restSplit = rest.split(",")
            renewablesUsedIndex = restSplit.index("RenewablesUsed")
            demandIndex = restSplit.index("Demand")
            outFile.write(","+"NetDemand")
          first = False
          for bus in busList:
            for dataName in ["Shortfall","Overgeneration","LMP","LMP_DA"]:
              outFile.write(","+bus+"_"+dataName)
        else:
          if hasNetDemand:
            #Calculate the demand - renewables used to get net demand
            restSplit = rest.split(",")
            netDemand = float(restSplit[demandIndex]) - float(restSplit[renewablesUsedIndex])
            outFile.write(","+str(netDemand))
          for bus in busList:
            for data in busData[(date,hour)][bus]:
              outFile.write(","+data)
        outFile.write("\n")
      readFile = readFileNew
    return readFile

  def addDefaultExtension(self):
    """
      Possible input extensions found in the input files.
      @ In, None
      @ Out, None
    """
    self.addInputExtension(['txt', 'dat'])

