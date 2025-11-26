import json
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
import matplotlib.ticker as mticker
import unicodedata
import matplotlib.patches as mpatches
import colorsys
import matplotlib.colors as mc

# --- Configuração Inicial e Carregamento de Dados ---

json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'dados.json')
with open(json_path, 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

df = pd.DataFrame(data)

output_dir = os.path.join(os.path.dirname(__file__))
os.makedirs(output_dir, exist_ok=True)

# --- Definição Global de Cores e Ordenação ---

# Função auxiliar para ordenação alfabética ignorando acentos
def normalize_sort_key(x):
    if isinstance(x, str):
        return unicodedata.normalize('NFD', x).encode('ascii', 'ignore').decode('ascii')
    return x

# Função auxiliar para ajustar a luminosidade da cor
def adjust_lightness(color, amount=0.5):
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2])

# Identificar continentes únicos e ordenar alfabeticamente
sorted_continents = sorted(df['continent'].unique(), key=normalize_sort_key)

# Nova paleta de cores fornecida
custom_palette = ['#4e79a7','#f28e2b','#e15759','#76b7b2','#59a14f','#edc949','#b07aa1']

# Criar mapa de cores
color_map = {continent: custom_palette[i % len(custom_palette)] for i, continent in enumerate(sorted_continents)}

print("Mapa de cores definido:", {k: str(v) for k, v in color_map.items()})


# --- 1. Pie chart: % of countries by continent ---

continent_counts = df['continent'].value_counts()
continent_counts = continent_counts.sort_index(key=lambda index: index.map(normalize_sort_key))

pie_colors = [color_map[c] for c in continent_counts.index]

plt.figure(figsize=(16, 16))
plt.pie(continent_counts, 
        labels=continent_counts.index, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=pie_colors,
        textprops={'fontsize': 24})
plt.title('Porcentagem de Países por Continente', fontsize=30)
plt.savefig(os.path.join(output_dir, 'paises_por_continente.png'))
plt.close()


# --- 2. Bar chart: Average electricity access by continent ---

avg_electricity_access = df.groupby('continent')['electricity_access'].mean()
avg_electricity_access = avg_electricity_access.sort_index(key=lambda x: x.map(normalize_sort_key))

bar_colors_elec = [color_map[c] for c in avg_electricity_access.index]

plt.figure(figsize=(20, 12))
avg_electricity_access.plot(kind='bar', color=bar_colors_elec)

plt.title('Média do Acesso à Eletricidade por Continente', fontsize=30)
plt.xlabel('Continente', fontsize=24)
plt.ylabel('Média do Acesso à Eletricidade (%)', fontsize=24)
plt.xticks(rotation=0, fontsize=16)
plt.yticks(fontsize=20)
plt.savefig(os.path.join(output_dir, 'media_acesso_eletricidade_por_continente.png'))
plt.close()


# --- 3. Bar chart: Average PIB by continent ---

avg_gdp = df.groupby('continent')['gdp'].mean() * 1_000_000
avg_gdp = avg_gdp.sort_index(key=lambda x: x.map(normalize_sort_key))

bar_colors_gdp = [color_map[c] for c in avg_gdp.index]

plt.figure(figsize=(20, 12))
avg_gdp.plot(kind='bar', color=bar_colors_gdp)

plt.title('Média do PIB por Continente', fontsize=30)
plt.xlabel('Continente', fontsize=24)
plt.ylabel('Média do PIB', fontsize=24)
plt.xticks(rotation=0, fontsize=16)
plt.yticks(fontsize=20)

ax = plt.gca()
def gdp_formatter(x, pos):
    if x >= 1e12:
        return f'${x/1e12:.1f}T'
    elif x >= 1e9:
        return f'${x/1e9:.1f}B'
    elif x >= 1e6:
        return f'${x/1e6:.1f}M'
    else:
        return f'${int(round(x)):,}'
ax.yaxis.set_major_formatter(mticker.FuncFormatter(gdp_formatter))

plt.savefig(os.path.join(output_dir, 'media_gdp_por_continente.png'))
plt.close()


# --- NOVO 3b. Pie chart: Average PIB by continent ---
# Adicionado conforme solicitado para melhor visualização das proporções

plt.figure(figsize=(16, 16))
# Usando os mesmos dados ordenados do gráfico de barras anterior
pie_gdp_colors = [color_map[c] for c in avg_gdp.index]

plt.pie(avg_gdp, 
        labels=avg_gdp.index, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=pie_gdp_colors,
        textprops={'fontsize': 24})
plt.title('Média do PIB por Continente (Distribuição)', fontsize=30)
plt.savefig(os.path.join(output_dir, 'media_gdp_por_continente_pizza.png'))
plt.close()


# --- 4. Scatter plot: Relationship between electricity access and PIB by country ---

plt.figure(figsize=(20, 12))
gdp_million = df['gdp'] * 1_000_000

for continent in sorted_continents:
    mask = df['continent'] == continent
    plt.scatter(gdp_million[mask], df.loc[mask, 'electricity_access'], 
                alpha=0.7, color=color_map[continent], label=continent, s=100)

plt.title('Relação entre Acesso à Eletricidade e PIB por País', fontsize=30)
plt.xlabel('PIB', fontsize=24)
plt.ylabel('Electricity Access (%)', fontsize=24)
plt.xticks(fontsize=16)
plt.yticks(fontsize=20)
plt.xscale('log')
plt.legend(loc='best', fontsize=16)

