file_path = r'C:\Users\ASUS\Downloads\A6FE192460051_attlog.dat'

with open(file_path) as file:
    lines = file.readlines()

for i in range(len(lines)):
    line = lines[i].strip()
    parts = line.split()
    
    if len(parts) >=3:
       
        employee_id = parts[0] #id
        date = parts[1] #date
        time = parts[2] #time
        #unnamed = parts[3]
       
        print(f"{employee_id}")
        print(f"{date}")
        print(f"{time}")
        #print(f"Line{i + 1}: {' '.join(parts)}")
        #print(f"{unnamed}")
        print()  
    

    
