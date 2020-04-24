from wire import wire
from point import M_Point

def merge(points,seg_length):

	new_points = []
	new_wires = []
	end_point_location = get_center(points)
	end_point = M_Point(location=end_point_location)
	end_point.set_gid(points[0].get_gid())

	for i in range(len(points)):
		direct_wire = wire(end_point,points[i])
		new_points += [end_point,points[i]]
		new_wires  += [direct_wire]

	return end_point,new_points,new_wires

def get_center(points):
	sum_loc = complex(0,0)
	for i in range(len(points)):
		sum_loc += points[i].location
	return sum_loc/len(points)

def get_seg_length(points):

	points_number = len(points)
	vec = complex(0,0)
	seg_length = 0
	center = get_center(points)
	for i in range(points_number):
		vec += points[i].location - center
		seg_length += abs(vec.real)+abs(vec.imag)
	
	return seg_length/points_number


def main():
	pass

if __name__ == "__main__":
	main()
