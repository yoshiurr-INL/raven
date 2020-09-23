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
    return ([("parallel", "runner.py "+input[0].getAbsFile())], os.path.join(input[0].getPath(), "output"))

  def createNewInput(self, inputs, oinputs, samplerType, **Kwargs):
    print(inputs, oinputs, samplerType, Kwargs)
    print("createNewInput")
    self._output_directory = None
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
          elif line.lstrip().startswith("--output-directory="):
            self._output_directory = line.split("=",1)[1].rstrip()
          newLines.append(line)
        newFile = open(singleInput.getAbsFile(),"w")
        for line in newLines:
          newFile.write(line)
        newFile.close()
      else:
        print("SampledVars", Kwargs["SampledVars"])
        data = open(singleInput.getAbsFile(),"r").read()
        for var in Kwargs["SampledVars"]:
          data = data.replace("$"+var+"$", str(Kwargs["SampledVars"][var]))
        open(singleInput.getAbsFile(),"w").write(data)
        print("Huh?", singleInput)
    return inputs

  def finalizeCodeOutput(self, command, codeLogFile, subDirectory):
    print("finalizeCodeOutput", command, codeLogFile, subDirectory)
    to_read = "hourly_summary" #"Daily_summary"
    if self._output_directory is not None:
      directory = os.path.join(subDirectory, self._output_directory, to_read)
    else:
      directory = os.path.join(subDirectory, to_read)
    if to_read.lower().startswith("hourly"):
      #Need to merge the date and hour
      directoryNew = directory + "_merged"
      outFile = open(directoryNew+".csv","w")
      inFile = open(directory+".csv","r")
      for line in inFile.readlines():
        splited = line.split(",", maxsplit=1)
        outFile.write(splited[0].rstrip()+"_"+splited[1].lstrip())
      directory = directoryNew
    return directory

  def addDefaultExtension(self):
    """
      Possible input extensions found in the input files.
      @ In, None
      @ Out, None
    """
    self.addInputExtension(['txt', 'dat'])

