class Point():
    # basic type in the whole design
    def __init__(self,x,y,p_type='normal'):
        self.location = complex(x,y)
        self.type = p_type
        self.p_id = 0

    def set_id(self,p_id):
        self.p_id = p_id

    def get_id(self):
        return self.p_id

class Sink(Point):

    def __init__(self,location,label="real"):
        super(Sink,self).__init__(location.real,location.imag,p_type='sink')
        self.relative_location = complex(0,0)
        self.label = label 
        self.__group_id = [] # represent hierachical group id

    def append_gid(self,gid):
        self.__group_id.append(gid)

    def get_gid(self):
        return self.__group_id 

class G_Point(Point):
    # this type of point is used only in topology generation.(ie,wire snaking)
    def __init__(self,location):
        super(G_Point,self).__init__(location.real,location.imag,p_type='g_point')  
        self.__group_id = [] # represent hierachical group id

    def append_gid(self,gid):
        self.__group_id.append(gid)

    def get_gid(self):
        return self.__group_id 
    
class M_Point(G_Point):
    # this type of point can be used both in topology generation and buffer insertion
    def __init__(self, location):
        super(M_Point,self).__init__(location=location) 
        self.type = 'm_point'
        self.__group_id = []
        self.__buffer_type = 0

    def get_gid(self):
        return self.__group_id

    def set_gid(self,gid_list):
        self.__group_id = gid_list


