import numpy as np
import matplotlib.pyplot as plt

#import csv file
data = np.genfromtxt('DataFiles/data_18-04-2024_13-14-46.csv', delimiter=',', skip_header=1)

relative_time = data[:,0]-data[0,0]
dt = np.diff(relative_time)

fs_real = 1/np.mean(dt)
print(fs_real)

#plot distribution of dt

plt.figure()
plt.hist(dt, bins=100)
plt.show()
