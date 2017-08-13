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

import scipy.stats
import operator as op
import numpy as np
import time
import sys

class MissionStage:
	"""
		An enumeration for classifying mission stages, note they are ordinal
		in the sense that PreDock < Docked < PostUndock < Complete. This is
		useful for checking specific conditions.
	"""
	PreDock, Docked, PostUndock, Complete = range(4)

class MissionStatus:
	"""
		An enumeration for encoding the different mission status, note that
		operational condition is zero, so any non-zero condition represents
		a mission loss.
	"""
	OK, LOM, LOC, LOV = range(4)

rocket = """
                 _______
                 \\      \\__
                  \\        \\_____________________
       #####     [                              |\\__________________
   ############|\\[                              |                  ||\\
###############|/[=======--       N A S A       |                  || >
###############|\\[                              | _________________||/
   ############|/[          ____________________|/
       #####      /      __/
                 /______/
"""

brokenRocket = """
                 _______           ##
                 \\      \\__       ###                  ##
                  \\        \\________##___________       ##
                 [                   / \\        |\\_________##  _______
   \\/ _~       #|\\[                \\/            |          \\   \\     ||\\
   [|-'        |/[=======--                     |           /   /    || >
  /(O)\\     ## |\\[                              | ________/   /______||/
              #|/[~~~~~~~~~~_____/\\_____________|/

                  /~~~~~~~~/
                 /______/
"""

demands = {MissionStage.PreDock:    2000,
		   MissionStage.Docked:        0,
		   MissionStage.PostUndock: 1000}

operationExposures = {MissionStage.PreDock:    2,
					  MissionStage.Docked:     0,
					  MissionStage.PostUndock: 1}

leakExposures = {MissionStage.PreDock:      24,
				 MissionStage.Docked:     5040,
				 MissionStage.PostUndock:    4}

exciterExposures = {MissionStage.PreDock:      24,
					MissionStage.Docked:        0,
					MissionStage.PostUndock:    4}

def testSystem(failureProbability, count):
	"""
		Function for testing if a failure has occurred given a set number of
		operations
		@In, failureProbability, float, the probability this component will fail
		@In, count, int, the number of times this operation is requested
		@Out, firstFailure, {int}, the first occurrence of failure for this
		component, if no failure then it will return None
	"""
	if count == 0: return None
	outcomes = scipy.stats.bernoulli.rvs(failureProbability, size=count)
	firstFailure = next((i for i, x in enumerate(outcomes) if x), None)

	return firstFailure

def getRealizedFailure(failureDictionary):
	"""
		Function for retrieving the realized failure given a dictionary of keyed
		failure times
		@In, failureDictionary, {string: int}, a dictionary specifying the
		failure times of each event, None will be representative of an event
		not occurring
		@Out, return, {string: int}, the realized event and when it occurred
	"""

	## Sort these and see if anybody failed, the first one will be
	## the realized failure as the others will not have occur due to
	## handling of the first issue.
	for key,value in sorted(failureDictionary.items(), key=op.itemgetter(1)):
		if value is not None:
			realizedFailure = key
			return key, value
	## If you are still here, then nobody failed
	return None, None

class componentInfo(object):
	def __init__(self):
		self.failureTime = float("inf")

class valveInfo(componentInfo):
	def __init__(self):
		self.failToOpenCount = float("inf")
		self.failToCloseCount = float("inf")
		self.leakTime = float("inf")

class ThrusterStatus(object):
	def __init__(self, idx):
		self.id = idx
		self.uses = 0
		self.hours = 0

		self.fuelValve = valveInfo()
		self.oxidizerValve = valveInfo()
		self.exciter = componentInfo()

		self.isolationValveFailure = False
		self.isolationValveLeak = float("inf")

	def checkFailedOpen(self):
		return self.uses >= min(self.fuelValve.failToOpenCount,self.oxidizerValve.failToOpenCount)

	def checkFailedClose(self):
		return self.uses >= min(self.fuelValve.failToCloseCount,self.oxidizerValve.failToCloseCount)

	def checkLeakage(self, missionTime):
		return missionTime >= min(self.fuelValve.leakTime, self.oxidizerValve.leakTime)

	def checkExciter(self):
		return self.hours >= self.exciter.failureTime

	def checkFuelValve(self):
		return self.hours >= self.fuelValve.failureTime

	def checkOxidizerValve(self):
		return self.hours >= self.oxidizerValve.failureTime

	def checkValves(self):
		return self.checkFuelValve() or self.checkOxidizerValve()

	def checkIsolationValve(self, missionTime):
		return missionTime >= self.isolationValveLeak

