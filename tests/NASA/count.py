fin = open('raven.out')

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
for value in counts.values():
	total += value

for key in ['LOM','LOC','LOV']:
	value = counts[key]
	print('{}: {:6.2e}'.format(key, float(value)/total))
print('')
print('Total: {}'.format(total))