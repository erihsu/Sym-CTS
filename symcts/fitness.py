# this file define a fittness function used in clock path variation evaluation 
import load_lut as load
import numpy as np

class Fitness:
	def __init__(self,strategy):
		self.strategy = strategy
		self.prepareLut()
		self.readClockpath()
		self.readConfig()

	def readConfig(self,file='./config.txt'):
		self.f1 = np.array([5, 10, 20, 40, 80])  # reflect between buffer size and buffer input capacitance
		self.max_buffer = len(self.f1)
		self.sink_cap = 15
		with open(file,'r') as f:
			self.a     = float(f.readline().split(' ')[2])
			self.b     = float(f.readline().split(' ')[2])
			self.c0    = float(f.readline().split(' ')[2])
			self.rho_f = float(f.readline().split(' ')[2])
			self.Slin  = float(f.readline().split(' ')[2])

	def readClockpath(self,file='./clockpath.txt'):
		self.num = []
		self.WL = []
		with open(file,'r') as f:
			self.L = int(f.readline()) # read in clock tree level
			self.U = int(f.readline()) # read in sink number
			for i in range(self.L):
				self.num.append(int(f.readline())) # read in branch number of each level
			for i in range(self.L):
				self.WL.append(float(f.readline())/1000) # read in wire length between every branchs(um)

	def prepareLut(self):
		DModel, SModel, PModel = load.initialize(5) # with buffer size
		# DModel is a list containing miu and sigma of delay at rise and fall edge respectively
		# DModel[0]:miu(delay), rise edge | DModel[1]:sigma(delay), rise edge | DModel[2]:miu(delay), fall edge | DModel[3]:sigma(delay), fall edge

		# SModel is a list containing miu and sigma of output slew at rise and fall edge respectively
		# SModel[0]:miu(slew), rise edge | SModel[1]:sigma(slew), rise edge | SModel[2]:miu(slew), fall edge | SModel[3]:sigma(slew), fall edge

		# PModel is a list containing power value at rise and fall edge respectively
		# PModel[0]:power dissiption, rise edge | PModel[1]:power dissiption, fall edge
		self.f21 = SModel[2]
		self.f22 = SModel[3]
		self.f31 = DModel[2]
		self.f32 = DModel[3]

	def computeObj(self):

		# record index in strategy where not equal to 0
		buffer_list = self.strategy
		M = len(buffer_list) # buffer level in the strategy


		Cl   = [0]*M
		Slout = [0]*M
		Slout_sigma = [0]*M
		Delay = [0]*M
		Delay_sigma = [0]*M
		# breakpoint()
		# recording information of each buffer level

		# construct load capacitance list of each clock buffer
		for i in range(M):
			if i < M -1:
				Cl[i] = (self.WL[i]*self.c0 + self.f1[buffer_list[i+1]])*self.num[i]
			else:
				Cl[i] = (self.WL[i]*self.c0 + self.sink_cap)*self.num[i]
		slew_in = self.Slin
		# tranverse clock path
		for i in range(M):
			s = buffer_list[i]
			Slout[i] = self.f21[s](slew_in, Cl[i])		
			Slout_sigma[i] = self.f22[s](slew_in, Cl[i])
			Delay[i] = self.f32[s](slew_in, Cl[i])
			Delay_sigma[i] = self.f31[s](slew_in, Cl[i])
			
			slew_in = Slout[i]
			

		sigma_skew = (sum([u**2 for u in Delay_sigma]) + sum([self.rho_f*Delay_sigma[i]* Delay_sigma[i+1] for i in range(M-1)])) #ignore mathematical constant
		return sigma_skew + self.a*max(Slout_sigma) + self.b*max(Slout)
		# return sigma_skew 


	def objFitness(self):
		fitness = 1/float(self.computeObj())
		return fitness

