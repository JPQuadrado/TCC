import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

import networkx as nx
import pandas as pd

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

# Exemplo de verificação da leitura
print(f"Nós carregados: {G.number_of_nodes()}")
print(f"Arestas carregadas: {G.number_of_edges()}")

nx.draw_spring(G, with_labels=True, font_size='small')
plt.show()