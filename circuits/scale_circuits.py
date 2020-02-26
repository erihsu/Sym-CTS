import pdb
with open("./ispd/ispd09f11",'r') as f1, open("./ex_ispd/ispd09f11_small_new",'w') as f2:

    for i in range(137):
        data = f1.readline()
        if i == 0:
            data_new = data.split()
            data_new[2] = int(int(data_new[2])/1000*30)
            data_new[3] = int(int(data_new[3])/1000*30)
            f2.write("{} {} {} {}\n".format(data_new[0],data_new[1],data_new[2],data_new[3]))
        elif  2 < i < 124:
            data_new = data.split()
            data_new[1] = int(float(data_new[1])/1000*30)
            data_new[2] = int(float(data_new[2])/1000*30)
            
            f2.write("{} {} {} {}\n".format(data_new[0],data_new[1],data_new[2],data_new[3]))
        else:
            f2.write(data)    