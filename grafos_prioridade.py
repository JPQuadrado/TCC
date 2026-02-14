import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

memo_prioridade = {}

def calcular_prioridade(disciplina_id):
    # Se já calculado, retorna o valor
    if disciplina_id in memo_prioridade:
        return memo_prioridade[disciplina_id]
    
    no = G.nodes[disciplina_id]
    
    # Fator alpha: 10 para obrigatórias, 1 para optativas (conforme eq. 1 do artigo)
    alpha = 10 if no['obrigatoria'] == 1 else 1
    carga_h = no['carga_horaria']
    
    # Valor base da própria disciplina
    prioridade_v = alpha * carga_h
    
    # Soma a prioridade de todas as disciplinas que DEPENDEM desta (sucessores)
    # Isso garante que matérias que "abrem" o curso tenham valor maior
    for dependente in G.successors(disciplina_id):
        prioridade_v += calcular_prioridade(dependente)
    
    # Armazena e retorna
    memo_prioridade[disciplina_id] = prioridade_v
    return prioridade_v

# Carregar os dados dos arquivos CSV
df_nos = pd.read_csv('materias_nos.csv')
df_arestas = pd.read_csv('materias_arestas.csv')

# Criar a instância do Grafo Direcionado (DiGraph)
G = nx.DiGraph()

# Adicionar os nós e seus atributos (nome e carga horária)
for _, linha in df_nos.iterrows():
    G.add_node(
        linha['id'], 
        nome=linha['nome'], 
        carga_horaria=int(linha['carga_horaria']),
        prioridade=int(linha['prioridade']),
        obrigatoria=int(linha['obrigatoria'])
    )

# Adicionar as arestas (conexões de pré-requisito)
for _, linha in df_arestas.iterrows():
    G.add_edge(linha['origem'], linha['destino'])

# 4. Executar o cálculo para todas as matérias
for materia in G.nodes():
    G.nodes[materia]['prioridade'] = calcular_prioridade(materia)

# 5. Salvar os resultados de volta no CSV
df_nos['prioridade'] = df_nos['id'].apply(lambda x: G.nodes[x]['prioridade'])
df_nos.to_csv('materias_prioridades.csv', index=False)

print("Processamento concluído. Arquivo 'materias_prioridades.csv' gerado.")