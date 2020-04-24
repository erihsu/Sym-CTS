from ga import geneticAlgorithm
from construction import topology
from partition import partition
import time
import os 

start = time.time()

division = partition("usb_phy")
division.partition()
cts = topology()
cts.loadSinks(division.sinks,division.num_branchs)
# Step 1: generate symmetric topology
cts.construct()
print(str(cts.num_branchs))
# Step 2: buffer sizing with GA
branch_level = len(cts.num_branchs) 
buffer_lib_size = 9
isigma=osigma=0
istrategy=ostrategy=[]
isigma,osigma,istrategy,ostrategy = geneticAlgorithm(buffer_lib_size=buffer_lib_size ,branch_level=branch_level ,popSize=300, eliteSize=30, mutationRate=0.15, generations=30)
cts.buffering()

# Step 3: export netlist of clock tree
cts.exportNetlist()
# export wire length and buffer area statistics
cts.exportStatistics()
# write out runtime and estimate skew_sigma
used_time = time.time()-start
with open('{}/evaluation/output/other_info.txt'.format(os.getenv('SYMCTS')),'w') as f:
    f.write("estimate skew sigma:\n")
    f.write("before optimize:{}  after optimize:{}\n".format(isigma,osigma))
    f.write("solution:\n")
    f.write("before optimize:{}  after optimize:{}\n".format(str(istrategy),str(ostrategy)))
    f.write("runtime:{}s\n".format(used_time))



