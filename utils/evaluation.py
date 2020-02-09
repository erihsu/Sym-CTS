# -*- coding: utf-8 -*-
# @Author: eirc
# @Date:   2020-01-13 16:32:22
# @Last Modified by:   eirc
# @Last Modified time: 2020-01-15 20:56:01

import os
import json
import numpy as np

class evaluation:

    def __init__(self):
        self.skew = [0,0] # skew mean and skew sigma
        self.slew = [0,0] # max slew mean and max slew sigma
        self.voltage = 0.6 #v
        self.input_slew = 0
        self.max_path = 0 # use sink node to represent path
        self.min_path = 0 # use sink node to represent path
        self.max_slew_node = 0
        self.sinks = []
        self.nodes = []
        self.rise_or_fall = "rise"
        self.mc_times = 100
        self.time_unit = "ps"
        self.capacitance_unit = "fF"
        self.space_unit = "um"
        self.sim_length = 100000
        self.sim_precision = 10

    def read_settings(self):
        with open('{}/utils/settings.json'.format(os.getenv('SYMCTS')),'r') as f:
            a_dict = json.loads(f.read())
            self.mc_times = a_dict["evaluation"]["mc_times"]
            self.voltage = a_dict["evaluation"]["voltage"]
            self.rise_or_fall = a_dict["evaluation"]["rise_or_fall"]
            self.time_unit = a_dict["unit"]["time"]
            self.space_unit = a_dict["unit"]["space"]
            self.capacitance_unit = a_dict["unit"]["capacitance"]
            self.input_slew = a_dict["evaluation"]["initial_input_slew"]
        
        with open('{}/evaluation/output/watchpoint.json'.format(os.getenv('SYMCTS')),'r') as f:
            a_dict = json.loads(f.read())
            self.sinks = a_dict['sink']
            self.nodes = a_dict['node']



    def gen_common(self):
        output_str = "*simple title\n" + \
                     ".include \"45nm_LP.pm\"\n" +\
                     ".include \"result.spice\"\n" +\
                     ".param S_Voltage={}v\n".format(self.voltage) +\
                     ".param SLEW_I={}{}\n".format(self.input_slew,self.time_unit) +\
                     ".option MEASFORM=3\n"        
        return output_str

    def gen_source(self):
        output_str = "V0 vdd 0 DC=S_Voltage\n" +\
                     "vpulse n0 0 pulse( v1 v2 td tr tf pw per )\n" +\
                     ".param v1=0v v2=S_Voltage td=5ns tr=SLEW_I " + "tf=SLEW_I " + "pw=20ns per=50ns\n"
        return output_str

    def gen_stage1_tran(self):
        output_str = ".tran {}{} {}{}\n".format(self.sim_precision,self.time_unit,self.sim_length,self.time_unit)
        return output_str
    
    def gen_stage2_tran(self):
        output_str = ".tran {}{} {}{} MONTE={}\n".format(self.sim_precision,self.time_unit,self.sim_length,self.time_unit,self.mc_times)
        return output_str

    def gen_stage1_measure(self):
        output_str = ""

        for sink in self.sinks:
            output_str += ".IC v(n{}) = 0v\n".format(sink)

        for node in self.nodes:
            output_str += ".IC v(n{}) = 0v\n".format(node)

        if self.rise_or_fall == "rise":
            for i,sink in enumerate(self.sinks):
                output_str += ".measure TRAN delay{} TRIG v(n0) VAL='S_Voltage/2' RISE=1 TARG v(n{}) VAL='S_Voltage/2' RISE=1\n".format(i,sink)
            for i,node in enumerate(self.nodes):
                output_str += ".measure TRAN slew{} TRIG v(n{}) VAL='S_Voltage*0.3' RISE=1 TARG v(n{}) VAL='S_Voltage*0.7' RISE=1\n".format(i,node,node)

        else:
            for i,sink in enumerate(self.sinks):
                output_str += ".measure TRAN delay{} TRIG v(n0) VAL='S_Voltage/2' FALL=1 TARG v(n{}) VAL='S_Voltage/2' FALL=1\n".format(i,sink)
            for i,node in enumerate(self.nodes):
                output_str += ".measure TRAN slew{} TRIG v(n{}) VAL='S_Voltage*0.7' FALL=1 TARG v(n{}) VAL='S_Voltage*0.3' FALL=1\n".format(i,node,node)
        
        return output_str

    def gen_stage2_measure(self):
        output_str = ""

        output_str += ".IC v(n{}) = 0v\n".format(self.max_path)
        output_str += ".IC v(n{}) = 0v\n".format(self.min_path)
        output_str += ".IC v(n{}) = 0v\n".format(self.max_slew_node)
        
        if self.rise_or_fall == "rise":
            output_str += ".measure TRAN skew TRIG v(n{}) VAL='S_Voltage/2' RISE=1 TARG v(n{}) VAL='S_Voltage/2' RISE=1\n".format(self.min_path,self.max_path)
            output_str += ".measure TRAN max_slew TRIG v(n{}) VAL='S_Voltage*0.3' RISE=1 TARG v(n{}) VAL='S_Voltage*0.7' RISE=1\n".format(self.max_slew_node,self.max_slew_node)
        else:
            output_str += ".measure TRAN skew TRIG v(n{}) VAL='S_Voltage/2' FALL=1 TARG v(n{}) VAL='S_Voltage/2' FALL=1\n".format(self.min_path,self.max_path)
            output_str += ".measure TRAN max_slew TRIG v(n{}) VAL='S_Voltage*0.7' FALL=1 TARG v(n{}) VAL='S_Voltage*0.3' FALL=1\n".format(self.max_slew_node,self.max_slew_node)
        return output_str
        
    def gen_end(self):
        output_str = ".end"
        return output_str

    def generate_stage1_control_file(self):
        with open("{}/workspace/sim_control.sp".format(os.getenv('SYMCTS')),'w') as f:
            f.write(self.gen_common())
            f.write(self.gen_source())
            f.write(self.gen_stage1_tran())
            f.write(self.gen_stage1_measure())
            f.write(self.gen_end())

    def launch_simulator(self):
        os.system("hspice sim_control.sp")
    
    def parse_from_mt(self):
        delay_num = len(self.sinks)
        slew_num = len(self.nodes)
        with open("{}/workspace/sim_control.mt0.csv".format(os.getenv('SYMCTS')),'r') as f:
            delay_and_slew = np.genfromtxt(f,delimiter=',',skip_header=4)
        
        if np.isnan(np.min(delay_and_slew)):
            print("some nodes may be floating,please check netlist")
            exit(1)
        else:        
            delays = delay_and_slew[:delay_num]
            slews = delay_and_slew[delay_num:delay_num+slew_num]
            self.max_path = np.argmax(delays)
            self.min_path = np.argmin(delays)
            self.max_slew_node = np.argmax(slews)
        
    def generate_stage2_control_file(self):
        with open("{}/workspace/sim_control.sp".format(os.getenv('SYMCTS')),'w') as f:
            f.write(self.gen_common())
            f.write(self.gen_source())
            f.write(self.gen_stage2_tran())
            f.write(self.gen_stage2_measure())
            f.write(self.gen_end())        



    def get_statistics(self):

        skew = np.loadtxt("skew.log",dtype=float,usecols=2)
        # slew = np.loadtxt("max_slew.log",dtype=float,usecols=2)
        sskew = [np.mean(skew).astype(np.float32),np.std(skew).astype(np.float32)]
        # sslew = [np.mean(slew).astype(np.float32),np.std(slew).astype(np.float32)]
        return sskew
        


def main():
    u = evaluation()
    u.read_settings()
    u.generate_stage1_control_file()
    u.launch_simulator()
    u.parse_from_mt()
    u.generate_stage2_control_file()
    u.launch_simulator()
    u.get_statistics()


if __name__ == "__main__":
    main()



