import cmath
import numpy as np
import os
from point import Sink

class partition():

    def __init__(self,circuits_name):
        self.circuits = circuits_name
        self.sinks = []
        self.num_real_sinks = 0
        self.num_pseudo_sinks = 0
        self.num_sinks = 0
        self.num_branchs = []

    def bnp(self):
        n = self.num_sinks
        while n > 1:
            for i in range(2, int(n+1)):
                if n % i == 0:
                    n /= i
                    self.num_branchs.append(i)
                    break

    def readSinks(self):

        with open("{}/circuits/ex_ispd/{}".format(os.getenv('SYMCTS'),self.circuits),'r') as f:       
            # skip first and second Line
            f.readline()
            f.readline()
            self.num_real_sinks = int(f.readline().split(" ")[2])
            
        with open("{}/evaluation/input/{}".format(os.getenv('SYMCTS'),self.circuits),'r') as f:

            # skip first and second Line
            f.readline()
            f.readline()

            self.num_sinks = int(f.readline().split(" ")[2])
            self.num_pseudo_sinks = self.num_sinks - self.num_real_sinks

            for i in range(self.num_sinks):
                data = f.readline().split(" ")
                location = complex(float(data[1]), float(data[2]))

                if i < self.num_real_sinks:
                    s = Sink(location,label='real')
                else:
                    s = Sink(location,label='pseudo')

                s.set_id(i+1)
                self.sinks.append(s)                           


    def find_center(self,location):
        # find geometry center
        xs = [point.real for point in location]
        ys = [point.imag for point in location]
        center = complex(sum(xs)/len(location),sum(ys)/len(location))
        return center

    def get_angle_of_complex(self,complex_number):

        if complex_number.imag < 0:
            return abs(cmath.phase(complex_number)) + cmath.pi
        else:
            return cmath.phase(complex_number)

    def find_group(self,points,group_id,group_number):

        result_part = []
        location = [u.location for u in points]
        center = self.find_center(location)    
        for point in points:
            point.relative_location = point.location - center    

        # sorted points by relative location 
        points = sorted(points,key=lambda point:self.get_angle_of_complex(point.relative_location))
        sorted_location = [u.location for u in points]
        part_length = int(len(points)/group_number)
        min_len = np.inf
        final_start_cut = 0
        
        for start_cut in range(part_length):
            distance = []
            for i in range(group_number):
                if i == 0:
                    part = sorted_location[0:start_cut] + sorted_location[start_cut+part_length:]
                    estimate_distance = np.array(part) - center
                    distance.extend(estimate_distance.tolist())
                else:
                    step_length = part_length*(i-1)
                    part = sorted_location[start_cut+step_length:start_cut+step_length+part_length]
                    estimate_distance = np.array(part) - center
                    distance.extend(estimate_distance.tolist())
            # pdb.set_trace()
            u = np.array(distance).max()
            if u < min_len:
                final_start_cut = start_cut
                min_len = u
        
        # partition
        for i in range(group_number):
            if i == 0:
                a_part = points[0:final_start_cut] + points[final_start_cut+part_length:]
            else:
                step_length = part_length*(i-1)
                a_part = points[final_start_cut+step_length:final_start_cut+part_length+step_length]
            
            for p in a_part:
                p.append_gid(group_id+i)

            result_part.append(a_part)
        
        return result_part

    def cake_cut(self,points,cls_num,group_id=0):

        grouped = self.find_group(points,group_id,cls_num)

        return grouped

    def division(self):

        for i,cls_num in enumerate(self.num_branchs):
            if i == 0:
                grouped = self.cake_cut(self.sinks,cls_num)
            else:
                new_points = []
                for j,points in enumerate(grouped):
                    new_grouped = self.cake_cut(points,cls_num,cls_num*j)
                    new_points = new_points + new_grouped
                grouped = new_points
    


    def partition(self):
        self.readSinks()
        self.bnp()
        self.division()



        

    
