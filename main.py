import dotenv
import os, nltk, re, json, csv
import pandas as pd
import xml.etree.ElementTree as ET


dotenv.load_dotenv()

def create_csv_json(data):
    with open('/workspaces/estatisticaGDP/data/dados.csv', 'w', newline='', encoding='utf-8') as csv_file:
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            print("CSV file created successfully: ./dados.csv")

def mergeJsons(json1_path, json2_path, threshold=0.7): # Função para fazer merge de dois JSONs com os dados de países.
    def load_json(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def normalize(s):
        if s is None:
            return ""
        s = s.lower()
        s = re.sub(r'[^a-z0-9\s]', ' ', s, flags=re.UNICODE)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def entries_from(obj):
        if isinstance(obj, list):
            return obj
        if isinstance(obj, dict):
            items = []
            for k, v in obj.items():
                items.append({"country": k, "records": v})
            return items
        return []

    a = load_json(json1_path) if isinstance(json1_path, str) else json1_path
    b = load_json(json2_path) if isinstance(json2_path, str) else json2_path

    a_entries = entries_from(a)
    b_entries = entries_from(b)

    b_index = { normalize(item.get("country")): item for item in b_entries if item.get("country") }

    # mapa de continentes para Português
    continent_map = {
        'asia': 'Ásia', 'europe': 'Europa', 'africa': 'África',
        'north america': 'América do Norte', 'south america': 'América do Sul',
        'oceania': 'Oceania', 'antarctica': 'Antártica', 'central america': 'América Central'
    }

    merged = []

    for a_item in a_entries:
        a_name = a_item.get("country")
        norm_a = normalize(a_name)
        a_name_short = a_name.split(",")[0] if isinstance(a_name, str) else a_name

        best = None
        best_score = -1.0

        if norm_a in b_index:
            best = b_index[norm_a]
            best_score = 1.0
        else:
            for b_item in b_entries:
                b_name = b_item.get("country")
                norm_b = normalize(b_name)
                if not norm_b:
                    continue
                dist = nltk.edit_distance(norm_a, norm_b)
                maxlen = max(len(norm_a), len(norm_b), 1)
                sim = 1.0 - (dist / maxlen)
                if sim > best_score:
                    best_score = sim
                    best = b_item

            if best_score < threshold:
                tokens_a = set(norm_a.split())
                best_tok = None
                best_j = 0.0
                for b_item in b_entries:
                    tokens_b = set(normalize(b_item.get("country","")).split())
                    if not tokens_a or not tokens_b:
                        continue
                    j = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
                    if j > best_j:
                        best_j = j
                        best_tok = b_item
                if best_j > 0.6 and best_j > best_score:
                    best = best_tok
                    best_score = best_j

        # Extrai o valor de acesso à eletricidade (ano 2023) do registro de energia
        elec_val = None
        for rec in a_item.get("records", []) or []:
            if isinstance(rec, dict) and rec.get("year") == 2023:
                elec_val = rec.get("value")
                break
        if elec_val is None:
            # fallback: usa o primeiro registro disponível
            if a_item.get("records"):
                first = (a_item.get("records")[0])
                if isinstance(first, dict):
                    elec_val = first.get("value")

        if best and best_score >= threshold:
            gdp_val = best.get("un_2023")
            cont = best.get("continent")
            cont_trans = None
            if isinstance(cont, str):
                cont_trans = continent_map.get(cont.strip().lower(), cont)
        else:
            gdp_val = None
            cont_trans = None

        if gdp_val is None or elec_val is None:
            print(f"Nenhum país correspondente encontrado para '{a_name_short}' (melhor score: {best_score:.3f})")
            continue

        merged.append({
            "country": a_name_short,
            "electricity_access": elec_val,
            "gdp": gdp_val,
            "continent": cont_trans
        })

    return merged

def abrir_arquivo(nome_arquivo): # Função para gerar o caminho absoluto do arquivo.
    arquivo = os.path.abspath(nome_arquivo)
    
    try:
        if not os.path.exists(arquivo): # Se achou
            raise FileNotFoundError
        return arquivo
    
    except FileNotFoundError: # Se o arquivo não for encontrado, te avisa.
        print('Arquivo não encontrado:', arquivo)
        
        return None

def salvaJson(obj, caminho_saida):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2) # Só salva o JSON com indentacao.

