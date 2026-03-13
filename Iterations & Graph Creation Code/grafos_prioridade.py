import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

memo_prioridade = {}

def calcular_prioridade(disciplina_id):
    # Se já calculado, retorna o valor
    if disciplina_id in memo_prioridade:
        return memo_prioridade[disciplina_id]
    
    no = G.nodes[disciplina_id]
    
    alpha = 10 if no['obrigatoria'] == 1 else 1
    carga_h = no['carga_horaria']
    
    prioridade_v = alpha * carga_h
    
    for dependente in G.successors(disciplina_id):
        prioridade_v += calcular_prioridade(dependente)
    
    memo_prioridade[disciplina_id] = prioridade_v
    return prioridade_v

df_nos = pd.read_csv('materias_nos.csv')
df_arestas = pd.read_csv('materias_arestas.csv')

G = nx.DiGraph()

for _, linha in df_nos.iterrows():
    G.add_node(
        linha['id'], 
        nome=linha['nome'], 
        carga_horaria=int(linha['carga_horaria']),
        prioridade=int(linha['prioridade']),
        obrigatoria=int(linha['obrigatoria'])
    )

for _, linha in df_arestas.iterrows():
    G.add_edge(linha['origem'], linha['destino'])

for materia in G.nodes():
    G.nodes[materia]['prioridade'] = calcular_prioridade(materia)

df_nos['prioridade'] = df_nos['id'].apply(lambda x: G.nodes[x]['prioridade'])
df_nos.to_csv('materias_prioridades.csv', index=False)

print("Processamento concluído. Arquivo 'materias_prioridades.csv' gerado.")