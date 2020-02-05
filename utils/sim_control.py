# This script is used to generate lookup table of clock buffer using Hspice.

# The lookup table considering input slew, output load and input slew polarity(rising or fall).
# Output slew, delay and their standard-variance(std) can be look-up from this table.

# The technology file under library/tech folder will be used as mosfet parameter file.

# After excuation, new buffer model and lookup table will be generated under library/spice and library/lib respectively.

import json


class genLut():

    def __init__(self,spice_file,buffer_index):
        self.global_include_path = "." # mosfet parameter file path
        self.buffer_spice_path = spice_file # buffer spice file path
        self.input_slew = []
        self.output_load = []
        self.buffer_index = buffer_index
        self.voltage = 25
        self.time_unit = "ps"
        self.space_unit = "nm"
        self.capacitance_unit = "fF"
        self.mc_times = 1000
        self.sim_length = 5000
        self.sim_precision = 10
    
    def read_settings(self,file_path='settings.json'):
        with open(file_path,'r') as f:
            a_dict = json.loads(f.read())
            self.input_slew = a_dict["library"]["input_slew"]
            self.output_load = a_dict["library"]["output_load"]
            self.voltage = a_dict["library"]["voltage"]
            self.time_unit = a_dict["unit"]["time"]
            self.space_unit = a_dict["unit"]["space"]
            self.capacitance_unit = a_dict["unit"]["capacitance"]

    def gen_global_include(self):
        output_str = ".include " + str(self.global_include_path) + "\n" + \
                     ".include " + str(self.buffer_spice_path) + "\n"
        return output_str

    def gen_parameter(self):
        output_str = ".param SLEW_I=0" + str(self.time_unit) + "\n" +\
                     ".param CAP_O =0" + str(self.capacitance_unit) + "\n" +\
                     ".param S_Voltage=" + str(self.voltage) + "\n"
        return output_str
    
    def gen_circuits(self):
        output_str = "x1 in out vdd buf" + str(self.buffer_index) + "\n" + \
                     "c1 out 0 CAP_O\n"
        return output_str

    def gen_datablock(self):
        
        data_block_index = 0
        output_str = ".DATA LutIndex\n" +\
                      "SLEW_I CAP_O\n"
        for slew in self.input_slew:
            for capload in self.output_load:
                output += "{} {} {}\n".format(data_block_index,slew,capload)
                data_block_index += 1
        
        output_str += ".ENDDATA\n"

        return output_str
    
    def gen_tran(self):
        output_str = ".tran {} {} SWEEP DATA=LutIndex Monte = {}\n".format(self.sim_precision,self.sim_length,self.mc_times)
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
                     ".param v1=0v v2=S_Voltage td=5ns tr=SLEW_I" + str(self.time_unit) + "tf=SLEW_I" + str(self.time_unit) + "pw=20ns per=50ns\n" +\
                     ".IC v(out) = 0v\n"
        return output_str
    
    def write_spice(self,filename="../workspace/for_lut.sp"):

        with open(filename,'w') as f:
            f.write("No Title\n")
            f.write(self.gen_global_include())
            f.write(self.gen_parameter())
            f.write(self.gen_tran())
            f.write(self.gen_source())
            f.write(self.gen_circuits())
            f.write(self.gen_datablock())
            f.write(self.gen_measure())

def gen_spice():

    with open("buffer.json",'r') as f:
        a_dict = json.loads(f.read())
        buffer_lib_size = a_dict["buffer_num"]
    for buffer_index in range(buffer_lib_size):
        buffer_spice_file = "../library/spice/buf{}.subckt".format(buffer_index)
        lut = genLut(buffer_spice_file,buffer_index)
        lut.write_spice()

if __name__ == "__main__":
    gen_spice()
        