import os
import glob

totalCounts = {'LOM': 0, 'LOC': 0, 'LOV': 0, 'OK': 0}
truth       = {'LOM': 2.58e-3, 'LOC': 3.1e-4}
fileCount = 0
for t in range(10):
	filename = 's{}/raven.out'.format(t)
	filesWritten = len(glob.glob('s{}/*csv'.format(t)))
	fileCount += filesWritten

	if not os.path.isfile(filename):
		continue

	fin = open(filename)

	counts = {'LOM': 0, 'LOC': 0, 'LOV': 0, 'OK': 0}

	endTime = None
	for line in fin:
		if line.startswith('Model run time:'):
			counts['OK'] += 1
		if 'LOV' in line:
			counts['LOV'] += 1
		if 'LOC' in line:
			counts['LOC'] += 1
		if 'LOM' in line:
			counts['LOM'] += 1
		if 'sec) SIMULATION               : Message         -> Run complete!' in line:
			token = line.split('s',1)[0].replace('(', '').strip()
			endTime = float(token)

	total = 0
	for key,value in counts.items():
		total += value
		totalCounts[key] += value

	if total:
		print('#'*80)
		print('\tSeed  | {}'.format(t))
		print('\tCount | {}'.format(total))
		print('\tFiles | {}'.format(filesWritten))
		if endTime:
			print('\tTime  | {:4.0f}'.format(endTime))
		else:
			print('\tTime  | ')

		print('\tLOV   | {}'.format(counts['LOV']))
		for key,expProb in truth.items():
			value = counts[key]
			actProb = float(value)/total
			print('\t{}   | {:6.2e} ( {:5.1f}% )'.format(key, actProb, 100*abs(actProb - expProb) / expProb))
			print('\t      | {}'.format(value))
		print('')


total = 0
for key,value in totalCounts.items():
	total += value

print('#'*80)
print('#'*80)
print('#'*80)
print('total:')
for key,expProb in truth.items():
	value = totalCounts[key]
	actProb = float(value)/total
	print('\t{}  | {:6.2e} ( {:5.1f}% )'.format(key, actProb, 100*abs(actProb - expProb) / expProb))
	print('\t     | {}'.format(value))

print('#'*80)
print('#'*80)
print('#'*80)
print('Simulations Run: {:6d} / {:6d} ({:5.1f}% Complete )'.format(total, 100000, 100*float(total)/100000.))
print('  Files Written: {:6d} / {:6d} ({:5.1f}% Complete )'.format(fileCount, 10, 100*float(fileCount)/10.))

print('#'*80)
print('#'*80)
print('#'*80)
filename = 'raven.out'
filesWritten = len(glob.glob('*csv'))
fileCount += filesWritten

if os.path.isfile(filename):
	fin = open(filename)
	counts = {'LOM': 0, 'LOC': 0, 'LOV': 0, 'OK': 0}

	for line in fin:
		if line.startswith('Model run time:'):
			counts['OK'] += 1
		if 'LOV' in line:
			counts['LOV'] += 1
		if 'LOC' in line:
			counts['LOC'] += 1
		if 'LOM' in line:
			counts['LOM'] += 1

	total = 0
	for key,value in counts.items():
		total += value
		totalCounts[key] += value

	if total:
		print('#'*80)
		print('Total Run')
		print('Count | {}'.format(total))
		print('Files | {}'.format(filesWritten))
		print('LOV   | {}'.format(counts['LOV']))
		for key,expProb in truth.items():
			value = counts[key]
			actProb = float(value)/total
			print('{}   | {:6.2e} ( {:5.1f}% )'.format(key, actProb, 100*abs(actProb - expProb) / expProb))
			print('\t      | {}'.format(value))
		print('')