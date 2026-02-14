import pulp
import pandas as pd

def otimizar_plano_estudos(arq_prioridades, arq_turmas, arq_arestas, arq_aluno_pendencias):
    print(f"--- Iniciando Otimização (Prioridade Pré-Calculada) ---")

    # 1. CARREGAMENTO DOS DADOS
    try:
        df_prioridades = pd.read_csv(arq_prioridades)
        df_turmas = pd.read_csv(arq_turmas)
        df_arestas = pd.read_csv(arq_arestas)
        df_pendencias = pd.read_csv(arq_aluno_pendencias)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e.filename}")
        return

    # 2. DEFINIÇÃO DOS CONJUNTOS
    todas_materias = set(df_prioridades['id'].unique())
    pendencias_ids = set(df_pendencias['id_materia'].unique())
    
    # S = V - P (Concluídas são todas menos as pendentes)
    concluidas_ids = todas_materias - pendencias_ids
    
    # Mapeamento de Pré-requisitos
    grafo_requisitos = {}
    for _, row in df_arestas.iterrows():
        origem, destino = row['origem'], row['destino']
        if destino not in grafo_requisitos:
            grafo_requisitos[destino] = []
        grafo_requisitos[destino].append(origem)
        
    # Identificar Elegíveis (R): Pendentes com requisitos OK e Ofertadas
    elegiveis_finais = []
    materias_ofertadas = set(df_turmas['id_materia'].unique())

    for materia in pendencias_ids:
        # Checa requisitos
        requisitos = grafo_requisitos.get(materia, [])
        requisitos_ok = all(req in concluidas_ids for req in requisitos)
        
        # Checa oferta
        ofertada = materia in materias_ofertadas
        
        if requisitos_ok and ofertada:
            elegiveis_finais.append(materia)

    print(f"Disciplinas candidatas (Elegíveis + Ofertadas): {len(elegiveis_finais)}")

    if not elegiveis_finais:
        print("Nenhuma disciplina disponível para matrícula.")
        return

    # 3. MODELAGEM (PuLP)
    prob = pulp.LpProblem("Otimizacao_Horario", pulp.LpMaximize)
    
    dados_materia = df_prioridades.set_index('id').to_dict('index')
    df_oferta_final = df_turmas[df_turmas['id_materia'].isin(elegiveis_finais)]
    
    # Variáveis de Decisão x_ik
    vars_x = {}
    for _, row in df_oferta_final.iterrows():
        m_id, t_id = row['id_materia'], row['id_turma']
        vars_x[(m_id, t_id)] = pulp.LpVariable(f"x_{m_id}_{t_id}", cat='Binary')

    # --- CORREÇÃO AQUI ---
    # Função Objetivo: Maximizar APENAS a Prioridade (já calculada)
    prob += pulp.lpSum([
        vars_x[(m, t)] * dados_materia[m]['prioridade']
        for (m, t) in vars_x.keys()
    ])
    
    # Restrições (Mantidas)
    # 1. Unicidade
    for m_id in elegiveis_finais:
        turmas = [vars_x[k] for k in vars_x if k[0] == m_id]
        if turmas: prob += pulp.lpSum(turmas) <= 1

    # 2. Conflito de Horários
    mapa_slots = {}
    for _, row in df_oferta_final.iterrows():
        m_id, t_id = row['id_materia'], row['id_turma']
        slots = [s.strip().replace('"', '').replace("'", "") for s in str(row['slots']).split(',')]
        for s in slots:
            if s:
                if s not in mapa_slots: mapa_slots[s] = []
                mapa_slots[s].append(vars_x[(m_id, t_id)])
            
    for slot, lista_vars in mapa_slots.items():
        prob += pulp.lpSum(lista_vars) <= 1

    # 4. RESOLVER
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if pulp.LpStatus[prob.status] == 'Optimal':
        print("\n=== GRADE SUGERIDA ===")
        resultado = []
        for (m, t), var in vars_x.items():
            if pulp.value(var) == 1:
                resultado.append({
                    "Disciplina": dados_materia[m]['nome'],
                    "Turma": t,
                    "Prioridade": dados_materia[m]['prioridade'],
                    "Slots": df_turmas[(df_turmas['id_materia']==m) & (df_turmas['id_turma']==t)]['slots'].values[0]
                })
        print(pd.DataFrame(resultado).to_string(index=False))
    else:
        print("Solução ótima não encontrada.")

# Exemplo:
otimizar_plano_estudos('materias_prioridades.csv', 'turmas.csv', 'materias_arestas.csv', 'aluno1_elegiveis.csv')
otimizar_plano_estudos('materias_prioridades.csv', 'turmas.csv', 'materias_arestas.csv', 'aluno2_elegiveis.csv')