# this file define a fittness function used in clock path variation evaluation 
import load_lut as load
import numpy as np
import os
import json

class Fitness:
	def __init__(self):
		self.prepareLut()
		self.readClockpath()
		self.readConfig()

	def readConfig(self):

		self.f1 = [] # reflect between buffer size and buffer input capacitance

		with open('{}/utils/buffer.json'.format(os.getenv('SYMCTS')),'r') as f:
			a_dict = json.loads(f.read())
			self.lib_size = a_dict['buffer_num']
			for i in range(self.lib_size):
				self.f1.append(a_dict['buffers']['buf{}'.format(i)]['input_cap'])

		with open('{}/utils/sink.json'.format(os.getenv('SYMCTS')),'r') as f:
			a_dict = json.loads(f.read())
			self.sink_cap = a_dict['sink']['input_cap']

		with open('{}/utils/wire.json'.format(os.getenv('SYMCTS')),'r') as f:
			a_dict = json.loads(f.read())
			self.c0 = a_dict['wire']['unit_cap']['value']

		with open('{}/utils/settings.json'.format(os.getenv('SYMCTS')),'r') as f:
			a_dict = json.loads(f.read())
			self.a     = a_dict['symcts']['a']
			self.b     = a_dict['symcts']['b']
			self.Slin  = a_dict['symcts']['Slin']

		self.rho_matrix = np.load('{}/utils/rho_matrix.npy'.format(os.getenv('SYMCTS')))

	def readClockpath(self):
		self.num = []
		self.branch = []
		self.WL = []
		with open('{}/symcts/clockpath.txt'.format(os.getenv('SYMCTS')),'r') as f:
			self.L = int(f.readline()) # read in clock tree level
			self.U = int(f.readline()) # read in sink number

			self.branch.append(1)
			for _ in range(self.L):
				self.branch.append(int(f.readline())) # read in branch number of each level
			for _ in range(self.L+1):
				self.WL.append(float(f.readline())/1000) # read in wire length between every branchs(um)

			for i in range(self.L+1):
				fanout = 1
				fanout_list = []
				for j in range(i,self.L+1):
					fanout *= self.branch[j]
					fanout_list.append(fanout)
				self.num.append(fanout_list)



	def prepareLut(self):
		DModel, SModel = load.initialize()
		# DModel is a list containing miu and sigma of delay at rise and fall edge respectively
		# DModel[0]:miu(delay), rise edge | DModel[1]:sigma(delay), rise edge | DModel[2]:miu(delay), fall edge | DModel[3]:sigma(delay), fall edge

		# SModel is a list containing miu and sigma of output slew at rise and fall edge respectively
		# SModel[0]:miu(slew), rise edge | SModel[1]:sigma(slew), rise edge | SModel[2]:miu(slew), fall edge | SModel[3]:sigma(slew), fall edge

		# PModel is a list containing power value at rise and fall edge respectively
		# PModel[0]:power dissiption, rise edge | PModel[1]:power dissiption, fall edge
		self.f21 = SModel[0]
		self.f22 = SModel[1]
		self.f31 = DModel[0]
		self.f32 = DModel[1]

	def computeObj(self,strategy):

		
		raw_strategy = np.array([self.lib_size] + strategy) # assume largest buffer at clock root

		buffer_strategy = raw_strategy[raw_strategy != 0] - 1
		buffer_index_of_strategy = np.nonzero(raw_strategy)[0]

		M = buffer_strategy.size # buffer level in the strategy


		Cl   = np.zeros(M)
		Slout = np.zeros(M)
		Delay = np.zeros(M)
		Delay_sigma = np.zeros(M)
		# recording information of each buffer level

		# construct load capacitance list of each clock buffer

		for i in range(M-1):
			num = np.array(self.num[buffer_index_of_strategy[i]][:(buffer_index_of_strategy[i+1]-buffer_index_of_strategy[i])])
			wl = np.array(self.WL[buffer_index_of_strategy[i]:buffer_index_of_strategy[i+1]])

			Cl[i] = sum(num*wl*self.c0) + self.f1[buffer_strategy[i]]*num[-1]

		num = np.array(self.num[buffer_index_of_strategy[-1]])
		wl = np.array(self.WL[buffer_index_of_strategy[-1]:])
		Cl[M-1] = sum(num*wl*self.c0) + self.sink_cap*num[-1]
		slew_in = self.Slin
		# tranverse clock path
		for i in range(M):
			s = buffer_strategy[i]
			Slout[i] = self.f21[s](slew_in, Cl[i])		
			Delay[i] = self.f32[s](slew_in, Cl[i])
			Delay_sigma[i] = self.f31[s](slew_in, Cl[i])
			
			slew_in = Slout[i]
			
		sigma_skew = np.power(Delay_sigma,2).sum() + sum(self.rho_matrix[buffer_strategy[i],buffer_strategy[i+1]]*Delay_sigma[i]* Delay_sigma[i+1] for i in range(M-1))

		return sigma_skew 
		# return sigma_skew 


	def objFitness(self,strategy):
		fitness = 1/float(self.computeObj(strategy))
		return fitness

