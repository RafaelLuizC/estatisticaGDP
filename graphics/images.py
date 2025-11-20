'''
com base no exemplo:
  {
    "country": "Afghanistan",
    "electricity_access": 85.3,
    "gdp": 16417,
    "continent": "Asia"
  }
contido no arquivo "/workspaces/estatisticaGDP/data/dados.json"

gerar pngs com os seguintes gráficos:
- gráfico de setores (contendo a % de países por continente)
- gráfico de barras (contendo a média do acesso à eletricidade por continente)
- gráfico de barras (contendo a média do gdp por continente)
- gráfico de dispersão (contendo a relação entre acesso à eletricidade e gdp por país (cada 5k gdp é uma altura diferente))
- gráfico de setores (contendo a % de países com acesso à eletricidade acima de 90% e abaixo de 90%)
- gráfico de barras (mostrando o maior e o menor acesso à eletricidade por continente)

salvar os dados em "/workspaces/estatisticaGDP/graphics/"
'''

import json
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
import matplotlib.ticker as mticker

# Load data from JSON file
with open('/workspaces/estatisticaGDP/data/dados.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)
# Convert data to DataFrame
df = pd.DataFrame(data)
# Create output directory if it doesn't exist
output_dir = '/workspaces/estatisticaGDP/graphics/'
os.makedirs(output_dir, exist_ok=True)
# 1. Pie chart: % of countries by continent
continent_counts = df['continent'].value_counts()
plt.figure(figsize=(8, 8))
plt.pie(continent_counts, labels=continent_counts.index, autopct='%1.1f%%', startangle=140)
plt.title('Porcentagem de Países por Continente')
plt.savefig(os.path.join(output_dir, 'paises_por_continente.png'))
plt.close()
# 2. Bar chart: Average electricity access by continent
avg_electricity_access = df.groupby('continent')['electricity_access'].mean()
plt.figure(figsize=(10, 6))
avg_electricity_access.plot(kind='bar', color='skyblue')
plt.title('Média do Acesso à Eletricidade por Continente')
plt.xlabel('Continente')
plt.ylabel('Média do Acesso à Eletricidade (%)')
plt.xticks(rotation=0)
plt.savefig(os.path.join(output_dir, 'media_acesso_eletricidade_por_continente.png'))
plt.close()
# 3. Bar chart: Average PIB by continent
avg_gdp = df.groupby('continent')['gdp'].mean()
plt.figure(figsize=(10, 6))
avg_gdp.plot(kind='bar', color='salmon')
plt.title('Média do PIB por Continente')
plt.xlabel('Continente')
plt.ylabel('Média do PIB')
plt.xticks(rotation=0)

ax = plt.gca()
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f'${int(round(x)):,}'))

plt.savefig(os.path.join(output_dir, 'media_gdp_por_continente.png'))
plt.close()
# 4. Scatter plot: Relationship between electricity access and PIB by country
plt.figure(figsize=(10, 6))
plt.scatter(df['gdp'], df['electricity_access'], alpha=0.7, color='purple')
plt.title('Relação entre Acesso à Eletricidade e PIB por País')
plt.xlabel('PIB')
plt.ylabel('Electricity Access (%)')
plt.xscale('log')

ax = plt.gca()
ax.xaxis.set_major_locator(mticker.LogLocator(base=10.0, numticks=12, subs=(1,)))
def fmt(x, pos):
    try:
        if x >= 1:
            return f'${int(round(x)):,}'
        else:
            return f'${x:.2f}'
    except Exception:
        return str(x)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt))

plt.grid(True, which="both", ls="--", linewidth=0.5)
plt.savefig(os.path.join(output_dir, 'relacao_acesso_eletricidade_pib.png'))
plt.close()
# 5. Pie chart: % of countries with electricity access above and below 90%
above_90 = df[df['electricity_access'] > 90].shape[0]
below_90 = df[df['electricity_access'] <= 90].shape[0]
labels = ['Acima de 90%', 'Abaixo ou igual a 90%']
sizes = [above_90, below_90]
plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['lightgreen', 'lightcoral'])
plt.title('Porcentagem de Países com Acesso à Eletricidade Acima e Abaixo de 90%')
plt.savefig(os.path.join(output_dir, 'acesso_eletricidade_acima_abaixo_90.png'))
plt.close()
# 6. Bar chart: Max and Min electricity access by continent
max_access = df.groupby('continent')['electricity_access'].max()
min_access = df.groupby('continent')['electricity_access'].min()
access_df = pd.DataFrame({'Maior Acesso (%)': max_access, 'Menor Acesso (%)': min_access})
access_df.plot(kind='bar', figsize=(10, 6))
plt.title('Maior e Menor Acesso à Eletricidade por Continente')
plt.xlabel('Continente')
plt.ylabel('Acesso à Eletricidade (%)')
plt.xticks(rotation=0)
plt.legend(loc='lower right')
plt.savefig(os.path.join(output_dir, 'maior_menor_acesso_eletricidade_por_continente.png'))
plt.close()

print("Gráficos gerados e salvos em:", output_dir)