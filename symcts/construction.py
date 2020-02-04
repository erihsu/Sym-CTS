import numpy as np
from partition import partition
from merge import merge,get_seg_length
from point import Sink, M_Point
from buffer import candidate,clk_buffer

class topology():

	def __init__(self):
		self.sinks = []
		self.nodes = []
		self.wires = []
		self.wirelength = []
		self.candidates = []
		self.wire_buffer = [] # wire that lang buffer
		self.buffers = []
		self.num_branchs = []
		self.num_sinks = 0

	def loadSinks(self,sinks,num_branchs):
		# initialze partition
		self.sinks = sinks
		self.num_branchs = num_branchs

		for i in range(len(self.sinks)):
			self.sinks[i].set_id(i+1)

		# real_sinks = [u for u in sinks if u.label=='real']
		self.num_sinks = len(self.sinks)

	def computeTotalWL(self):
		total_wirelength = 0
		wire_num = 1
		for i in range(len(self.num_branchs)):
			wire_num *= self.num_branchs[i]
			total_wirelength += wire_num*self.wirelength[i]
		return total_wirelength



	def hieraMerge(self):
		# merge in bottom-up order
		branchs = self.num_branchs[::-1]

		l_branch = len(branchs)
		merge_times = len(self.sinks)
		for i,branch in enumerate(branchs):
			seg_length = []
			candidate = []
			wire_buffer = []
			if i == 0:
				# merge sinks
				merged_points = []
				merge_times /= branch
				points = sorted(self.sinks,key=lambda sink :sink.get_gid()[-2])

				for j in range(int(merge_times)):
					seg_length.append(get_seg_length(points[branch*j:branch*(j+1)]))

				target_seg_length = max(seg_length)
				self.wirelength.append(target_seg_length)

				for j in range(int(merge_times)):
					merged_point,nodes,wires = merge(points[branch*j:branch*(j+1)],target_seg_length,branch)
					candidate_points,candidate_buffer = self.candidateBuffer(merged_point)
					candidate.append(candidate_buffer)
					merged_point = candidate_points[-1]
					self.nodes = self.nodes + candidate_points + nodes
					self.wires = self.wires + wires
					merged_points.append(merged_point)
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
					merged_point,nodes,wires = merge(points[branch*j:branch*(j+1)],target_seg_length,branch)
					candidate_points,candidate_buffer = self.candidateBuffer(merged_point)
					merged_point = candidate_points[-1]
					candidate.append(candidate_buffer)
					self.nodes = self.nodes + candidate_points + nodes
					self.wires = self.wires + wires
					new_merged_points.append(merged_point)

				self.candidates.append(candidate)
				merged_points = new_merged_points

			else:
				# merge to get clock tree root point
				target_seg_length = get_seg_length(merged_points)
				self.wirelength.append(target_seg_length)
				root,nodes,wires = merge(merged_points,target_seg_length,branch)
				candidate_points,candidate_buffer = self.candidateBuffer(root)
 
				self.nodes = self.nodes + candidate_points + nodes
				self.wires = self.wires + wires

				self.candidates.append(candidate)

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

		with open("clockpath.txt",'w') as f:
			f.write(str(len(self.num_branchs)) + "\n")
			f.write(str(self.num_sinks) + "\n")
			for i in range(len(self.num_branchs)):
				f.write(str(self.num_branchs[i]) + "\n")
			for i in range(len(self.wirelength)):
				f.write(str(self.wirelength[i]) + "\n")

	def construct(self):
		self.hieraMerge()
		print(self.computeTotalWL())
		self.gen_clockpath()

	def candidateBuffer(self,insert_point):

		new_point = M_Point(location=insert_point.location)
		new_point.set_gid(insert_point.get_gid())
		candicate = candidate(new_point,insert_point)
		return [insert_point,new_point],candicate

	def buffering(self,filename="solution.txt"):

		buffer_type = []

		with open(filename,'r') as f:
			for i in range(len(self.num_branchs)):
				buffer_type.append(int(f.readline()))

		buffer_type.reverse()

		for i in range(len(self.nodes)):
			self.nodes[i].set_id(self.num_sinks+i+1)

		for i,candidate in enumerate(self.candidates):
			for j,a_candidate in enumerate(candidate):
				startpoint = a_candidate.startpoint
				endpoint   = a_candidate.endpoint
				self.buffers.append(clk_buffer(startpoint,endpoint,buffer_type[i]))
				
	def exportNetlist(self,filename='result.txt'):
		# # #
	    # write out clock tree netlist. the format keep same with ispd2009 output result for evaluation.
	    # # #
	    with open(filename,'w') as f:
	    
	        f.write("sourcenode 0 0\n")

	        # write out merge point location information
	        f.write("num node {}\n".format(len(self.nodes)))
	        for i,node in enumerate(self.nodes):
	            f.write("{} {:.6f} {:.6f}\n".format(node.get_id(),node.location.real,node.location.imag))

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


