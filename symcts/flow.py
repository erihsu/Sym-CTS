from ga import geneticAlgorithm
from construction import topology
from partition import partition
import time

start = time.time()
# cts = symmtric_cts()
division = partition()
division.partition()
cts = topology()
cts.loadSinks(division.sinks,division.num_branchs)
# Step 1: generate symmetric topology
cts.construct()
print(str(cts.num_branchs))
# Step 2: buffer sizing with GA
buffer_lib = [0,1,2,3,4]
branch_level = len(cts.num_branchs) 
buffer_lib_size = len(buffer_lib)

geneticAlgorithm(buffer_lib_size=buffer_lib_size ,branch_level=branch_level ,popSize=50, eliteSize=10, mutationRate=0.1, generations=30)
cts.buffering()

# Step 3: export netlist of clock tree
cts.exportNetlist()

print("time used:{}".format(time.time()-start))


