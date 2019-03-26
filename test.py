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

site_EUI = readTable(1,1,2,3,'no')
source_EUI = readTable(1,1,4,3,'no')
elec_EUI = readTable(1,4,0,2,'yes')*1000/readTable(1,3,2,2,'no')
ng_EUI = readTable(1,4,0,3,'yes')*1000/readTable(1,3,2,2,'no')

print readTable(1,1,2,3,'no')
print readTable(1,1,4,3,'no')
print readTable(1,4,0,2,'yes')
print readTable(1,4,0,3,'yes')
print readTable(1,3,2,2,'no')


