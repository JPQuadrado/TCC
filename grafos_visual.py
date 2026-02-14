import networkx as nx
import matplotlib.pyplot as plt
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

# 1. Identificar os nós que possuem pelo menos uma conexão (grau > 0)
nos_com_conexoes = [v for v, d in G.degree() if d > 0]

# 2. Criar um subgrafo contendo apenas esses nós
G_filtrado = G.subgraph(nos_com_conexoes)

# 3. Desenhar o grafo filtrado
plt.figure(figsize=(12, 10))
# pos = nx.spring_layout(G_filtrado, k=0.5) # Ajuste o k para afastar os nós
pos = nx.shell_layout(G_filtrado) # Ajuste o k para afastar os nós
nx.draw(G_filtrado, pos, 
        with_labels=True, 
        font_size='small', 
        arrows=True)

# Em ambientes de script/notebook use plt.savefig para gerar o arquivo da imagem
plt.show()