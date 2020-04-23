import cmath
import numpy as np
import os

from point import Sink

class partition():

    def __init__(self):
        self.sinks = []
        self.num_real_sinks = 0
        self.num_pseudo_sinks = 0
        self.num_sinks = 0
        self.num_branchs = []

    def bnp(self):
        # n represent number of subtree needed in the design considering 2-3 mixed branch planning
        n = self.num_sinks
        while n > 1:
            for i in range(2, int(n+1)):
                if n % i == 0:
                    n /= i
                    self.num_branchs.append(i)
                    break

    def readSinks(self):

        with open("{}/circuits/ex_ispd/mem_ctrl".format(os.getenv('SYMCTS')),'r') as f:       
            # skip first and second Line
            f.readline()
            f.readline()
            self.num_real_sinks = int(f.readline().split(" ")[2])
            
        with open("{}/evaluation/input/mem_ctrl".format(os.getenv('SYMCTS')),'r') as f:

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

    def find_two_group(self,points,group_id):

        location = [u.location for u in points]
        center = self.find_center(location)

        for point in points:
            point.relative_location = point.location - center

        # sorted points by relative location 
        points = sorted(points,key=lambda point:self.get_angle_of_complex(point.relative_location))

        sorted_location = [u.location for u in points]

        part_length = int(len(points)/2)
        min_len = np.inf
        final_start_cut = 0
        # find final start cut when minimizing the cost
        for start_cut in range(part_length):
            # len(part1) == len(part2)
            part1 = sorted_location[start_cut:start_cut+part_length]
            part2 = sorted_location[0:start_cut] + sorted_location[start_cut+part_length:]
            center1 = self.find_center(part1)
            center2 = self.find_center(part2)
            sub2_dis1 = np.array(part1) - center1
            sub2_dis2 = np.array(part2) - center2
            sub1_dis1 = np.array(center1) - center
            sub1_dis2 = np.array(center2) - center 
            total_dis1 = np.abs(sub2_dis1) + np.abs(sub1_dis1)
            total_dis2 = np.abs(sub2_dis2) + np.abs(sub1_dis2)

            total_dis  = np.concatenate((total_dis1,total_dis2))
            u = total_dis.std()
            # compute max distance in a meshgrid (max distance between part1 and part2)
            # m1,n1 = np.meshgrid(part1,part1)
            # m2,n2 = np.meshgrid(part2,part2)
            # # cost function
            # u = (abs(m1-n1).max() - abs(m1-n1).min())+(abs(m2-n2).max() - abs(m2-n2).min())

            if u < min_len:
                final_start_cut = start_cut
                min_len = u
        # partition
        part1 = points[final_start_cut:final_start_cut+part_length]
        part2 = points[0:final_start_cut] + points[final_start_cut+part_length:]
        for p1 in part1:
            p1.append_gid(group_id)
        for p2 in part2:
            p2.append_gid(group_id+1)
        return [part1, part2]

    def find_three_group(self,points,group_id):

        location = [u.location for u in points]
        center = self.find_center(location)

        for point in points:
            point.relative_location = point.location - center

        points = sorted(points,key=lambda point:self.get_angle_of_complex(point.relative_location))

        sorted_location = [u.location for u in points]

        part_length = int(len(points)/2)
        min_len = np.inf
        final_start_cut = 0

        part_length = int(len(location)/3)
        min_len = np.inf
        final_start_cut = 0
        # find final start cut when minimizing the cost
        for start_cut in range(part_length):
            # len(part1) == len(part2) == len(part3)
            part1 = sorted_location[start_cut:start_cut+part_length]
            part2 = sorted_location[start_cut+part_length:start_cut+2*part_length]
            part3 = sorted_location[0:start_cut] + sorted_location[start_cut+2*part_length:]
            center1 = self.find_center(part1)
            center2 = self.find_center(part2)
            center3 = self.find_center(part3)
            sub2_dis1 = np.array(part1) - center1
            sub2_dis2 = np.array(part2) - center2
            sub2_dis3 = np.array(part3) - center3 
            sub1_dis1 = np.array(center1) - center
            sub1_dis2 = np.array(center2) - center 
            sub1_dis3 = np.array(center3) - center
            total_dis1 = np.abs(sub2_dis1) + np.abs(sub1_dis1)
            total_dis2 = np.abs(sub2_dis2) + np.abs(sub1_dis2)
            total_dis3 = np.abs(sub2_dis3) + np.abs(sub1_dis3)

            total_dis  = np.concatenate((total_dis1,total_dis2,total_dis3))
            u  = total_dis.std()
            # m1,n1 = np.meshgrid(part1,part1)
            # m2,n2 = np.meshgrid(part2,part2)
            # m3,n3 = np.meshgrid(part3,part3)
            # # cost function
            # u = abs(m1-n1).max() + abs(m2-n2).max() + abs(m3-n3).max() - abs(m1-n1).min() - abs(m2-n2).min() - abs(m3-n3).min()

            if u < min_len:
                final_start_cut = start_cut
                min_len = u
        # partition
        part1 = points[final_start_cut:final_start_cut+part_length]
        part2 = points[final_start_cut+part_length:final_start_cut+2*part_length]
        part3 = points[0:final_start_cut] + points[final_start_cut+2*part_length:]
        for p1 in part1:
            p1.append_gid(group_id)
        for p2 in part2:
            p2.append_gid(group_id+1)
        for p3 in part3:
            p3.append_gid(group_id+2)
        return [part1, part2, part3]

    def cake_cut(self,points,cls_num,group_id=0):
        # the cls_num is limited to 2 or 3
        if not (cls_num == 2 or cls_num == 3):
            print("branch number except 2 or 3 is not supported")
            exit(1)
        elif cls_num == 2:
            grouped = self.find_two_group(points,group_id)
        else:
            grouped = self.find_three_group(points,group_id)

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



        

    
