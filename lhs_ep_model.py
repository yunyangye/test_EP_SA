from pyDOE import lhs
import os
from shutil import copyfile,rmtree
import subprocess
import time
import multiprocessing as mp
import math

# sampling
def sampling(data_lo,data_mo,data_so):
    sample = lhs(8,samples=1500)
    # large office
    sample_lo = []
    for i in range(10):
        sample_lo_cz = []
        for row in sample:
            temp_lo = []
            for j in range(8):
                temp_lo.append((data_lo[j][i][1]-data_lo[j][i][0])*row[j]+data_lo[j][i][0])
            sample_lo_cz.append(temp_lo)
        sample_lo.append(sample_lo_cz)

    # medium office
    sample_mo = []
    for i in range(10):
        sample_mo_cz = []
        for row in sample:
            temp_mo = []
            for j in range(8):
                temp_mo.append((data_mo[j][i][1]-data_mo[j][i][0])*row[j]+data_mo[j][i][0])
            sample_mo_cz.append(temp_mo)
        sample_mo.append(sample_mo_cz)

    # small office
    sample_so = []
    for i in range(10):
        sample_so_cz = []
        for row in sample:
            temp_so = []
            for j in range(8):
                temp_so.append((data_so[j][i][1]-data_so[j][i][0])*row[j]+data_so[j][i][0])
            sample_so_cz.append(temp_so)
        sample_so.append(sample_so_cz)

    return sample_lo,sample_mo,sample_so

def readTable(temp_id,num_table,num_row,num_col,tot_row_yn):
    f = open('./'+str(temp_id)+'/eplustbl.htm','r')
    lines = f.readlines()
    f.close()

    k = 0
    for i in range(len(lines)):
        if '<table' in lines[i]:
            k += 1
            if k == num_table:
                line_start = i
                break
    
    for i in range(line_start,len(lines)):
        if '</table>' in lines[i]:
            line_end = i
            break
    
    k = 0
    for i in range(line_start,line_end):
        if '<tr>' in lines[i]:
            k += 1
    tot_row = k
    
    if tot_row_yn == 'no':
        k = 0
        for i in range(line_start,line_end):
            if '<tr>' in lines[i]:
                k += 1
                if k == num_row:
                    line_start = i
                    break
        
        for i in range(line_start,len(lines)):
            if '</tr>' in lines[i]:
                line_end = i
                break
    
    else:
        k = 0
        for i in range(line_start,line_end):
            if '<tr>' in lines[i]:
                k += 1
                if k == tot_row:
                    line_start = i
                    break
        
        for i in range(line_start,len(lines)):
            if '</tr>' in lines[i]:
                line_end = i
                break
        
    k = 0
    for i in range(line_start,line_end):
        if '<td' in lines[i]:
            k += 1
            if k == num_col:
                indx = i
                break
    
    return float(lines[indx].split('>')[1].split('<')[0].replace(' ',''))

