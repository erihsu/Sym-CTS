# -*- coding: utf-8 -*-
# @Author: mac
# @Date:   2019-11-02 09:54:23
# @Last Modified by:   eirc
# @Last Modified time: 2019-12-29 15:31:13

from scipy import interpolate
import numpy as np 
import os 
import json

def readindex(file="../utils/settings.json"):
	# read input_slew and capacitance_load index from indices.txt
	with open(file,'r') as f:
		a_dict = json.loads(f.read())
		input_slew = a_dict["library"]["input_slew"]
		output_load = a_dict["library"]["output_load"]
	return input_slew, output_load

def readlut(bufsize,filepath,option='rise'):
	# assume lut keep 7x7 shape
	delay_lut = np.zeros((7,7,2,bufsize))
	slew_lut  = np.zeros((7,7,2,bufsize))
	power_lut = np.zeros((7,7,bufsize))
	for s in range(bufsize):
		with open("{}/X{}/lut_{}.txt".format(filepath,s+1,option),'r') as f:
			# skip first line
			f.readline()
			# input_slew sweep loop
			for i in range(7):
				# output_cap sweep loop 
				for j in range(7):
					data = f.readline().split(" ")
					delay_lut[i,j,0,s] = float(data[0])*1e12 # mean value of delay, convert to ps
					delay_lut[i,j,1,s] = float(data[1])*1e12 # standard deviation of delay, convert to ps
					slew_lut[i,j,0,s]  = float(data[2])*1e12 # mean value of output slew, convert to ps
					slew_lut[i,j,1,s]  = float(data[3])*1e12 # standard deviation of output slew, convert to ps
					power_lut[i,j,s]   = float(data[4])*1e12 # power dissipation, convert to ps
	return delay_lut,slew_lut,power_lut

def init_Lut(lut,x,y,bufsize):
	model = []
	for s in range(bufsize):
		# lut model for a specific size
		# using cubic interpolate 
		model_s = interpolate.interp2d(x, y, lut[:,:,s],kind='cubic')
		model.append(model_s)
	return model


def load_lut(bufsize,filepath="../library/lib"):
	if not os.path.exists(filepath):
		print("file path not exist !")
	else:
		DLut_r,SLut_r,PLut_r = readlut(bufsize,filepath,'rise')
		DLut_f,SLut_f,PLut_f = readlut(bufsize,filepath,'fall')
	# delay lut.
	DLut = [DLut_r[:,:,0,:],DLut_r[:,:,1,:],DLut_f[:,:,0,:],DLut_f[:,:,1,:]]
	# output slew lut
	SLut = [SLut_r[:,:,0,:],SLut_r[:,:,1,:],SLut_f[:,:,0,:],SLut_f[:,:,1,:]]
	# power dissipation lut
	PLut = [PLut_r,PLut_f]
	return DLut, SLut, PLut 

def initialize(bufsize):
	DModel = []
	SModel = []
	PModel = []
	input_slew_index,output_cap_index = readindex()
	Dlut,Slut,Plut = load_lut(bufsize)
	for lut in Dlut:
		DModel.append(init_Lut(lut,input_slew_index,output_cap_index,bufsize))
	for lut in Slut:
		SModel.append(init_Lut(lut,input_slew_index,output_cap_index,bufsize))
	for lut in Plut:
		PModel.append(init_Lut(lut,input_slew_index,output_cap_index,bufsize))
	return DModel,SModel,PModel

def main():
	pass

if __name__ == '__main__':
	main()