def parserXML(arquivo):
    tree = ET.parse(arquivo)
    root = tree.getroot()

    rows = [] # Inicia a lista com os valores de ai meu deus, o PIB.

    # Percorre todos os registros no XML, de acordo com a estrutura do documento original.
    # "//record/field" 
    
    for rec in root.findall('.//record'):
        # Para cada registro, cria um dicionário para armazenar os dados.
        row = {} # Inicia o dicionario.

        for f in rec.findall('field'):
            name = f.attrib.get('name') # Pega o nome do campo.
            text = f.text.strip() if f.text and f.text.strip() else None 
            
            if name: # Se o nome desse campo existir, ele deve ser adicionado ao dicionário.
                row[name] = text
                key = f.attrib.get('key')
                if key:
                    row[f"{name}_key"] = key
        rows.append(row)

    return pd.DataFrame(rows) # Retorna o DataFrame com os dados extraídos.

def iniciaJsonPaises(arquivo):

    # Inicia o Dataframe a partir do XML.
    df = parserXML(arquivo)

    # Ve se coloquei o XML correto, tem que ter "Year", "Country or Area" e "Value"
    if 'Country or Area' not in df.columns or 'Year' not in df.columns or 'Value' not in df.columns:
        # Se as colunas esperadas não existirem, tenta lidar sem quebrar.
        print("Colunas esperadas não encontradas.")
    
    # Limpa artefatos e espaços em branco dos nomes das colunas
    df = df.rename(columns=lambda c: c.strip() if isinstance(c, str) else c)
    
    # Limpa espaços em branco nas colunas relevantes
    df_country = df[['Country or Area','Year','Value']].copy() if set(['Country or Area','Year','Value']).issubset(df.columns) else df.copy()

    result = [] # Inicia o array de resultado

    # Agrupa por país e inicia a montagem da estrutura.
    for country, group in df_country.groupby('Country or Area', dropna=True):
        records = []
        
        # Para cada linha do grupo, tenta extrair ano e valor.
        for _, row in group.iterrows():
            year_raw = row.get('Year')
            value_raw = row.get('Value')

            try:
                # Tenta converter o ano para int
                year = int(year_raw) if year_raw is not None else None
            
            except Exception:
                # Se o ano não for conversível, pula esse registro
                continue

            # Tenta converter o valor para float -  recebe None ou vazio.
            if value_raw is None or (isinstance(value_raw, str) and value_raw.strip() == ""):
                value = None
            else:
                try:
                    value = float(value_raw)
                except Exception:
                    # Se não converter, o valor é tratado como string
                    value = value_raw


            # Filtra apenas valores a partir de 2023, e com valor não nulo
            # Como 2024 ainda não tem dados, não será incluído.
            if year is not None and year >= 2023 and value is not None:
                records.append({"year": year, "value": value})

        # Ordena os registros por ano, mas como somente um ano esta sendo utilizado, essas ordenações não terão efeito.
        records.sort(key=lambda x: (x['year'] is None, x['year']))
        result.append({"country": country, "records": records})

    # Ordena os países por nome.
    result.sort(key=lambda x: x['country'] or "")
    return result # Retorna o array de países.


def main():
    #Inicializa as tabelas de Dados.

    arquivo = "data/ListaEnergia.xml"
    caminho = abrir_arquivo(arquivo) #Gera o caminho

    # Gera o JSON agrupado por país
    country_data = iniciaJsonPaises(caminho)

    saida = "data/tempJSON.json"
    salvaJson(country_data, saida)

    # Agora faz merge com o PIB.json (assume PIB.json está na raiz do projeto)
    pib_path = "data/PIB.json"
    if not os.path.exists(pib_path):
        print("Arquivo PIB.json não encontrado. Merge não realizado.")
        print("Rodou o codigo!")
        return

    merged = mergeJsons(saida, pib_path, threshold=0.85)
    saida_merge = "data/dados.json"
    salvaJson(merged, saida_merge)

    print("Merge gerado em:", saida_merge)
    print("Rodou o codigo!")

if __name__ == "__main__":
    main()