# run models
def runModels(value_list,building_type,city,temp_id,output):
    # modify the tmpl file and save it as idf file
    data_loc = ['$r_wall$','$r_roof$','$u_window$','$shgc$','$lpd$','$epd$','$gas_eff$','$cop$']
    
    ## identify the .tmpl file name
    if building_type == 'LargeOffice':
        temp_list = os.listdir('./LargeOffice/template')
        tmpl_list = []
        for x in temp_list:
            tmpl_list.append('./LargeOffice/template/'+x)
    elif building_type == 'MediumOffice':
        temp_list = os.listdir('./MediumOffice/template')
        tmpl_list = []
        for x in temp_list:
            tmpl_list.append('./MediumOffice/template/'+x)
    else:
        temp_list = os.listdir('./SmallOffice/template')
        tmpl_list = []
        for x in temp_list:
            tmpl_list.append('./SmallOffice/template/'+x)
    
    ## copy .tmpl file into temp file and change .tmpl into .idf
    os.mkdir('./'+str(temp_id))
    for x in tmpl_list:
        if city in x:
            copyfile(x, './'+str(temp_id)+'/temp.idf')
            
    ## modify $$ into values
    f = open('./'+str(temp_id)+'/temp.idf','r')
    lines = f.readlines()
    f.close()
    
    new_lines = []
    for i in range(len(lines)):
        k = 0
        for ind,x in enumerate(data_loc):
            if x in lines[i]:
                new_lines.append(lines[i].replace(x,str(value_list[ind])))
                k = 1
        if k == 0:
            new_lines.append(lines[i])
    
    f = open('./'+str(temp_id)+'/run.idf','w')
    for line in new_lines:
        f.writelines(line)
    f.close()
    
    # run simulation
    df = subprocess.Popen(['/usr/local/EnergyPlus-8-6-0/energyplus-8.6.0','-w','./epw/'+city+'.epw','-d','./'+str(temp_id),'./'+str(temp_id)+'/run.idf'],stdout=subprocess.PIPE)
    output1,err = df.communicate()
    print(output1.decode('utf-8'))
    if not err is None:
        print(err.decode('utf-8'))
    
    # collect site EUI and source EUI
    site_EUI = readTable(temp_id,1,2,3,'no')
    source_EUI = readTable(temp_id,1,4,3,'no')
    elec_EUI = readTable(temp_id,4,0,2,'yes')*1000/readTable(temp_id,3,2,2,'no')
    ng_EUI = readTable(temp_id,4,0,3,'yes')*1000/readTable(temp_id,3,2,2,'no')    
    
    data = city
    output_data = [city]
    for x in value_list:
        data += ','
        data += str(x)
        output_data.append(x)
    data += ','
    data += str(site_EUI)
    output_data.append(site_EUI)
    data += ','
    data += str(source_EUI)
    output_data.append(source_EUI)
    data += ','
    data += str(elec_EUI)
    output_data.append(elec_EUI)
    data += ','
    data += str(ng_EUI)
    output_data.append(ng_EUI)
    data += '\n'
    
    if building_type == 'LargeOffice':
        f = open('./large_office.csv','a')
        f.writelines(data)
        f.close()
    elif building_type == 'MediumOffice':
        f = open('./medium_office.csv','a')
        f.writelines(data)
        f.close()
    else:
        f = open('./small_office.csv','a')
        f.writelines(data)
        f.close()
    output.put(output_data)
    
    # delete the folder
    rmtree('./'+str(temp_id))

# parallel simulation
def parallelSimulation(sample_line,buildingtype_line,city_line):
    #record the start time
    start = time.time()
            
    #multi-processing
    output = mp.Queue()
    processes = [mp.Process(target=runModels,args=(sample_line[i],buildingtype_line[i],city_line[i],i+7501,output)) for i in range(len(sample_line))]

    #count the number of cpu
    cpu = mp.cpu_count()#record the results including inputs and outputs
    print cpu
    
    model_results = []
    
    run_times = math.floor(len(processes)/cpu)
    if run_times > 0:
        for i in range(int(run_times)):
            for p in processes[i*int(cpu):(i+1)*int(cpu)]:
                p.start()
            
            for p in processes[i*int(cpu):(i+1)*int(cpu)]:
                p.join()
    
            #get the outputs
            temp = [output.get() for p in processes[i*int(cpu):(i+1)*int(cpu)]]
            
            for x in temp:
                model_results.append(x)
    
    for p in processes[int(run_times)*int(cpu):len(processes)]:
        p.start()
            
    for p in processes[int(run_times)*int(cpu):len(processes)]:
        p.join()    
        
    #get the outputs
    temp = [output.get() for p in processes[int(run_times)*int(cpu):len(processes)]]
    for x in temp:
        model_results.append(x)
            
    #record the end time
    end = time.time()
    
    return model_results,end-start

# database
r_wall_lo1 = [[0.35,0.77],[0.35,1.17],[0.35,1.17],[0.61,1.43],[0.61,1.43],
              [0.42,1.43],[0.99,1.69],[0.93,1.69],[1.01,1.76],[1.13,1.96],
              [1.09,1.96],[1.22,2.48],[1.22,2.23],[1.30,2.89],[1.41,3.75]]
r_wall_mo1 = [[0.40,1.42],[0.77,2.10],[0.73,2.10],[0.78,2.29],[0.77,2.29],
              [0.79,2.29],[0.99,2.75],[0.96,2.75],[1.01,2.75],[1.13,3.21],
              [1.09,3.21],[1.22,3.60],[1.22,3.60],[1.30,3.60],[1.41,4.76]]
r_wall_so1 = [[0.42,1.98],[0.42,1.98],[0.42,1.98],[0.61,1.98],[0.61,1.98],
              [0.42,1.98],[0.99,2.75],[0.93,2.75],[1.01,2.75],[1.13,3.45],
              [1.09,3.45],[1.22,3.45],[1.22,3.45],[1.30,3.45],[1.41,5.49]]

r_roof_lo1 = [[1.76,3.72],[1.76,4.57],[1.76,4.57],[1.76,4.57],[1.76,4.57],
              [1.76,4.57],[2.04,5.56],[1.98,5.56],[2.07,5.56],[2.50,5.56],
              [2.37,5.56],[2.85,5.56],[2.85,5.56],[2.79,6.33],[2.99,6.33]]
