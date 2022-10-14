from os import mkfifo
import os
from tracemalloc import start
from numpy import average, diff
import pandas as pd
from datetime import datetime
from datetime import timedelta
from pathlib import Path
import sys

from requests import delete


#getting for the csv file name
file_name = sys.argv[1]
runtype = sys.argv[2]

path_to_csvfile = Path(file_name)
#taking in the fliepath which sadly is absolute for now
data = pd.read_csv(path_to_csvfile)


df2 = data.pivot(index="timeStamp",columns="label",values="elapsed")
df2.index = df2.index.map(lambda v: datetime.utcfromtimestamp(v / 1000).strftime('%Y-%m-%d %H:%M:%S.%f'))
creation_date = df2.index[0]
df2.index = df2.index.str.slice(start=11)
df2["localhost Memory"] = df2["localhost Memory"] / 1000.0
df2["localhost CPU"] = df2["localhost CPU"] / 1000.0


temp_array = []

for x in range(0,len(df2.index)):
    temp = df2.index[x]
    temp_array.append(temp)

#print(temp_array)
for x in range(1, len(temp_array)):
    a = datetime.strptime(temp_array[0],'%H:%M:%S.%f')
    b = datetime.strptime(temp_array[x],'%H:%M:%S.%f')
    temp_array[x] = (b-a).total_seconds()

#saving the max values of the CPU and Memmory usage, and the start/end time of the test
start_time = df2.index[0]
end_time = df2.index[len(df2.index) - 1]
average_time = temp_array[len(temp_array) - 1] / 5
average_time_dateform = timedelta(seconds=average_time)
total_test_time = timedelta(seconds=temp_array[len(temp_array) -1])


max_value_CPU = df2["localhost CPU"].max()
max_value_Memory = df2["localhost Memory"].max()
average_value_CPU = df2["localhost CPU"].mean()
average_value_Memory = df2["localhost Memory"].mean()

#setting the first index to 0 
temp_array[0] = 0
df2.index = temp_array

#giving a name to the index
df2.index.name = "Timestamp"
creation_date = creation_date[0:19]
#creating the cvs file where the results will be saved
metrics_folder = Path("metrics_folder")
metrics_folder.mkdir()

result_file = runtype + "metrics-" + str(creation_date) + ".csv"

open("metrics_folder/" + result_file, 'w+')

#getting the path to the generated file
path_to_metrics_folder = Path("metrics_folder/" + result_file)

#printing to the terminal 
print("<=========================================>\n")
print("The results are from a " + runtype + " command\n")
print("Starting time : " + start_time + "      " + "Finishing time : " + end_time)
print("Avarage run time :{:0>8} ".format(str(timedelta(seconds=average_time))) + " Total test time :{:0>8}".format(str(timedelta(seconds=temp_array[len(temp_array) -1]))))
print("\nMax CPU Usage % : " + str(max_value_CPU))
print("\nMax Memory Usage % : " + str(max_value_Memory))
print("\nAvarage CPU Usage % : " + str(average_value_CPU))
print("\nAvarage Memory Usage % : " + str(average_value_Memory))
print("\n<=========================================>")

os.remove(path_to_csvfile)
df2.to_csv(path_to_metrics_folder, encoding='utf-8')
