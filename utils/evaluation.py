# -*- coding: utf-8 -*-
# @Author: eirc
# @Date:   2020-01-13 16:32:22
# @Last Modified by:   eirc
# @Last Modified time: 2020-01-15 20:56:01

import os
import numpy as np

class evaluation:

	def __init__(self,sink_num,node_num):
		self.skew = [0,0] # skew mean and skew sigma
		self.slew = [0,0] # max slew mean and max slew sigma
		self.simulation_time = 50 #ns
		self.simulation_voltage = 0.6 #v
		self.max_path = 0 # use sink node to represent path
		self.min_path = 0 # use sink node to represent path
		self.max_slew_node = 0
		self.sink_num = sink_num
		self.node_num = node_num
		self.mc_times = 5


	def extract_min_max_path(self,file="delay.log"):
		delay = np.loadtxt(file,dtype=float,usecols=2)
		self.max_path = np.argmax(delay)
		self.min_path = np.argmin(delay)
		
	def extract_max_slew_node(self,file="slew.log"):
		slew = np.loadtxt(file,dtype=float,usecols=2)
		self.max_slew_node = np.argmax(slew) + 1


	def generate_control_file(self,destination1="delay.log",destination2="slew.log"):
		with open("sim_control.sp",'w') as f:
			f.write("*simple title\n")
			f.write(".control\n\tsource result.spice\n\tlet sink_num = {}\n\ttran 10p {}n\n"\
				.format(self.sink_num,self.simulation_time))
			# control for delay measurement
			for i in range(self.sink_num):
				f.write("\tmeas tran delay{} trig v(gin) val='0.5*vp' fall=1 targ v(n{}) val='0.5*vp' fall=1\n"\
					.format(i,i+1))
				f.write("\tprint delay{} >> ".format(i) + destination1 + "\n")

			# control for slew measurement
			for i in range(self.node_num):
				# f.write("\tmeas tran slew{} trig v(n{}) val='0.9*vp' fall=1 targ v(n{}) val='0.1*vp' fall=1\n"\
				# 	.format(i,i+1,i+1))
				f.write("\tmeas tran slew{} trig v(n{}) val='0.99' fall=1 targ v(n{}) val='0.11' fall=1\n"\
					.format(i,i+1,i+1))
				f.write("\tprint slew{} >> ".format(i) + destination2 + "\n")

			f.write("\tquit\n")
			f.write(".endc\n.end\n")

	def simulation_for_result(self):
		str1 = "\tdefine gauss(nom, var, sig) (nom + (nom*var)/sig * sgauss(0))\n\tdefine agauss(nom, avar, sig) (nom + avar/sig * sgauss(0))\n\
				\tlet n1vth0=@nmos[vth0]\n\tlet n1u0=@nmos[u0]\n\tlet n1tox=@nmos[toxref]\n\
				\tlet p1vth0=@pmos[vth0]\n\tlet p1u0=@pmos[u0]\n\tlet p1tox=@pmos[toxref]\n\
  				\tdowhile run <= mc_runs\n\t\tif run > 1\n\
  				\t\t\taltermod @nmos[vth0] = gauss(n1vth0, 0.05, 3)\n\t\t\taltermod @nmos[u0] = gauss(n1u0, 0.05, 3)\n\
      			\t\t\taltermod @nmos[toxref] = gauss(n1tox, 0.05, 3)\n\t\t\taltermod @pmos[vth0] = gauss(p1vth0, 0.05, 3)\n\
      			\t\t\taltermod @pmos[u0] = gauss(p1u0, 0.05, 3)\n\t\t\taltermod @pmos[toxref] = gauss(p1tox, 0.05, 3)\n\t\tend\n\
    			\t\tsave @xbuf[v] all\n"

		str2 = "\t\tdestroy all\n\t\tlet run = run + 1\n\tend\n\trusage\n\tquit\n.endc\n.end\n"

		with open("sim_control.sp",'w') as f:
			f.write("*simple title\n")
			f.write(".control\n\tlet mc_runs={}\n\tlet run = 1\n\tsource result.spice\n\tlet vp = {}\n\ttran 10p {}n\n"\
				.format(self.mc_times,self.simulation_voltage,self.simulation_time))
			f.write(str1)
			f.write("\t\ttran 10p {}n\n".format(self.simulation_time))
			f.write("\t\tmeas tran skew trig v(n{}) val=0.55 fall=1 targ v(n{}) val=0.55 fall=1\n".format(self.min_path,self.max_path))
			# f.write("\t\tmeas tran slew trig v(n{}) val=0.99 fall=1 targ v(n{}) val=0.11 fall=1\n".format(self.max_slew_node,self.max_slew_node))
			# f.write("\t\tprint skew >> skew.log\n\t\tprint slew >> max_slew.log\n")
			f.write("\t\tprint skew >> skew.log\n")
			f.write(str2)

	def launch_simulator(self):
		os.system("ngspice -b sim_control.sp")

	def clean_logs(self):
		os.system("rm *.log")

	def get_statistics(self):

		skew = np.loadtxt("skew.log",dtype=float,usecols=2)
		# slew = np.loadtxt("max_slew.log",dtype=float,usecols=2)
		sskew = [np.mean(skew).astype(np.float32),np.std(skew).astype(np.float32)]
		# sslew = [np.mean(slew).astype(np.float32),np.std(slew).astype(np.float32)]
		self.clean_logs()
		return sskew

	def get_result(self):
		self.generate_control_file()

		if os.path.exists("*.log"):
			self.clean_logs()

		self.launch_simulator()
		self.extract_min_max_path()
		# self.extract_max_slew_node()

		# if os.path.exists("*.log"):
		# 	self.clean_logs()

		self.simulation_for_result()
		self.launch_simulator()
		return self.get_statistics()


if __name__ == "__main__":
	main()



