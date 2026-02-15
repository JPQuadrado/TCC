import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# --- 1. CARREGAMENTO DOS DADOS ---
try:
    df_nos = pd.read_csv('materias_nos.csv')
    df_arestas = pd.read_csv('materias_arestas.csv')
except FileNotFoundError:
    print("Arquivos não encontrados. Usando dados de exemplo.")
    df_nos = pd.DataFrame({'id': ['A', 'B', 'C', 'D'], 'nome': ['Mat A', 'Mat B', 'Mat C', 'Mat D'], 
                           'carga_horaria': [60, 60, 60, 60], 'prioridade': [1,2,3,4], 'obrigatoria': [1,1,1,1]})
    df_arestas = pd.DataFrame({'origem': ['A', 'B', 'A'], 'destino': ['B', 'C', 'C']})

G = nx.DiGraph()

for _, linha in df_nos.iterrows():
    G.add_node(linha['id'], nome=linha['nome'])

for _, linha in df_arestas.iterrows():
    G.add_edge(linha['origem'], linha['destino'])

# --- 2. FILTRAGEM ---
nos_com_conexoes = [v for v, d in G.degree() if d > 0]
G_filtrado = G.subgraph(nos_com_conexoes)

# --- 3. VISUALIZAÇÃO CUSTOMIZADA ---

plt.figure(figsize=(14, 10))

# LAYOUT
pos = nx.spring_layout(G_filtrado, k=3.0, iterations=100, seed=42)

# 1. Desenhar os NÓS (MUDANÇA AQUI: node_size=30)
nx.draw_networkx_nodes(
    G_filtrado, 
    pos,
    node_size=30,        # <--- Tamanho reduzido (era 100)
    node_color='black', 
    alpha=1.0            # Tirei a transparência para o ponto ficar bem nítido
)

# 2. Desenhar as ARESTAS
nx.draw_networkx_edges(
    G_filtrado, 
    pos,
    edge_color='gray',
    arrows=True,
    arrowsize=12,        # Reduzi um pouco a seta para acompanhar a bolinha menor
    width=0.8,
    alpha=0.5
)

# 3. Desenhar os RÓTULOS
# Ajuste fino: Reduzi o deslocamento para 0.04 para o texto ficar mais "colado" no ponto menor
pos_labels = {node: (coords[0], coords[1] + 0.04) for node, coords in pos.items()}

nx.draw_networkx_labels(
    G_filtrado, 
    pos_labels, 
    font_size=10, 
    font_color='black', 
    verticalalignment='bottom', 
    horizontalalignment='center'
)

plt.title("Grafo de Pré-requisitos", fontsize=16)
plt.axis('off') 
plt.margins(x=0.1, y=0.1) 
plt.tight_layout()
plt.show()