from flask import Flask, render_template
import json
import os
from main import abrir_arquivo

app = Flask(__name__)
data_path = abrir_arquivo("data/dadosenergiaPIB.json") # Caminho para o arquivo de dados processados.

# Função para ordenar os dados por eletricidade, tratando None como maior valor.
def ordenar_valores(e):
    v = e.get("electricity")
    return (v is None, -(v or 0))

def processa_dados():

    with open(data_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    grouped = {} # Dicionario para agrupar os dados por continente.

    for item in raw:
        country = item.get("country")
        # Pega os valores de eletricidade e PIB.
        records = item.get("records") or []
        electricity = None
        if records:
            first = records[0]
            electricity = first.get("value")

        pib_info = item.get("pib") or {}
        pib_value = pib_info.get("records")
        continent = pib_info.get("continent") or "Dados Globais" # Se não tiver continente, marca como Unknown.
        # É possivel não ter pais? Da para fazer isso sendo os dados "gerais"

        entry = {
            "country": country,
            "electricity": electricity,
            "pib": pib_value,
        }

        grouped.setdefault(continent, []).append(entry)

    # Cria a chave para apresentar todos os valores.
    all_list = []
    for lst in grouped.values():
        all_list.extend(lst)
    grouped["All"] = all_list

    # Para cada continente, ordenar por electricity (desc) — None vai para o final
    # Para ficar decrescente, se quiser alterar, só mudar essa chave.
    # Esta usando a função sort_key
    for k in grouped:
        grouped[k].sort(key=ordenar_valores)

    return grouped # Retorna os dados agrupados e ordenados para o front-end.

@app.route("/")
def index():
    data = processa_dados()
    # passe o dicionário para o template; usaremos tojson em Jinja
    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)