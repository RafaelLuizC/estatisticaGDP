import dotenv
import os, nltk, re, json
import pandas as pd
import xml.etree.ElementTree as ET

dotenv.load_dotenv()

def mergeJsons(json1_path, json2_path, threshold=0.85): # Função para fazer merge de dois JSONs com os dados de países.

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
        # aceita lista de objetos {"country":..., "records":...} ou dict {country: records}
        
        if isinstance(obj, list): # Se for lista, retorna como está.
            return obj
        
        if isinstance(obj, dict): # Se for dicionário, converte para lista de objetos.
            items = [] # inicia lista
            for k, v in obj.items():
                items.append({"country": k, "records": v}) # Adiciona o país e seus registros.
            return items
        return []

    # Eu sei que a, e b são nomes ruins
    a = load_json(json1_path) if isinstance(json1_path, str) else json1_path # Carrega o JSON 1
    b = load_json(json2_path) if isinstance(json2_path, str) else json2_path # Carrega o JSON 2 

    
    # A = Dados de Energia dos paises.
    # B = Dados de PIB dos paises.

    a_entries = entries_from(a) # Extrai os dados do JSON 1
    b_entries = entries_from(b) # Extrai os dados do JSON 2

    # Se a comparação já for exata, usa índice para acelerar o processo, e não precisa calcular distância.
    b_index = { normalize(item.get("country")): item for item in b_entries if item.get("country") } 

    merged = [] # Inicia a lista de resultados mesclados.

    # Aqui ele faz a busca percorrendo os países do JSON A (Energia)
    for a_item in a_entries:
        a_name = a_item.get("country")
        best = None
        best_score = -1.0
        norm_a = normalize(a_name)

        # Procura a correspondencia exata = valores 1.0 
        if norm_a in b_index:
            best = b_index[norm_a]
            best_score = 1.0
        
        # Se não encontrar, ele calcula a distancia entre os nomes.
        else:
            for b_item in b_entries:
                b_name = b_item.get("country")
                norm_b = normalize(b_name) # normaliza o nome do país B
                if not norm_b:
                    continue
                
                # Similaridade entre as strings baseada em edit distance
                dist = nltk.edit_distance(norm_a, norm_b)
                maxlen = max(len(norm_a), len(norm_b), 1)
                
                # Calcula a distancia. - O Valor vai de 0-1, e o treshold padrão é de 0.85
                # Da para reduzir esse valor no argumento da função.
                sim = 1.0 - (dist / maxlen) 
                if sim > best_score:
                    best_score = sim
                    best = b_item

            # Faz uma segunda busca, caso não tenha encontrado nada acima do treshold.
            if best_score < threshold:
                tokens_a = set(norm_a.split())
                best_tok = None
                best_j = 0.0

                # Busca por similaridade de Jaccard, outro metodo que tem na NLTK.
                for b_item in b_entries:
                    tokens_b = set(normalize(b_item.get("country","")).split())
                    if not tokens_a or not tokens_b:
                        continue
                    j = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
                    if j > best_j:
                        best_j = j
                        best_tok = b_item
                
                if best_j > 0.6 and best_j > best_score:
                    # Se encontrou algo bom o suficiente.
                    best = best_tok
                    best_score = best_j

        merged_item = dict(a_item)  # Captura os dados do país A (Energia)
        
        if best and best_score >= threshold: # Se encontrou um país B (PIB) correspondente acima do treshold
            # Adiciona os dados do PIB, estou consumindo os valores de 2023.
            merged_item["pib"] = {"country": best.get("country"), "records": best.get("un_2023")}
        else:
            # Se não encontrou, deixa o PIB como None.
            merged_item["pib"] = None

        merged.append(merged_item)

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

    arquivo = "ListaEnergia.xml"
    caminho = abrir_arquivo(arquivo) #Gera o caminho

    # Gera o JSON agrupado por país
    country_data = iniciaJsonPaises(caminho)

    saida = "DadosEnergia.json"
    salvaJson(country_data, saida)

    # Agora faz merge com o PIB.json (assume PIB.json está na raiz do projeto)
    pib_path = "PIB.json"
    if not os.path.exists(pib_path):
        print("Arquivo PIB.json não encontrado. Merge não realizado.")
        print("Rodou o codigo!")
        return

    merged = mergeJsons(saida, pib_path, threshold=0.85)
    saida_merge = "dadosenergiaPIB.json"
    salvaJson(merged, saida_merge)

    print("Merge gerado em:", saida_merge)
    print("Rodou o codigo!")



if __name__ == "__main__":
    main()
