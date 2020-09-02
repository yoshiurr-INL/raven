import os
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
    return ([("parallel", "runner.py "+input[0].getAbsFile())], os.path.join(input[0].getPath(),"output.txt"))

  def createNewInput(self, inputs, oinputs, samplerType, **Kwargs):
    print(inputs, oinputs, samplerType, Kwargs)
    print("createNewInput")
    for singleInput in inputs:
      if singleInput.getExt() == 'txt':
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
          newLines.append(line)
        newFile = open(singleInput.getAbsFile(),"w")
        for line in newLines:
          newFile.write(line)
        newFile.close()
      else:
        print("Huh?", singleInput)
    return inputs

  def addDefaultExtension(self):
    """
      Possible input extensions found in the input files.
      @ In, None
      @ Out, None
    """
    self.addInputExtension(['txt', 'dat'])