r_roof_mo1 = [[1.76,3.72],[1.76,4.57],[1.76,4.57],[1.76,4.57],[1.76,4.57],
              [1.76,4.57],[2.04,5.56],[1.98,5.56],[2.07,5.56],[2.50,5.56],
              [2.37,5.56],[2.85,5.56],[2.85,5.56],[2.79,6.33],[2.99,6.33]]
r_roof_so1 = [[2.38,6.23],[2.67,6.23],[3.83,6.23],[2.45,6.23],[3.67,6.23],
              [2.00,6.23],[3.04,8.10],[2.99,8.10],[2.75,8.10],[3.32,8.10],
              [3.45,8.10],[3.91,8.10],[3.59,8.10],[4.40,10.07],[5.68,10.07]]

u_window_lo = [[3.36,5.84],[3.29,5.84],[3.29,5.84],[2.85,5.84],[2.85,5.84],
               [2.85,5.84],[2.37,5.84],[2.37,5.84],[2.25,5.84],[2.25,3.53],
               [2.25,3.53],[2.22,3.53],[2.22,3.53],[1.75,3.53],[1.75,3.53]]
u_window_mo = [[3.36,5.84],[3.29,5.84],[3.29,5.84],[2.85,5.84],[2.85,5.84],
               [2.85,5.84],[2.37,5.84],[2.37,5.84],[2.25,5.84],[2.25,3.53],
               [2.25,3.53],[2.22,3.53],[2.22,3.53],[1.75,3.53],[1.75,3.53]]
u_window_so = [[3.36,5.84],[3.29,5.84],[3.29,5.84],[2.85,5.84],[2.85,5.84],
               [2.85,5.84],[2.37,5.84],[2.37,5.84],[2.25,5.84],[2.25,3.53],
               [2.25,3.53],[2.22,3.53],[2.22,3.53],[1.75,3.53],[1.75,3.53]]

shgc_lo = [[0.23,0.54],[0.23,0.54],[0.23,0.54],[0.22,0.54],[0.22,0.54],
           [0.22,0.54],[0.36,0.54],[0.36,0.54],[0.37,0.54],[0.37,0.43],
           [0.37,0.43],[0.37,0.43],[0.37,0.43],[0.41,0.50],[0.30,0.62]]
shgc_mo = [[0.23,0.54],[0.23,0.54],[0.23,0.54],[0.22,0.54],[0.22,0.54],
           [0.22,0.54],[0.36,0.54],[0.36,0.54],[0.37,0.54],[0.37,0.43],
           [0.37,0.43],[0.37,0.43],[0.37,0.43],[0.41,0.50],[0.30,0.62]]
shgc_so = [[0.23,0.54],[0.23,0.54],[0.23,0.54],[0.22,0.54],[0.22,0.54],
           [0.22,0.54],[0.36,0.54],[0.36,0.54],[0.37,0.54],[0.37,0.43],
           [0.37,0.43],[0.37,0.43],[0.37,0.43],[0.41,0.50],[0.30,0.62]]

lpd_lo = [[8.50,16.15],[8.50,16.15],[8.50,16.15],[8.50,16.15],[8.50,16.15],
          [8.50,16.15],[8.50,16.15],[8.50,16.15],[8.50,16.15],[8.50,16.15],
          [8.50,16.15],[8.50,16.15],[8.50,16.15],[8.50,16.15],[8.50,16.15]]
lpd_mo = [[8.50,16.90],[8.50,16.90],[8.50,16.90],[8.50,16.90],[8.50,16.90],
          [8.50,16.90],[8.50,16.90],[8.50,16.90],[8.50,16.90],[8.50,16.90],
          [8.50,16.90],[8.50,16.90],[8.50,16.90],[8.50,16.90],[8.50,16.90]]
lpd_so = [[8.50,19.48],[8.50,19.48],[8.50,19.48],[8.50,19.48],[8.50,19.48],
          [8.50,19.48],[8.50,19.48],[8.50,19.48],[8.50,19.48],[8.50,19.48],
          [8.50,19.48],[8.50,19.48],[8.50,19.48],[8.50,19.48],[8.50,19.48]]

epd_lo = [[8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],
          [8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],
          [8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76]]
epd_mo = [[8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],
          [8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],
          [8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76],[8.07,10.76]]
