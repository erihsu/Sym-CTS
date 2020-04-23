import numpy as np
from point import M_Point,G_Point,Sink

class wire():
    # startpoint and endpoint are Point type
    def __init__(self, startpoint, endpoint):
        self.startpoint = startpoint # Point type
        self.endpoint = endpoint     # Point type

        self.start = self.startpoint.location # complex number
        self.end   = self.endpoint.location     # complex number

    def changeStartPoint(self,new_startpoint):
        self.startpoint = new_startpoint

    def changeEndPoint(self,new_endpoint):
        self.endpoint = new_endpoint

    def getLength(self):
        return abs(self.end - self.start)

class Man_wire(wire):
    def __init__(self, startpoint, endpoint):
        super().__init__(startpoint,endpoint)
        self.turning = [G_Point(location=complex(self.end.real,self.start.imag)),\
                        G_Point(location=complex(self.start.real,self.end.imag))]

    def getLength(self):
        vec = self.end - self.start
        return abs(vec.real) + abs(vec.imag)

    def getPoints(self,choice=True):

        if choice:
            return self.turning[0]
        else:
            return self.turning[1]

class Snake_wire(Man_wire):

    def __init__(self, startpoint, endpoint):
        super().__init__(startpoint,endpoint)
        self.__points = [] #recording new points when snaking
        self.__wires = []

    def snaking(self,length):

        op1_1 = complex(1,0)
        op1_2 = complex(0,1)

        min_length = self.getLength()
        vec = self.end - self.start
        real_sign = np.sign(vec.real)
        image_sign = np.sign(vec.imag)
        index = int(-1/2*image_sign + 1/2)

        if isinstance(self.startpoint,Sink) or isinstance(self.endpoint,Sink) or (length >= min_length and length <2*min_length):
            # update points while snaking(1 point)
            self.__points.append(G_Point(self.turning[index].location))

            # update wires while snaking(2 wires)
            self.__wires.append(wire(self.startpoint,self.__points[0]))
            self.__wires.append(wire(self.__points[0],self.endpoint))

        elif length >= 2*min_length and length <5*min_length:
            step = (length-min_length)/4
            # update points while snaking(3 points)
            self.__points.append(G_Point(self.start-image_sign*step*op1_2))

            # self.__points.append(G_Point(self.turning[index].location+step*complex(real_sign,-image_sign)))
            self.__points.append(G_Point(complex((self.end+real_sign*step*op1_1).real,(self.start-image_sign*step*op1_2).imag)))

            self.__points.append(G_Point(self.end+real_sign*step*op1_1))

            # update wires while snaking(4 wires)
            self.__wires.append(wire(self.startpoint,self.__points[0]))
            self.__wires.append(wire(self.__points[0],self.__points[1]))
            self.__wires.append(wire(self.__points[1],self.__points[2]))
            self.__wires.append(wire(self.__points[2],self.endpoint))

        else:
            step = (length-min_length)/8
            width1 = abs(vec.real)/3
            width2 = abs(vec.imag)/3
            # update points while snaking(11 points)
            self.__points.append(G_Point(self.start-image_sign*step*op1_2))
            self.__points.append(G_Point(self.start-image_sign*step*op1_2+real_sign*width1*op1_1))
            self.__points.append(G_Point(self.start+real_sign*width1*op1_1))
            self.__points.append(G_Point(self.start+2*real_sign*width1*op1_1))
            self.__points.append(G_Point(self.start-image_sign*step*op1_2+2*real_sign*width1*op1_1))

            # self.__points.append(G_Point(self.turning[index].location+step*complex(real_sign,-image_sign)))
            self.__points.append(G_Point(complex((self.end+real_sign*step*op1_1).real,(self.start-image_sign*step*op1_2).imag)))

            self.__points.append(G_Point(self.end+real_sign*step*op1_1-2*image_sign*width2*op1_2))
            self.__points.append(G_Point(self.end-2*image_sign*width2*op1_2))
            self.__points.append(G_Point(self.end-image_sign*width2*op1_2))
            self.__points.append(G_Point(self.end+real_sign*step*op1_1-image_sign*width2*op1_2))
            self.__points.append(G_Point(self.end+real_sign*step*op1_1))

            # update wires while snaking(12 wires)
            self.__wires.append(wire(self.startpoint,self.__points[0]))
            for i in range(10):
                self.__wires.append(wire(self.__points[i],self.__points[i+1]))
            self.__wires.append(wire(self.__points[10],self.endpoint))

    
    def no_snaking(self):

        vec = self.end - self.start
        image_sign = np.sign(vec.imag)
        index = int(-1/2*image_sign + 1/2)

        self.__points.append(G_Point(self.turning[index].location))

        self.__wires.append(wire(self.startpoint,self.__points[0]))
        self.__wires.append(wire(self.__points[0],self.endpoint))


    def getPoints(self):
        return self.__points 

    def getWires(self):
        return self.__wires
