import os
import glob

totalCounts = {'LOM': 0, 'LOC': 0, 'LOV': 0, 'OK': 0}
fileCount = 0
for t in range(10):
	filename = 't{}/raven.out'.format(t)
	fileCount += len(glob.glob('t{}/*csv'.format(t)))

	if not os.path.isfile(filename):
		continue

	fin = open(filename)

	counts = {'LOM': 0, 'LOC': 0, 'LOV': 0, 'OK': 0}

	for line in fin:
		if line.startswith('Model run time:'):
			counts['OK'] += 1
		elif line.startswith('LOV'):
			counts['LOV'] += 1
		elif line.startswith('LOC'):
			counts['LOC'] += 1
		elif line.startswith('LOM'):
			counts['LOM'] += 1
		else:
			pass
			# print(line)

	total = 0
	for key,value in counts.items():
		total += value
		totalCounts[key] += value

	if total:
		print('#'*80)
		print('\tSeed | {}'.format(t))
		print('\tCount| {}'.format(total))
		for key in ['LOM','LOC','LOV']:
			value = counts[key]
			print('\t{}  | {:6.2e}'.format(key, float(value)/total))
		print('')


total = 0
for key,value in totalCounts.items():
	total += value

print('#'*80)
print('#'*80)
print('#'*80)
print('total:')
for key in ['LOM','LOC','LOV']:
	value = totalCounts[key]
	print('{}: {:6.2e}'.format(key, float(value)/total))
print('#'*80)
print('#'*80)
print('#'*80)
print('Simulations Run: {}/{} ({:5.1f}% Complete)'.format(total, 100000, 100*float(total)/100000.))
print('  Files Written: {}/{} ({:5.1f}% Complete)'.format(fileCount, 100000, 100*float(fileCount)/100000.))