import sys
import numpy as np

def readInput(inFile):
  """
    Reads in the key values.
    @ In, inFile, Python file object, file containing inputs
    @ Out, (x,y,z), tuple(float,float,float), input values
  """
  x, y, z = 0,0,0
  for line in inFile:
    var,val = line.strip().split('=')
    if   var.strip() == 'x': x = float(val)
    elif var.strip() == 'y': y = float(val)
    elif var.strip() == 'z': z = float(val)
  if x is None or y is None or z is None:
    raise IOError('x,y,z were not all found in input file',inFile)
  return x,y,z

def run(x,y,z):
  """
    Performs elementary calculations.
    @ In, x, float, value
    @ In, y, float, value
    @ In, z, float, value
    @ Out, 1, float, 1.0
  """
  return 1.0

def write(x,y,z,a,outname):
  """
    Writes to a CSV file, but intentionally truncates it
    @ In, x, float, value
    @ In, y, float, value
    @ In, z, float, value
    @ In, a, float, value
    @ In, outname, string, name of output file
    @ Out, None
  """
  out = file(outname+'.csv','w')
  out.writelines('x,y,z,a\n')
  out.writelines(','.join(str(np.around(s,decimals=3)) for s in [x,y,z,a])+'\n')
  out.close()

if __name__ == '__main__':
  if '-i' not in sys.argv:
    raise IOError('No input file was specified with "-i"!')
  if '-o' not in sys.argv:
    raise IOError('No output file was specified with "-o"!')
  if len(sys.argv)<5:
    raise IOError('Insufficient arguments! Need -i Input -o Output')
  inFile = file(sys.argv[2],'r')
  x,y,z = readInput(inFile)
  a = run(x,y,z)
  write(x,y,z,a,sys.argv[4])