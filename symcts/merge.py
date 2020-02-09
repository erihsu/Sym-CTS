from wire import Snake_wire
from point import M_Point

def merge_two_points(points,seg_length):

	new_points = []
	new_wires = []
	end_point = M_Point(location=(points[0].location+points[1].location)/2)
	end_point.set_gid(points[0].get_gid())
	wire1 = Snake_wire(end_point,points[0])
	wire2 = Snake_wire(end_point,points[1])
	wire1.snaking(seg_length)
	wire2.snaking(seg_length)
	new_points = wire1.getPoints() + wire2.getPoints()
	new_wires = wire1.getWires() + wire2.getWires()
	return end_point,new_points,new_wires

def merge_three_points(points,seg_length):

	new_points = []
	new_wires = []
	end_point_location = get_center_of_three(points[0].location,points[1].location,points[2].location)
	end_point = M_Point(location=end_point_location)
	end_point.set_gid(points[0].get_gid())
	wire1 = Snake_wire(end_point,points[0])
	wire2 = Snake_wire(end_point,points[1])
	wire3 = Snake_wire(end_point,points[2])

	wire1.snaking(seg_length)
	wire2.snaking(seg_length)
	wire3.snaking(seg_length)

	new_points = wire1.getPoints() + wire2.getPoints() + wire3.getPoints()
	new_wires  = wire1.getWires() + wire2.getWires() + wire3.getWires()

	return end_point,new_points,new_wires

def merge(points,seg_length,number=2):
	# the merge function return endpoints(M_Points) and a list of wires(each wire contain a bunch of G_Points)

	if number == 2 and len(points) == 2:
		parent,nodes,wires = merge_two_points(points,seg_length)
	elif number == 3 and len(points ) == 3:
		parent,nodes,wires = merge_three_points(points,seg_length)
	else:
		print("please make sure input contain two or three points")
		exit(1)
	return parent,nodes,wires
			
def get_center_of_three(loca1,loca2,loca3):
	# input: location of three points
	# output: location of center point
	l1 = abs(loca1-loca2)
	l2 = abs(loca2-loca3)
	l3 = abs(loca1-loca3)
	if l1>l2 and l1>l3:
		loca_center = (loca1+loca2)/2
	elif l2>l1 and l2>l3:
		loca_center = (loca2+loca3)/2
	elif l3>l1 and l3>l2:
		loca_center = (loca1+loca3)/2
	return loca_center

def get_seg_length(points):

	points_number = len(points)
	if not (points_number == 2 or points_number == 3):
		print("can not get seg length more than 3 points")
		return None
	else:
		if points_number == 2:
			vec = points[0].location - points[1].location
			return abs(vec.real) + abs(vec.imag)
		else:
			center = get_center_of_three(points[0].location,points[1].location,points[2].location)
			vec1 = points[0].location - center
			vec2 = points[1].location - center
			vec3 = points[2].location - center
			return max((abs(vec1.real)+abs(vec1.imag)),(abs(vec2.real)+abs(vec2.imag)),abs((vec3.real)+abs(vec3.imag)))


def main():
	pass

if __name__ == "__main__":
	main()
