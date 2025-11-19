import json
import csv

'''
{
    "country": "Afghanistan",
    "electricity_access": 85.3,
    "gdp": 16417,
    "continent": "Asia"
  },
  
gerar um csv com os dados de ./dados.json
'''

# Read JSON file
with open('/workspaces/estatisticaGDP/data/dados.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Write to CSV file
with open('/workspaces/estatisticaGDP/data/dados.csv', 'w', newline='', encoding='utf-8') as csv_file:
    if data:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        print("CSV file created successfully: ./dados.csv")