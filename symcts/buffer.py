from wire import wire
class clk_buffer():

	def __init__(self,startpoint,endpoint,buffer_type):
		self.startpoint = startpoint
		self.endpoint   = endpoint
		self.buffer_type = buffer_type
		self.__id = 0

	def set_id(self,identity):
		self.__id = identity

	def get_id(self):
		return self.__id

class candidate(clk_buffer):

	def __init__(self,startpoint,endpoint):
		super().__init__(startpoint,endpoint,buffer_type="none")

	def insert_buffer(self,buffer_type):
		self.buffer_type = buffer_type

	def changeToWire(self):
		return wire(self.startpoint,self.endpoint)



