import math
import random
import os
class convertion():

    def __init__(self):
        self.head = []
        self.sinks = []
        self.lines = []
        self.num_real_sinks = 0
        self.num_pseudo_sinks = 0
        self.num_sinks = 0
        self.minX = 0
        self.minY = 0
        self.maxX = 0
        self.maxY = 0

    def bnpPre(self):
        bnp_pre = []
        max_level = int(math.ceil(math.sqrt(self.num_real_sinks)))
        # # ensurance branch=2 and branch=3 can exist at the same time
        for i in range(1, max_level):
            for j in range(1, i):
                bnp_pre.append((2**j)*(3**(i-j)))

        bnp_pre = sorted(bnp_pre)
        # find the closed number to the sink_num in the bnp_pre list
        for i, number in enumerate(bnp_pre):
            if number >= self.num_real_sinks:
                self.num_sinks = number
                break
        self.num_pseudo_sinks = self.num_sinks - self.num_real_sinks

    def readOriginFile(self):

        with open("{}/circuits/ex_ispd/ispd09f11_small".format(os.getenv('SYMCTS')),'r') as f:
            area = f.readline()
            self.head.append(area)

            self.minX,self.minY,self.maxX,self.maxY = tuple(map(int,area.split(" ")))          
            # skip second Line
            source = f.readline()
            self.head.append(source)
            sink_info = f.readline()
            self.head.append(sink_info)

            self.num_real_sinks = int(sink_info.split(" ")[2])
            self.num_sinks = self.num_real_sinks

            start_label = 1
            for i in range(self.num_real_sinks):
                sink_line = f.readline()
                data = sink_line.split(" ")
                self.sinks.append(sink_line)
                start_label += 1

                # update horizontal plot constraints
                if int(data[1]) < self.minX:
                    self.minX = int(data[1])
                elif int(data[1]) > self.maxX:
                    self.maxX = int(data[1])

                # update vertical plot constraints
                if int(data[2]) < self.minY:
                    self.minY = int(data[2])
                elif int(data[2]) > self.maxY:
                    self.maxY = int(data[2])
            
            self.bnpPre()
            
            for i in range(self.num_pseudo_sinks):
                x = random.randint(self.minX,self.maxX)
                y = random.randint(self.minY,self.maxY)
                self.sinks.append("{} {} {} 35\n".format(start_label+i,x,y))

            while True:
                line = f.readline()
                if not line:
                    break
                else:
                    self.lines.append(line)

    def export_with_pseudo(self):
        with open("{}/evaluation/input/ispd09f11".format(os.getenv('SYMCTS')),'w') as f:
            for i,line in enumerate(self.head):
                if i < 2:
                    f.write(line)
                else:
                    f.write("num sink {}\n".format(self.num_sinks))
            
            for line in self.sinks:
                f.write(line)
            
            for line in self.lines:
                f.write(line)

def convert_circuits():
    convert = convertion()
    convert.readOriginFile()
    convert.export_with_pseudo()

if __name__ == "__main__":
    convert_circuits()