ax = plt.gca()
ax.xaxis.set_major_locator(mticker.LogLocator(base=10.0, numticks=12, subs=(1,)))
ax.xaxis.set_major_formatter(mticker.FuncFormatter(gdp_formatter))

plt.grid(True, which="both", ls="--", linewidth=0.5)
plt.savefig(os.path.join(output_dir, 'relacao_acesso_eletricidade_pib.png'))
plt.close()


# --- 5. Pie chart: % of countries with electricity access above and below 90% ---

above_90 = df[df['electricity_access'] > 90].shape[0]
below_90 = df[df['electricity_access'] <= 90].shape[0]
labels = ['Acima de 90%', 'Abaixo ou igual a 90%']
sizes = [above_90, below_90]
plt.figure(figsize=(16, 16))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['lightgreen', 'lightcoral'], textprops={'fontsize': 24})
plt.title('Porcentagem de Países com Acesso\nà Eletricidade Acima e Abaixo de 90%', fontsize=30)
plt.savefig(os.path.join(output_dir, 'acesso_eletricidade_acima_abaixo_90.png'))
plt.close()


# --- 6. Bar chart: Max and Min electricity access by continent ---

max_access = df.groupby('continent')['electricity_access'].max()
min_access = df.groupby('continent')['electricity_access'].min()
access_df = pd.DataFrame({'Maior Acesso (%)': max_access, 'Menor Acesso (%)': min_access})
access_df = access_df.sort_index(key=lambda x: x.map(normalize_sort_key))

colors_max_min = ['#4e79a7', '#edc949']

ax = access_df.plot(kind='bar', figsize=(20, 12), color=colors_max_min)

plt.title('Maior e Menor Acesso à Eletricidade por Continente', fontsize=30)
plt.xlabel('Continente', fontsize=24)
plt.ylabel('Acesso à Eletricidade (%)', fontsize=24)
plt.xticks(rotation=0, fontsize=16)
plt.yticks(fontsize=20)
plt.legend(loc='lower right', fontsize=16)

plt.savefig(os.path.join(output_dir, 'maior_menor_acesso_eletricidade_por_continente.png'))
plt.close()


# --- 7. Box plot: GDP distribution by continent ---

plt.figure(figsize=(20, 12))
df_gdp = df.copy()
df_gdp['gdp'] = df_gdp['gdp'] * 1_000_000

# TRUQUE: Converter para Categórico ordenado para forçar a ordem no Boxplot
# Apenas ordenar o DataFrame não garante a ordem no eixo X do boxplot.
df_gdp['continent'] = pd.Categorical(
    df_gdp['continent'], 
    categories=sorted_continents, 
    ordered=True
)

# O boxplot vai respeitar a ordem das categorias
box_gdp = df_gdp.boxplot(column='gdp', by='continent', figsize=(20, 12), patch_artist=True)

# Recuperar os labels do eixo X (agora garantidamente ordenados)
categories = box_gdp.get_xticklabels()
for patch, label in zip(box_gdp.patches, categories):
    continent_name = label.get_text()
    color = color_map[continent_name]
    patch.set_facecolor(color)
    patch.set_edgecolor('black')
    patch.set_linewidth(1)
    patch.set_alpha(0.7)

handles = [mpatches.Patch(facecolor=color_map[c], edgecolor='black', label=c, alpha=0.7) for c in sorted_continents]
plt.legend(handles=handles, title='Continente', fontsize=14, title_fontsize=16, loc='upper right')

plt.title('Distribuição do PIB por Continente', fontsize=30)
plt.suptitle('')
plt.xlabel('Continente', fontsize=24)
plt.ylabel('PIB', fontsize=24)
plt.xticks(fontsize=16)
plt.yticks(fontsize=20)
ax = plt.gca()
ax.yaxis.set_major_formatter(mticker.FuncFormatter(gdp_formatter))
plt.savefig(os.path.join(output_dir, 'boxplot_gdp_por_continente.png'))
plt.close()


# --- 8. Box plot: Electricity access distribution by continent ---

plt.figure(figsize=(20, 12))
df_access = df.copy()

# TRUQUE: Converter para Categórico ordenado
df_access['continent'] = pd.Categorical(
    df_access['continent'], 
    categories=sorted_continents, 
    ordered=True
)

box_access = df_access.boxplot(column='electricity_access', by='continent', figsize=(20, 12), patch_artist=True)

categories = box_access.get_xticklabels()
for patch, label in zip(box_access.patches, categories):
    continent_name = label.get_text()
    color = color_map[continent_name]
    patch.set_facecolor(color)
    patch.set_edgecolor('black')
    patch.set_linewidth(1)
    patch.set_alpha(0.7)

handles = [mpatches.Patch(facecolor=color_map[c], edgecolor='black', label=c, alpha=0.7) for c in sorted_continents]
plt.legend(handles=handles, title='Continente', fontsize=14, title_fontsize=16, loc='upper right')

plt.title('Distribuição do Acesso à Eletricidade por Continente', fontsize=30)
plt.suptitle('')
plt.xlabel('Continente', fontsize=24)
plt.ylabel('Acesso à Eletricidade (%)', fontsize=24)
plt.xticks(fontsize=16)
plt.yticks(fontsize=20)
plt.savefig(os.path.join(output_dir, 'boxplot_acesso_eletricidade_por_continente.png'))
plt.close()

print("Gráficos gerados e salvos em:", output_dir)