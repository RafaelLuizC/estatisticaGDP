import json
import os
import sys
import pandas as pd
import numpy as np

# --- Configuração de Caminhos ---
base_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base_dir, 'dados.json')
output_path = os.path.join(base_dir, 'dados.txt')

# --- Carregamento de Dados ---
try:
    with open(json_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
except FileNotFoundError:
    try:
        json_path = os.path.join(base_dir, '..', 'data', 'dados.json')
        with open(json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        print(f"Erro Crítico: Arquivo 'dados.json' não encontrado em {base_dir}")
        exit()

df = pd.DataFrame(data)
df['gdp_million'] = df['gdp'] * 1_000_000

# --- Configuração do Pandas ---
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# --- Função de Formatação (T, B, M) ---
def format_human_readable(x):
    """Converte números grandes para formato curto (ex: 1.5T, 30.2B, 500M)"""
    if pd.isna(x):
        return "-"
    if x >= 1e12:
        return f'{x/1e12:.1f}T'
    elif x >= 1e9:
        return f'{x/1e9:.1f}B'
    elif x >= 1e6:
        return f'{x/1e6:.1f}M'
    else:
        return f'{x:,.0f}'

# --- Função Principal de Geração de Relatório ---
def gerar_conteudo_relatorio():
    print("="*60)
    print("RELATÓRIO DE DADOS DOS GRÁFICOS (EM PORTUGUÊS)")
    print("="*60)
    print("\n")

    # --- 1. Países por Continente ---
    print("-" * 40)
    print("1. Distribuição de Países por Continente")
    print("-" * 40)
    continent_counts = df['continent'].value_counts()
    continent_pct = df['continent'].value_counts(normalize=True) * 100
    df_counts = pd.DataFrame({'Total Países': continent_counts, 'Porcentagem (%)': continent_pct})
    print(df_counts.to_string())
    print("\n")

    # --- 2. Média Acesso Eletricidade ---
    print("-" * 40)
    print("2. Média de Acesso à Eletricidade por Continente")
    print("-" * 40)
    avg_electricity = df.groupby('continent')['electricity_access'].mean().sort_values(ascending=False)
    print(avg_electricity.to_string(float_format="%.2f%%"))
    print("\n")

    # --- 3. Média PIB ---
    print("-" * 40)
    print("3. Média do PIB por Continente (Formatado)")
    print("-" * 40)
    avg_gdp = df.groupby('continent')['gdp_million'].mean().sort_values(ascending=False)
    
    # Aplica a formatação simplificada
    print(avg_gdp.apply(format_human_readable).to_string())
    print("(Legenda: T = Trilhões, B = Bilhões, M = Milhões de US$)")
    print("\n")

    # --- 4. Correlação ---
    print("-" * 40)
    print("4. Correlação entre PIB e Acesso à Eletricidade")
    print("-" * 40)
    print("Nota: A correlação varia de -1 a 1.")
    print("      1 = Crescem juntos perfeitamente.")
    print("      0 = Não tem relação nenhuma.")
    print("    NaN = Dados constantes (sem variação para calcular).\n")

    corr_geral = df['gdp_million'].corr(df['electricity_access'])
    print(f"Correlação Geral (Pearson): {corr_geral:.4f}")

    print("\nCorrelação por Continente:")
    corrs = df.groupby('continent')[['gdp_million', 'electricity_access']].corr().iloc[0::2, -1]
    corrs.index = corrs.index.droplevel(1)
    
    corrs_formatted = corrs.apply(lambda x: "Constante (100% fixo)" if pd.isna(x) else f"{x:.4f}")
    print(corrs_formatted.to_string())
    print("\n")

    # --- 5. Acesso > 90% ---
    print("-" * 40)
    print("5. Países com Acesso à Eletricidade > 90%")
    print("-" * 40)
    above_90 = df[df['electricity_access'] > 90].shape[0]
    below_90 = df[df['electricity_access'] <= 90].shape[0]
    total = above_90 + below_90
    print(f"Acima de 90%: {above_90} países ({above_90/total*100:.1f}%)")
    print(f"Abaixo ou igual a 90%: {below_90} países ({below_90/total*100:.1f}%)")
    print("\n")

    # --- 6. Amplitude Acesso ---
    print("-" * 40)
    print("6. Amplitude de Acesso à Eletricidade (Max/Min)")
    print("-" * 40)
    agg_access = df.groupby('continent')['electricity_access'].agg(['max', 'min'])
    agg_access['Amplitude'] = agg_access['max'] - agg_access['min']
    agg_access.rename(columns={'max': 'Máximo', 'min': 'Mínimo'}, inplace=True)
    print(agg_access.to_string(float_format="%.2f%%"))
    print("\n")

    # --- 7. Estatísticas do PIB ---
    print("-" * 40)
    print("7. Estatísticas Descritivas do PIB por Continente")
    print("-" * 40)
    desc_gdp = df.groupby('continent')['gdp_million'].describe()

    traducao_cols = {
        'count': 'Contagem',
        'mean': 'Média',
        'std': 'Desvio Padrão',
        'min': 'Mínimo',
        '25%': 'Q1 (25%)',
        '50%': 'Mediana',
        '75%': 'Q3 (75%)',
        'max': 'Máximo'
    }
    desc_gdp.rename(columns=traducao_cols, inplace=True)
    desc_gdp['Amplitude'] = desc_gdp['Máximo'] - desc_gdp['Mínimo']

    # Selecionar colunas
    colunas_exibir = ['Média', 'Mediana', 'Mínimo', 'Máximo', 'Amplitude', 'Desvio Padrão']
    subset_gdp = desc_gdp[colunas_exibir]

    # Aplicar formatação (T, B, M) em todas as colunas numéricas selecionadas
    # Usamos apply com map para garantir compatibilidade
    subset_formatted = subset_gdp.apply(lambda col: col.map(format_human_readable))
    
    print(subset_formatted.to_string())
    print("(Legenda: T = Trilhões, B = Bilhões, M = Milhões de US$)")
    print("\n")

    # --- 8. Estatísticas Acesso Eletricidade ---
    print("-" * 40)
    print("8. Estatísticas Descritivas de Acesso à Eletricidade")
    print("-" * 40)
    pd.options.display.float_format = '{:.2f}'.format
    desc_access = df.groupby('continent')['electricity_access'].describe()
    desc_access.rename(columns=traducao_cols, inplace=True)

    colunas_exibir_elec = ['Média', 'Mediana', 'Mínimo', 'Máximo', 'Desvio Padrão']
    print(desc_access[colunas_exibir_elec].to_string())
    print("(Valores em %)")
    print("\n")
    print("="*60)

# --- Gerenciamento de Arquivo Seguro ---
target_file = output_path
try:
    print(f"Tentando salvar relatório em: {target_file}...")
    with open(target_file, 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = f
        gerar_conteudo_relatorio()
        sys.stdout = original_stdout
    print("Sucesso! O arquivo 'dados.txt' foi atualizado.")

except PermissionError:
    target_file = os.path.join(base_dir, 'dados_novo.txt')
    print(f"AVISO: O arquivo 'dados.txt' está aberto e bloqueado.")
    print(f"Salvando como '{os.path.basename(target_file)}' em vez disso...")
    
    with open(target_file, 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = f
        gerar_conteudo_relatorio()
        sys.stdout = original_stdout
    print("Sucesso! Relatório salvo no novo arquivo.")