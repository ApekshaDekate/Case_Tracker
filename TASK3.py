import pandas as pd
df = pd.read_csv(r'C:\Users\ASUS\Downloads\A6FE192460051_attlog.dat', delimiter='\t',encoding='utf-8')
with open(r'C:\Users\ASUS\Downloads\A6FE192460051_attlog.dat') as f:
    [line.split() for line in f]
    print(df.iloc[:,[0,1]])
