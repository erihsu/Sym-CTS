# This script is used to generate lookup table of clock buffer using Hspice.

# The lookup table considering input slew, output load and input slew polarity(rising or fall).
# Output slew, delay and their standard-variance(std) can be look-up from this table.

# The technology file under library/tech folder will be used as mosfet parameter file.

# After excuation, new buffer model and lookup table will be generated under library/spice and library/lib respectively.

import json
import os

import numpy as np

class genLut():

    def __init__(self,spice_file,buffer_index):
        self.global_include_path = "./smic40/l0040ll_v1p4_1r.lib" # mosfet parameter file path
        self.buffer_spice_path = "{}/library/spice/{}".format(os.getenv('SYMCTS'),spice_file) # buffer spice file path
        self.input_slew = []
        self.output_load = []
        self.buffer_index = buffer_index
        self.voltage = 25
        self.time_unit = "ps"
        self.space_unit = "nm"
        self.capacitance_unit = "fF"
        self.mc_times = 1000
        self.sim_length = 50000
        self.sim_precision = 10
    
    def read_settings(self):
        with open('{}/utils/settings.json'.format(os.getenv('SYMCTS')),'r') as f:
            a_dict = json.loads(f.read())
            self.input_slew = a_dict["library"]["input_slew"]
            self.output_load = a_dict["library"]["output_load"]
            self.voltage = a_dict["library"]["voltage"]
            self.time_unit = a_dict["unit"]["time"]
            self.space_unit = a_dict["unit"]["space"]
            self.capacitance_unit = a_dict["unit"]["capacitance"]

    def gen_global_include(self):
        output_str = ".lib \"" + str(self.global_include_path) + "\" mos_mc\n" + \
                     ".include \"" + str(self.buffer_spice_path) + "\"\n"
        return output_str

    def gen_options(self):
        output_str = ".Option SAMPLING_METHOD= SRS\n"
        return output_str

    def gen_parameter(self,slew,cap):
        output_str = ".param SLEW_I = {}".format(slew) + str(self.time_unit) + "\n" +\
                     ".param CAP_O = {}".format(cap) + str(self.capacitance_unit) + "\n" +\
                     ".param S_Voltage=" + str(self.voltage) + "\n"
        return output_str
    
    def gen_circuits(self):
        output_str = "x1 in out vdd buf" + str(self.buffer_index) + "\n" + \
                     "c1 out 0 CAP_O\n"
        return output_str

    # def gen_datablock(self):
        
    #     data_block_index = 0
    #     output_str = ".DATA LutIndex\n" +\
    #                   "Index SLEW_I CAP_O\n"
    #     for slew in self.input_slew:
    #         for capload in self.output_load:
    #             output_str += "{} {}{} {}{}\n".format(data_block_index,slew,self.time_unit,capload,self.capacitance_unit)
    #             data_block_index += 1
        
    #     output_str += ".ENDDATA\n"

    #     return output_str
    
    def gen_tran(self):
        output_str = ".tran {}{} {}{} SWEEP Monte = {}\n".format(self.sim_precision,self.time_unit,self.sim_length,self.time_unit,self.mc_times)
        return output_str

    def gen_measure(self,rise_or_fall="rise"):

        if rise_or_fall == "rise":
            output_str = ".measure TRAN delay TRIG v(in) VAL='S_Voltage/2' RISE=1 \n" +\
                                            "+TARG v(out) VAL='S_Voltage/2' RISE=1\n" +\
                          ".measure TRAN slew TRIG v(out) VAL='S_Voltage*0.3' RISE=1 \n" +\
                                            "+TARG v(out) VAL='S_Voltage*0.7' RISE=1 \n"
        elif rise_or_fall == "fall":
            output_str = ".measure TRAN delay TRIG v(in) VAL='S_Voltage/2' FALL=1 \n" +\
                                            "+TARG v(out) VAL='S_Voltage/2' FALL=1\n" +\
                         ".measure TRAN slew TRIG v(out) VAL='S_Voltage*0.7' FALL=1 \n" +\
                                            "+TARG v(out) VAL='S_Voltage*0.3' FALL=1 \n"
        
        return output_str


    def gen_source(self):
        output_str = "V0 vdd 0 DC=S_Voltage\n" +\
                     "vpulse in 0 pulse( v1 v2 td tr tf pw per )\n" +\
                     ".param v1=0v v2=S_Voltage td=5ns tr=SLEW_I " + "tf=SLEW_I " + "pw=20ns per=50ns\n" +\
                     ".IC v(out) = 0v\n"
        return output_str
    
    def gen_end(self):
        output_str = ".end"
        return output_str
    
    def write_spice(self,slew,cap):

        with open("{}/workspace/for_lut.sp".format(os.getenv('SYMCTS')),'w') as f:
            f.write("No Title\n")
            f.write(self.gen_global_include())
            f.write(self.gen_options())
            f.write(self.gen_parameter(slew,cap))
            f.write(self.gen_tran())
            f.write(self.gen_source())
            f.write(self.gen_circuits())
            f.write(self.gen_measure())
            f.write(self.gen_end())
        
    def launch_simulator(self):
        os.system("hspice for_lut.sp")
    
    def parse_mpp0(self):
        stamp = 49
        delay = 0 
        delay_std = 0
        slew = 0
        slew_std = 0
        
        with open("for_lut.mpp0","r") as f:
            
            for i,line in enumerate(f):
                if i == (stamp + 3):
                    delay = line.split()[1]
                    delay_std = line.split()[3]
                elif i == (stamp + 7):
                    slew = line.split()[1]
                    slew_std = line.split()[3]
        
        return delay,delay_std,slew,slew_std


    def gen_lut(self):
        shape = (len(self.input_slew),len(self.output_load))
        nominal_delay = np.zeros(shape=shape)
        std_delay = np.zeros(shape=shape)
        nominal_slew = np.zeros(shape=shape)
        std_slew = np.zeros(shape=shape)

        for i,slew in enumerate(self.input_slew):
            for j,cap in enumerate(self.output_load):
                self.write_spice(slew,cap)
                self.launch_simulator()
                nominal_delay[i,j],std_delay[i,j],nominal_slew[i,j],std_slew[i,j] = self.parse_mpp0()

        if os.path.exists("{}/library/lib/X{}".format(os.getenv('SYMCTS'),self.buffer_index)):
            os.system("rm {}/library/lib/X{}/*".format(os.getenv('SYMCTS'),self.buffer_index))
        else:
            os.mkdir("{}/library/lib/X{}".format(os.getenv('SYMCTS'),self.buffer_index))
        
        with open("{}/library/lib/X{}/lut.txt".format(os.getenv('SYMCTS'),self.buffer_index),'w') as f:
            f.write("delay(miu){}delay(sigma){}slew(miu){}slew(sigma){}input_slew{}output_cap\n".format(" "*10," "*10," "*10," "*10," "*5))
            for i,slew in enumerate(self.input_slew):
                for j,cap in enumerate(self.output_load):
                    f.write(str(nominal_delay[i,j])+" "+str(std_delay[i,j])+" "+str(nominal_slew[i,j])+" "+str(std_slew[i,j])+" "+str(slew)+" "+str(cap)+"\n")
            

def gen_spice(i):

    lut = genLut("buf{}.subckt".format(i),i)
    lut.read_settings()
    lut.gen_lut()

if __name__ == "__main__":
    for i in range(9):
        gen_spice(i)
        