class RCS(object):
	def __init__(self):
		self.times = {}
		self.times[MissionStage.PreDock]    = 24
		self.times[MissionStage.Docked]     = 5040
		self.times[MissionStage.PostUndock] = 4

		self.elapsedMissionTime = 0
		self.currentStage = MissionStage.PreDock
		self.LOM = None
		self.LOC = None
		self.LOV = None

		self.thrusters = {}
		for letter in ['A','B','C']:
			self.thrusters[letter] = [ThrusterStatus(letter), ThrusterStatus(letter)]

		## Initial conditions for a simulation
		self.availability = {'A': [True, True], 'B': [True, True], 'C': [True, True]}
		self.checkIsolationValves = {'A': False, 'B': False, 'C': False}
		self.activeThrusters = [self.thrusters['A'][0], self.thrusters['A'][1]]

		self.events = []

	def checkLoss(self, isolationLeak = False):
		sum0 = self.availability['A'][0] + self.availability['B'][0] + self.availability['C'][0]
		sum1 = self.availability['A'][1] + self.availability['B'][1] + self.availability['C'][1]

		## Another way we could test if all three thrusters are no longer available
		# sum0 = self.activeThrusters[0] is not None
		# sum1 = self.activeThrusters[1] is not None


		if isolationLeak or 0 in [sum0,sum1]:
			## Depending on when the failure occurs we may get either a loss of
			## crew or a loss of vehicle
			# print(brokenRocket)
			if self.currentStage == MissionStage.Docked:
				sys.stdout.write('LOV - Mission has ended in irrecoverable loss.')
				self.LOV = self.elapsedMissionTime
				return MissionStatus.LOV
			else:
				sys.stdout.write('LOC - Mission has ended in irrecoverable loss.')
				self.LOC = self.elapsedMissionTime
				return MissionStatus.LOC

		if 1 in [sum0,sum1]:
			## If we are already on our way home, then there is no mission left
			## to abort, so this is not classified as a loss
			if self.currentStage < MissionStage.PostUndock:
				# print(rocket)
				sys.stdout.write('LOM - Mission has been aborted. Returning home.')
				self.currentStage = MissionStage.PostUndock
				self.LOM = self.elapsedMissionTime
				## There is still a chance something worse could happen, so
				## continue the mission
				loss = self.run()
				if loss is not None:
					return loss
				else:
					return MissionStatus.LOM

		return None

	def updateThrusters(self):
		"""
			Ensure the thrusters are valid and update them if they are not
		"""
		for group in [0,1]:
			if self.activeThrusters[group] is not None:
				nextIdx = self.activeThrusters[group].id
				while not self.availability[nextIdx][group]:
					nextIdx = chr(ord(nextIdx)+1)
					if nextIdx > 'C':
						break
				if nextIdx > 'C':
					self.activeThrusters[group] = None
				elif nextIdx != self.activeThrusters[group].id:
					self.events.append((self.elapsedMissionTime, self.currentStage, self.activeThrusters[group].id + str(group) + '_Deactivated'))
					self.events.append((self.elapsedMissionTime, self.currentStage, nextIdx + str(group) + '_Activated'))
					self.activeThrusters[group] = self.thrusters[nextIdx][group]

	def run(self):
		self.updateThrusters()
		loss = self.checkLoss()

		if loss is not None:
			return loss

		if self.currentStage == MissionStage.Complete:
			return None

		## If we are docked we can coarsen the timestep resolution since we only
		## need to check the leakage
		if self.currentStage == MissionStage.Docked:
			demandsPerHour = 1
		else:
			demandsPerHour = 1000
		uses = 0
		## Check if anything failed each hour of operation
		for step in range(demandsPerHour*self.times[self.currentStage]):
			hour = float(step) / demandsPerHour
			## First check for leaks as they have the largest downstream effect
			## Leaks in the activated isolation valves? Instant failure
			if hour < leakExposures[self.currentStage]:
				for letter in ['A','B','C']:
					if self.checkIsolationValves[letter]:
						isolationLeak = self.thrusters[letter][0].checkIsolationValve(self.elapsedMissionTime)
						if isolationLeak:
							self.events.append((self.elapsedMissionTime, self.currentStage, letter + '_IsolationValveLeak'))
							loss = self.checkLoss(isolationLeak)
							if loss is not None:
								return loss

				## Leaks in the active valves? Can be recovered
				for group in [0,1]:
					if self.activeThrusters[group].checkLeakage(self.elapsedMissionTime):
						failedIdx = self.activeThrusters[group].id
						if self.elapsedMissionTime >= self.activeThrusters[group].fuelValve.leakTime:
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveLeak'))
						else:
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveLeak'))

						## Failure to close
						## Remove both downstream thrusters from
						## availability and attempt to set the new active
						## thrusters
						other = int(not group)
						self.availability[failedIdx][group] = False
						self.availability[failedIdx][other] = False
						self.updateThrusters()

						## Attempt to close the isolation valve and see if
						## we still have enough resources to continue
						isolationLeak = self.thrusters[failedIdx][group].isolationValveFailure
						if isolationLeak:
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + '_IsolationValveLeak'))

						loss = self.checkLoss(isolationLeak)
						if loss is not None:
							return loss
						self.checkIsolationValves[failedIdx] = True

						if self.activeThrusters[group].checkLeakage(self.elapsedMissionTime):
							failedIdx = self.activeThrusters[group].id
							if self.elapsedMissionTime >= self.activeThrusters[group].fuelValve.leakTime:
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveLeak'))
							else:
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveLeak'))
							## Failure to open, remove both thrusters from
							## availability and attempt to set the new active
							## thrusters
							self.availability[failedIdx][group] = False
							self.availability[failedIdx][other] = False
							self.updateThrusters()

							## Check for mission status
							loss = self.checkLoss()
							if loss is not None:
								return loss
							self.checkIsolationValves[failedIdx] = True

							## Attempt to close the isolation valve and see if
							## we still have enough resources to continue
							isolationLeak = self.thrusters[failedIdx][group].isolationValveFailure
							if isolationLeak:
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + '_IsolationValveLeak'))

							loss = self.checkLoss(isolationLeak)
							if loss is not None:
								return loss

							self.updateThrusters()

							if self.activeThrusters[group].checkLeakage(self.elapsedMissionTime):
								failedIdx = self.activeThrusters[group].id
								if self.elapsedMissionTime >= self.activeThrusters[group].fuelValve.leakTime:
									self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveLeak'))
								else:
									self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveLeak'))

								## Failure to open, remove both thrusters from
								## availability and process the failure
								self.availability[failedIdx][group] = False
								self.availability[failedIdx][other] = False

								## Mission has failed, this will always
								## return LOC/V at this point
								return self.checkLoss()

			## Next, check for failures from demand as they can also have
			## downstream effects
			if uses < demands[self.currentStage]:
				for group in [0,1]:
					if self.activeThrusters[group].checkFailedOpen():
						failedIdx = self.activeThrusters[group].id
						if self.activeThrusters[group].uses >= self.activeThrusters[group].fuelValve.failToOpenCount:
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveStuckClosed'))
						else:
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveStuckClosed'))

						## Failure to open
						## Update this thruster's availability and attempt to
						## set a new active
						self.availability[failedIdx][group] = False
						self.updateThrusters()

						## Check for mission status
						loss = self.checkLoss()
						if loss is not None:
							return loss

						if self.activeThrusters[group].checkFailedOpen():
							failedIdx = self.activeThrusters[group].id
							if self.activeThrusters[group].uses >= self.activeThrusters[group].fuelValve.failToOpenCount:
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveStuckClosed'))
							else:
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveStuckClosed'))

							## Failure to open, remove this thruster's availability
							self.availability[failedIdx][group] = False

							## Check for mission status
							loss = self.checkLoss()
							if loss is not None:
								return loss

							self.updateThrusters()

							if self.activeThrusters[group].checkFailedOpen():
								failedIdx = self.activeThrusters[group].id
								if self.activeThrusters[group].uses >= self.activeThrusters[group].fuelValve.failToOpenCount:
									self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveStuckClosed'))
								else:
									self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveStuckClosed'))

								## Failure to open, remove this thruster's availability
								self.availability[failedIdx][group] = False

								## Mission has failed, this will always
								## return LOC/V at this point
								return self.checkLoss()

					if self.activeThrusters[group].checkFailedClose():
						## Failure to close
						## Remove both downstream thrusters from
						## availability and attempt to set the new active
						## thrusters
						failedIdx = self.activeThrusters[group].id
						if self.activeThrusters[group].uses >= self.activeThrusters[group].fuelValve.failToCloseCount:
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveStuckOpen'))
						else:
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveStuckOpen'))

						other = int(not group)
						self.availability[failedIdx][group] = False
						self.availability[failedIdx][other] = False
						self.updateThrusters()

						## Attempt to close the isolation valve and see if
						## we still have enough resources to continue
						isolationLeak = self.thrusters[failedIdx][group].isolationValveFailure
						if isolationLeak:
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + '_IsolationValveLeak'))

						loss = self.checkLoss(isolationLeak)
						if loss is not None:
							return loss
						self.checkIsolationValves[failedIdx] = True

						if self.activeThrusters[group].checkFailedClose():
							failedIdx = self.activeThrusters[group].id
							if self.activeThrusters[group].uses >= self.activeThrusters[group].fuelValve.failToCloseCount:
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveStuckOpen'))
							else:
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveStuckOpen'))

							## Failure to open, remove both thrusters from
							## availability and attempt to set the new active
							## thrusters
							self.availability[failedIdx][group] = False
							self.availability[failedIdx][other] = False
							self.updateThrusters()

							## Check for mission status
							loss = self.checkLoss()
							if loss is not None:
								return loss
							self.checkIsolationValves[failedIdx] = True

							## Attempt to close the isolation valve and see if
							## we still have enough resources to continue
							isolationLeak = self.thrusters[failedIdx][group].isolationValveFailure
							if isolationLeak:
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + '_IsolationValveLeak'))

							loss = self.checkLoss(isolationLeak)
							if loss is not None:
								return loss

							self.updateThrusters()

							if self.activeThrusters[group].checkFailedClose():
								failedIdx = self.activeThrusters[group].id
								if self.activeThrusters[group].uses >= self.activeThrusters[group].fuelValve.failToCloseCount:
									self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveStuckOpen'))
								else:
									self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveStuckOpen'))
								## Failure to open, remove both thrusters from
								## availability and process the failure
								self.availability[failedIdx][group] = False
								self.availability[failedIdx][other] = False

								## Mission has failed, this will always
								## return LOC/V at this point
								return self.checkLoss()

				## Check for valve operational failure
				for group in [0,1]:
					if self.activeThrusters[group].checkValves():
						failedIdx = self.activeThrusters[group].id
						if self.activeThrusters[group].checkFuelValve():
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveFail'))
						else:
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveFail'))
						## Failure to open
						## Update this thruster's availability and attempt to
						## set a new active
						self.availability[failedIdx][group] = False
						self.updateThrusters()

						## Check for mission status
						loss = self.checkLoss()
						if loss is not None:
							return loss

						if self.activeThrusters[group].checkValves():
							failedIdx = self.activeThrusters[group].id
							if self.activeThrusters[group].checkFuelValve():
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveFail'))
							else:
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveFail'))

							## Failure to open, remove this thruster's availability
							self.availability[failedIdx][group] = False

							## Check for mission status
							loss = self.checkLoss()
							if loss is not None:
								return loss

							self.updateThrusters()

							if self.activeThrusters[group].checkValves():
								failedIdx = self.activeThrusters[group].id

								if self.activeThrusters[group].checkFuelValve():
									self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_FuelValveFail'))
								else:
									self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_OxidizerValveFail'))

								## Failure to open, remove this thruster's availability
								self.availability[failedIdx][group] = False

								## Mission has failed, this will always
								## return LOC/V at this point
								return self.checkLoss()

				## Increment our demand tracker for whatever is currently the
				## "active" thruster
				for group in [0,1]:
					self.activeThrusters[group].uses += 1
				uses += 1

			## Exciter failure?
			if hour < exciterExposures[self.currentStage]:
				for group in [0,1]:
					if self.activeThrusters[group].checkExciter():
						failedIdx = self.activeThrusters[group].id
						self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_ExciterFail'))
						## Failure to open
						## Update this thruster's availability and attempt to
						## set a new active
						failedIdx = self.activeThrusters[group].id
						self.availability[failedIdx][group] = False
						self.updateThrusters()

						## Check for mission status
						loss = self.checkLoss()
						if loss is not None:
							return loss

						if self.activeThrusters[group].checkExciter():
							failedIdx = self.activeThrusters[group].id
							self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_ExciterFail'))
							## Failure to open, remove this thruster's availability
							self.availability[failedIdx][group] = False

							## Check for mission status
							loss = self.checkLoss()
							if loss is not None:
								return loss

							self.updateThrusters()

							## Check common cause failure again
							if self.activeThrusters[group].checkExciter():
								failedIdx = self.activeThrusters[group].id
								self.events.append((self.elapsedMissionTime, self.currentStage, failedIdx + str(group) + '_ExciterFail'))
								## Failure to open, remove this thruster's availability
								self.availability[failedIdx][group] = False

								## Mission has failed, this will always
								## return LOC/V at this point
								return self.checkLoss()

			## Increment our time keepers
			for group in [0,1]:
				self.activeThrusters[group].hours += 1/demandsPerHour

			self.elapsedMissionTime += 1/demandsPerHour

		self.currentStage += 1
		self.run()

