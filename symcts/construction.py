import numpy as np
import os
import json
from partition import partition
from merge import merge,get_seg_length
from point import Sink, M_Point,Point
from buffer import candidate,clk_buffer
from wire import wire

class topology():

    def __init__(self):
        self.sinks = []
        self.nodes = []
        self.wires = []
        self.wirelength = []
        self.candidates = []
        self.buffers = []
        self.num_branchs = []
        self.num_sinks = 0

    def loadSinks(self,sinks,num_branchs):
        self.sinks = sinks
        self.num_branchs = num_branchs[::-1]
        self.num_sinks = len(self.sinks)

    def computeTotalWL(self):
        total_wirelength = 0
        for a_wire in self.wires:
            total_wirelength += a_wire.getLength()
        return total_wirelength

    def computeTotalBufferArea(self):
        total_area = 0
        buffer_area_list = [] #in um^2
        with open('{}/utils/buffer.json'.format(os.getenv('SYMCTS')),'r') as f:
            a_dict = json.loads(f.read())
            lib_size = a_dict['buffer_num']
            for i in range(lib_size):
                buffer_area_list.append(a_dict['buffers']['buf{}'.format(i)]['height']*a_dict['buffers']['buf{}'.format(i)]['width'])
            
        for a_buffer in self.buffers:
            total_area += buffer_area_list[a_buffer.get_id()]
        
        return total_area


    def hieraMerge(self):
        # merge in bottom-up order
        branchs = self.num_branchs[::-1]

        l_branch = len(branchs)
        merge_times = len(self.sinks)
        merged_points = []
        for i,branch in enumerate(branchs):
            seg_length = []
            candidate = []
            if i == 0:
                # merge sinks
                merge_times /= branch
                points = sorted(self.sinks,key=lambda u :u.get_gid()[-2])

                for j in range(int(merge_times)):
                    seg_length.append(get_seg_length(points[branch*j:branch*(j+1)]))

                target_seg_length = max(seg_length)
                self.wirelength.append(target_seg_length)

                for j in range(int(merge_times)):
                    merged_point,nodes,wires = merge(points[branch*j:branch*(j+1)],target_seg_length)
                    self.nodes.extend(nodes)
                    self.nodes.append(merged_point)
                    self.wires.extend(wires)

                    new_point,candidate_buffer = self.candidateBuffer(merged_point)
                    candidate.append(candidate_buffer)
                    self.nodes.append(new_point)
                    merged_points.append(new_point)
                self.candidates.append(candidate)

            elif i < (l_branch - 1):
                # merge sub-level points
                new_merged_points = []
                merge_times /= branch
                points = sorted(merged_points,key=lambda point :point.get_gid()[-2-i])

                for j in range(int(merge_times)):
                    seg_length.append(get_seg_length(points[branch*j:branch*(j+1)]))

                target_seg_length = max(seg_length)
                self.wirelength.append(target_seg_length)

                for j in range(int(merge_times)):
                    merged_point,nodes,wires = merge(points[branch*j:branch*(j+1)],target_seg_length)
                    self.nodes.extend(nodes)
                    self.nodes.append(merged_point)
                    self.wires.extend(wires)

                    new_point,candidate_buffer = self.candidateBuffer(merged_point)
                    candidate.append(candidate_buffer)
                    self.nodes.append(new_point)
                    new_merged_points.append(new_point)

                self.candidates.append(candidate)
                merged_points = new_merged_points

            else:
                # merge to get clock tree root point
                target_seg_length = get_seg_length(merged_points)
                self.wirelength.append(target_seg_length)
                root,nodes,wires = merge(merged_points,target_seg_length)
                self.nodes.extend(nodes)
                self.nodes.append(root)
                self.wires.extend(wires)
                new_root,candidate_buffer = self.candidateBuffer(root)
                self.nodes.append(new_root)
                self.candidates.append([candidate_buffer])

                # link root to sourcenode at (0,0)
                self.wires.append(wire(Point(0,0),new_root))
         
        self.wirelength.append(root.location.real+root.location.imag)
        # reverse order to top-down
        self.wirelength = self.wirelength[::-1]

    def gen_clockpath(self):
        # used to generate "clockpath.txt" from generated symmetric clock tree topology 
        # the "clockpath.txt" template like:
        #5   # clock tree level
        #72  # sink number
        #3   # branch number of clock path 
        #3   # ...
        #2   # ...
        #2   # ...
        #2   # ...
        #40  # wire length between parent-child nodes(nm)
        #50  # ...
        #55  # ...
        #44  # ...
        #23  # ...
        #32  # ...
        #55  # ...
        #70  # ...

        with open("{}/symcts/clockpath.txt".format(os.getenv('SYMCTS')),'w') as f:
            f.write(str(len(self.num_branchs)) + "\n")
            f.write(str(self.num_sinks) + "\n")
            for i in range(len(self.num_branchs)):
                f.write(str(self.num_branchs[i]) + "\n")
            for i in range(len(self.wirelength)):
                f.write(str(self.wirelength[i]) + "\n")

    def construct(self):
        self.hieraMerge()
        self.gen_clockpath()

    def candidateBuffer(self,insert_point):

        new_point = M_Point(location=insert_point.location)
        new_point.set_gid(insert_point.get_gid())
        candicate = candidate(new_point,insert_point)
        return new_point,candicate

    def buffering(self):

        buffer_type = []

        with open("{}/symcts/solution.txt".format(os.getenv('SYMCTS')),'r') as f:
            for i in range(len(self.num_branchs)):
                buffer_type.append(int(f.readline()))

        buffer_type.reverse()

        # wrap node id from "num_sinks+1"
        for i in range(len(self.nodes)):
            self.nodes[i].set_id(self.num_sinks+i+1)

        for i,candidate in enumerate(self.candidates):
            for a_candidate in candidate:
                startpoint = a_candidate.startpoint
                endpoint   = a_candidate.endpoint
                # considering non-buffering branch
                if buffer_type[i] == 0:
                    #self.wires.append(a_candidate.changeToWire())
                    self.removeMergePoint(startpoint,endpoint)
                else:
                    self.buffers.append(clk_buffer(startpoint,endpoint,buffer_type[i]-1))
    
    def removeMergePoint(self,startpoint,endpoint):
        own_end_point = False
        own_start_point = False
        wire_list = self.wires
        for a_wire in self.wires:
            if a_wire.startpoint == endpoint or a_wire.endpoint == startpoint:
                if a_wire.startpoint == endpoint:
                    own_end_point = True
                    new_endpoint = a_wire.endpoint
                    wire_list.remove(a_wire)
                else:
                    own_start_point = True
                    new_startpoint = a_wire.startpoint
                    wire_list.remove(a_wire)
                if own_end_point and own_start_point:
                    wire_list.append(wire(new_startpoint,new_endpoint))
                    own_end_point = False

        self.wires = wire_list
                
    def exportNetlist(self):
        # # #
        # write out clock tree netlist. the format keep same with ispd2009 output result for evaluation.
        # # #
        with open('{}/evaluation/output/result'.format(os.getenv('SYMCTS')),'w') as f:
        
            f.write("sourcenode 0 0\n")

            # write out merge point location information
            f.write("num node {}\n".format(len(self.nodes)))
            for i,node in enumerate(self.nodes):
                f.write("{} {} {}\n".format(node.get_id(),int(node.location.real),int(node.location.imag)))

            # write out sinknode information
            f.write("num sinknode {}\n".format(self.num_sinks))
            for i in range(self.num_sinks):
                f.write("{} {}\n".format(i+1,i+1))

            # write out wire information
            # considering connection between sourcenode and clock root node
            f.write("num wire {}\n".format(len(self.wires)))
            for i,wire in enumerate(self.wires):
                f.write("{} {} 0\n".format(wire.endpoint.get_id(),wire.startpoint.get_id()))

            # write out buffer information
            f.write("num buffer {}\n".format(len(self.buffers)))
            for a_buffer in self.buffers:
                f.write("{} {} {}\n".format(a_buffer.startpoint.get_id(),a_buffer.endpoint.get_id(),str(a_buffer.buffer_type)))
        
        # # #
        # write out json file for evaluation
        # # #

        with open('{}/evaluation/output/watchpoint.json'.format(os.getenv('SYMCTS')),'w') as f:
            watch_for_sinks = [u.get_id() for u in self.sinks if u.label == "real"]
            watch_for_nodes = [u.get_id() for u in self.nodes] + watch_for_sinks
            a_dict = {"sink":watch_for_sinks,"node":watch_for_nodes}
            json.dump(a_dict,f)
        
    def exportStatistics(self):
        with open('{}/evaluation/output/statistics.txt'.format(os.getenv('SYMCTS')),'w') as f:
            f.write("Total wirelength: {}um\n".format(self.computeTotalWL()/1000))
            f.write("Buffer Area: {}um^2\n".format(self.computeTotalBufferArea()))

            


