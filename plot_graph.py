import pandas as pd


file_name = 'Sites.txt'
df = pd.read_csv(file_name, sep='\t')
print(df['lon   '].min(), df['lon   '].max())
