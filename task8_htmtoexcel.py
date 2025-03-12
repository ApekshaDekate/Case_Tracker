# Importing pandas 
import pandas as pd 

# The webpage URL whose table we want to extract 
url = "https://www.geeksforgeeks.org/extended-operators-in-relational-algebra/"

# Assign the table data to a Pandas dataframe 
table = pd.read_html(url)[0] 

# Store the dataframe in Excel file 
table.to_excel("data.xlsx") 