def initialize(self, runInfoDict, inputFiles):
	pass

def run(dataObject,Input):
	start = time.time()
	rcs = RCS()

	for letter in ['A','B','C']:
		for group in [0, 1]:
			## Store this value twice even though it is the same, thus if either
			## group encounters this condition it should be handled correctly
			rcs.thrusters[letter][group].isolationValveFailure = Input[letter+'isolationValveStuckOpen']
			rcs.thrusters[letter][group].isolationValveLeak  = Input[letter+'isolationValveLeak']

			prefix = letter+str(group)
			rcs.thrusters[letter][group].fuelValve.failToOpenCount = Input[prefix+'fuelStuckClosed']
			rcs.thrusters[letter][group].oxidizerValve.failToOpenCount = Input[prefix+'oxidizerStuckClosed']
			rcs.thrusters[letter][group].fuelValve.failToCloseCount = Input[prefix+'fuelStuckOpen']
			rcs.thrusters[letter][group].oxidizerValve.failToCloseCount = Input[prefix+'oxidizerStuckOpen']

			rcs.thrusters[letter][group].fuelValve.failureTime = Input[prefix+'fuelOperation']
			rcs.thrusters[letter][group].oxidizerValve.failureTime = Input[prefix+'oxidizerOperation']

			rcs.thrusters[letter][group].fuelValve.leakTime = Input[prefix+'fuelLeak']
			rcs.thrusters[letter][group].oxidizerValve.leakTime = Input[prefix+'oxidizerLeak']

			rcs.thrusters[letter][group].exciter.failureTime = Input[prefix+'ExciterFailure']


	CCF2 = 0.04830
	CCF3 = 0.00517

	for letter in ['A','B','C']:
		for group in [0,1]:
			for valve in ['fuel','oxidizer']:
				for action in ['Open','Close']:
					ccf = np.random.uniform(0,1)
					if ccf <= CCF3:
						for other in set(['A','B','C']) - set(letter):
							minValue = min(rcs.thrusters[other][group].__dict__[valve+'Valve'].__dict__['failTo'+action+'Count'],rcs.thrusters[letter][group].__dict__[valve+'Valve'].__dict__['failTo'+action+'Count'])
							rcs.thrusters[other][group].__dict__[valve+'Valve'].__dict__['failTo'+action+'Count'] = minValue
					elif ccf <= CCF2:
						other = list(set(['A','B','C']) - set(letter))[np.random.randint(2)]
						minValue = min(rcs.thrusters[other][group].__dict__[valve+'Valve'].__dict__['failTo'+action+'Count'],rcs.thrusters[letter][group].__dict__[valve+'Valve'].__dict__['failTo'+action+'Count'])
						rcs.thrusters[other][group].__dict__[valve+'Valve'].__dict__['failTo'+action+'Count'] = minValue

	############################################################################
	## PROFILING
	simStart = time.time()
	############################################################################

	loss = rcs.run()

	############################################################################
	## PROFILING
	simEnd = time.time()
	############################################################################

	# for hour,iStage,event in rcs.events:
	# 	stage = None
	# 	if iStage == MissionStage.PreDock:
	# 		stage = 'PreDock'
	# 	elif iStage == MissionStage.Docked:
	# 		stage = 'Docked'
	# 	elif iStage == MissionStage.PostUndock:
	# 		stage = 'PostUndock'
	# 	else:
	# 		stage = 'Complete'
	# 	print(hour, stage, event)


	didNotOccur = 5069 #rcs.elapsedMissionTime+1

	## Setup the initial conditions:
	keysToUpdate = []
	for letter in ['A','B','C']:
		keysToUpdate.append(letter + '_IsolationValveOpen')
		keysToUpdate.append(letter + '_IsolationValveLeak')

		for group in ['0','1']:
			prefix = letter+group

			keysToUpdate.append(prefix + '_Activated')
			keysToUpdate.append(prefix + '_Deactivated')
			keysToUpdate.append(prefix + '_ExciterFail')
			for valve in ['Fuel','Oxidizer']:
				keysToUpdate.append(prefix +  '_' + valve + 'ValveFail')
				keysToUpdate.append(prefix +  '_' + valve + 'ValveStuckOpen')
				keysToUpdate.append(prefix +  '_' + valve + 'ValveStuckClosed')
				keysToUpdate.append(prefix +  '_' + valve + 'ValveLeak')

	for key in keysToUpdate:
		if key in ['A0_Activated', 'A1_Activated']:
			dataObject.__dict__[key] = 0
		else:
			dataObject.__dict__[key] = didNotOccur


	## These are the standard mission times, however an event could trigger
	## the PostUndock to occur earlier, however this should be captured below
	## by the events loop
	dataObject.DockTime = 24
	dataObject.UndockTime = 24+5040
	dataObject.EndTime = rcs.elapsedMissionTime

	dataObject.CCF2  = didNotOccur
	dataObject.CCF22 = didNotOccur
	dataObject.CCF3  = didNotOccur

	dataObject.LOM = didNotOccur
	dataObject.LOC = didNotOccur
	dataObject.LOV = didNotOccur

	dataObject.boolLOM = 0
	dataObject.boolLOC = 0
	dataObject.boolLOV = 0

	## NOW process all of the events as they occurred, first check our failure
	## flags
	if rcs.LOM is not None:
		dataObject.LOM = rcs.LOM
		dataObject.boolLOM = 1
	if rcs.LOC is not None:
		dataObject.LOC = rcs.LOC
		dataObject.boolLOC = 1
	if rcs.LOV is not None:
		dataObject.LOV = rcs.LOV
		dataObject.boolLOV = 1

	events = list(reversed(rcs.events))

	while len(events) > 0:
		t,stage,event = events.pop()
		if stage == MissionStage.PostUndock and t < dataObject.UndockTime:
			if t < dataObject.DockTime:
				dataObject.DockTime = didNotOccur
			dataObject.UndockTime = t

		if 'CCF2' in event:
			if dataObject.CCF2 < didNotOccur:
				dataObject.CCF22 = t
			else:
				dataObject.CCF2 = t
			event = event[:-5]
		elif 'CCF3' in event:
			dataObject.CCF3 = t
			event = event[:-5]

		dataObject.__dict__[event] = t

	end = time.time()
	print('Model run time: {:4.2f} s'.format(end-start))
	############################################################################
	## PROFILING
	if end-start > 1:
		print('\tSimulation      : {:4.2f} s'.format(simEnd-simStart))
		print('\tNumber of events: {}'.format(len(rcs.events)))
	############################################################################