epd_so = [[6.78,10.76],[6.78,10.76],[6.78,10.76],[6.78,10.76],[6.78,10.76],
          [6.78,10.76],[6.78,10.76],[6.78,10.76],[6.78,10.76],[6.78,10.76],
          [6.78,10.76],[6.78,10.76],[6.78,10.76],[6.78,10.76],[6.78,10.76]]

heat_eff_lo = [[0.70,0.83],[0.70,0.83],[0.70,0.83],[0.70,0.83],[0.70,0.83],
               [0.70,0.83],[0.70,0.83],[0.70,0.83],[0.70,0.83],[0.70,0.83],
               [0.70,0.83],[0.70,0.83],[0.70,0.83],[0.70,0.83],[0.70,0.83]]
heat_eff_mo = [[0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],
               [0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],
               [0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80]]
heat_eff_so = [[0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],
               [0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],
               [0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80],[0.70,0.80]]

cool_cop_lo = [[4.90,6.28],[4.90,6.28],[4.90,6.28],[4.90,6.28],[4.90,6.28],
               [4.90,6.28],[4.90,6.28],[4.90,6.28],[4.90,6.28],[4.90,6.28],
               [4.90,6.28],[4.90,6.28],[4.90,6.28],[4.90,6.28],[4.90,6.28]]
cool_cop_mo = [[2.68,3.23],[2.68,3.23],[2.68,3.23],[2.68,3.23],[2.68,3.23],
               [2.68,3.23],[2.68,3.23],[2.68,3.23],[2.68,3.23],[2.68,3.23],
               [2.68,3.23],[2.68,3.23],[2.68,3.23],[2.68,3.23],[2.68,3.23]]
cool_cop_so = [[3.07,4.12],[3.07,4.12],[3.07,4.12],[3.07,4.12],[3.07,4.12],
               [3.07,4.12],[3.07,4.12],[3.07,4.12],[3.07,4.12],[3.07,4.12],
               [3.07,4.12],[3.07,4.12],[3.07,4.12],[3.07,4.12],[3.07,4.12]]

# update the database
r_wall_lo = []
r_wall_mo = []
r_wall_so = []
r_roof_lo = []
r_roof_mo = []
r_roof_so = []

for row in r_wall_lo1:
    temp = []
    for x in row:
        temp.append(x-0.32)
    r_wall_lo.append(temp)

for row in r_wall_mo1:
    temp = []
    for x in row:
        temp.append(x-0.385)
    r_wall_mo.append(temp)

for row in r_wall_so1:
    temp = []
    for x in row:
        temp.append(x-0.38)
    r_wall_so.append(temp)

for row in r_roof_lo1:
    temp = []
    for x in row:
        temp.append(x-0.25)
    r_roof_lo.append(temp)

for row in r_roof_mo1:
    temp = []
    for x in row:
        temp.append(x-0.25)
    r_roof_mo.append(temp)

for row in r_roof_so1:
    temp = []
    for x in row:
        temp.append(x)
    r_roof_so.append(temp)

# cities
#cities = ['Honolulu','Tampa','Tucson','Atlanta','ElPaso',
#          'SanDiego','NewYork','Albuquerque','Seattle',
#          'Buffalo','Denver','Rochester','Great_Falls',
#          'InternationalFalls','FairBanks']
cities = ['SanDiego','NewYork','Albuquerque','Seattle',
          'Buffalo','Denver','Rochester','Great_Falls',
          'InternationalFalls','FairBanks']

data_lo = [r_wall_lo,r_roof_lo,u_window_lo,shgc_lo,lpd_lo,epd_lo,heat_eff_lo,cool_cop_lo]
data_mo = [r_wall_mo,r_roof_mo,u_window_mo,shgc_mo,lpd_mo,epd_mo,heat_eff_mo,cool_cop_mo]
data_so = [r_wall_so,r_roof_so,u_window_so,shgc_so,lpd_so,epd_so,heat_eff_so,cool_cop_so]

sample_lo,sample_mo,sample_so = sampling(data_lo,data_mo,data_so)

sample_line = []
buildingtype_line = []
city_line = []
'''
for ind,row in enumerate(sample_lo):
    for row1 in row:
        sample_line.append(row1)
        buildingtype_line.append('LargeOffice')
        city_line.append(cities[ind])
'''
for ind,row in enumerate(sample_mo):
    for row1 in row:
        sample_line.append(row1)
        buildingtype_line.append('MediumOffice')
        city_line.append(cities[ind])
'''
for ind,row in enumerate(sample_so):
    for row1 in row:
        sample_line.append(row1)
        buildingtype_line.append('SmallOffice')
        city_line.append(cities[ind])
'''
parallelSimulation(sample_line,buildingtype_line,city_line)
