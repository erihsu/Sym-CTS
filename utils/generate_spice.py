# This script is used to generate spice file of buffer
# the size of pmos and nmos is configured in buffer.json
# After exectuation, the spice file is generated under "../library/spice" folder

import json
import os

def generate_spice(lib_path,buffer_name,buffer_size,min_length):
    
    with open("{}/{}.subckt".format(lib_path,buffer_name),'w') as f:
        write_str = ".subckt " + str(buffer_name) + " in out vdd\n" +\
                    "mp1  tmp in  vdd vdd   pmos l={} w={}u\n".format(min_length,buffer_size[0]) +\
                    "mn1  tmp in  0   0     nmos l={} w={}u\n".format(min_length,buffer_size[1]) +\
                    "mp2  out tmp  vdd vdd   pmos l={} w={}u\n".format(min_length,buffer_size[0]) +\
                    "mn2  out tmp  0   0     nmos l={} w={}u\n".format(min_length,buffer_size[1]) +\
                    ".ends " + str(buffer_name) + "\n"
        
        f.write(write_str)

def generate_lib(lib_path):
    with open("buffer.json",'r') as f:
        a_dict = json.loads(f.read())
        buffers = a_dict['buffers']
        min_length = a_dict['length']
        for key,value in buffers.items():
            generate_spice(lib_path,key,value,min_length)




if __name__ == "__main__":
    lib_path = "../library/spice"
    # os.remove("{}/*".format(lib_path))
    generate_lib(lib_path)