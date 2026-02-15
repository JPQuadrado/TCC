import pulp
import pandas as pd

def otimizar_plano_estudos(arq_prioridades, arq_turmas, arq_arestas, arq_aluno_pendencias, horarios_indisponiveis=None):
    
    # Se não for passada uma lista, assume que o aluno tem disponibilidade total
    if horarios_indisponiveis is None:
        horarios_indisponiveis = []
        
    print(f"\n--- Iniciando Otimização (Prioridade Pré-Calculada) ---")
    if horarios_indisponiveis:
        print(f"Filtro ativo: O aluno NÃO pode cursar turmas nos horários: {horarios_indisponiveis}")

    # 1. CARREGAMENTO DOS DADOS
    try:
        df_prioridades = pd.read_csv(arq_prioridades)
        df_turmas = pd.read_csv(arq_turmas)
        df_arestas = pd.read_csv(arq_arestas)
        df_pendencias = pd.read_csv(arq_aluno_pendencias)
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e.filename}")
        return

    # 2. DEFINIÇÃO DOS CONJUNTOS E DADOS
    todas_materias = set(df_prioridades['id'].unique())
    pendencias_ids = set(df_pendencias['id_materia'].unique())
    
    # Disciplinas já concluídas
    concluidas_ids = todas_materias - pendencias_ids
    
    dados_materia = df_prioridades.set_index('id').to_dict('index')
    
    # Mapeamento de Pré-requisitos
    grafo_requisitos = {}
    for _, row in df_arestas.iterrows():
        origem, destino = row['origem'], row['destino']
        if destino not in grafo_requisitos:
            grafo_requisitos[destino] = []
        grafo_requisitos[destino].append(origem)
        
    # Identificar Matérias Elegíveis (Requisitos cumpridos + Ofertadas)
    elegiveis_finais = []
    materias_ofertadas = set(df_turmas['id_materia'].unique())

    for materia in pendencias_ids:
        # Checa pré-requisitos
        requisitos = grafo_requisitos.get(materia, [])
        requisitos_ok = all(req in concluidas_ids for req in requisitos)
        
        # Checa se há oferta
        ofertada = materia in materias_ofertadas
        
        if requisitos_ok and ofertada:
            elegiveis_finais.append(materia)

    print(f"Disciplinas candidatas (Elegíveis + Ofertadas): {len(elegiveis_finais)}")

    if not elegiveis_finais:
        print("Nenhuma disciplina disponível para matrícula.")
        return

    # 3. MODELAGEM (PuLP)
    prob = pulp.LpProblem("Otimizacao_Horario", pulp.LpMaximize)
    
    # Filtra apenas as turmas das matérias elegíveis
    df_oferta_final = df_turmas[df_turmas['id_materia'].isin(elegiveis_finais)]
    
    # --- VARIÁVEIS DE DECISÃO COM FILTRO DE INDISPONIBILIDADE ---
    vars_x = {}
    
    for _, row in df_oferta_final.iterrows():
        m_id, t_id = row['id_materia'], row['id_turma']
        
        # Limpeza e separação dos slots da turma
        raw_slots = str(row['slots']).split(',')
        slots_turma = [s.strip().replace('"', '').replace("'", "") for s in raw_slots if s.strip()]
        
        # VERIFICAÇÃO CRÍTICA:
        # Se a turma tiver QUALQUER horário que esteja na lista de proibidos, ignoramos essa turma.
        conflito_com_agenda = any(slot in horarios_indisponiveis for slot in slots_turma)
        
        if conflito_com_agenda:
            # Pula esta iteração, ou seja, a variável x_ik nem é criada.
            # O solver agirá como se essa turma não existisse.
            continue
            
        # Cria a variável se passou no filtro
        vars_x[(m_id, t_id)] = pulp.LpVariable(f"x_{m_id}_{t_id}", cat='Binary')

    # Verifica se sobrou alguma turma após os filtros
    if not vars_x:
        print("Aviso: Não há turmas disponíveis. Todas conflitam com os horários indisponíveis informados.")
        return

    # Função Objetivo: Maximizar Prioridade
    prob += pulp.lpSum([
        vars_x[(m, t)] * dados_materia[m]['prioridade']
        for (m, t) in vars_x.keys()
    ])
    
    # Restrições
    
    # 1. Unicidade: Aluno não pode fazer a mesma matéria em duas turmas diferentes
    for m_id in elegiveis_finais:
        turmas_desta_materia = [vars_x[k] for k in vars_x if k[0] == m_id]
        if turmas_desta_materia: 
            prob += pulp.lpSum(turmas_desta_materia) <= 1

    # 2. Conflito de Horários (Choque entre turmas selecionadas)
    # Mapeia cada slot para a lista de variáveis que o ocupam
    mapa_slots_ocupados = {}
    
    for (m_id, t_id), var in vars_x.items():
        # Busca os slots novamente para montar a restrição
        slots_raw = df_oferta_final[(df_oferta_final['id_materia'] == m_id) & (df_oferta_final['id_turma'] == t_id)]['slots'].values[0]
        slots = [s.strip().replace('"', '').replace("'", "") for s in str(slots_raw).split(',') if s.strip()]
        
        for s in slots:
            if s not in mapa_slots_ocupados: 
                mapa_slots_ocupados[s] = []
            mapa_slots_ocupados[s].append(var)
            
    # Para cada slot, a soma das variáveis deve ser <= 1
    for slot, lista_vars in mapa_slots_ocupados.items():
        prob += pulp.lpSum(lista_vars) <= 1

    # 4. RESOLVER
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    # 5. RESULTADOS
    if pulp.LpStatus[prob.status] == 'Optimal':
        print("\n=== GRADE SUGERIDA ===")
        resultado = []
        prioridade_acumulada = 0
        
        for (m, t), var in vars_x.items():
            if pulp.value(var) == 1:
                prioridade_acumulada += dados_materia[m]['prioridade']
                slots_str = df_turmas[(df_turmas['id_materia']==m) & (df_turmas['id_turma']==t)]['slots'].values[0]
                
                resultado.append({
                    "Disciplina": dados_materia[m]['nome'],
                    "Turma": t,
                    "Prioridade": dados_materia[m]['prioridade'],
                    "Slots": slots_str
                })
        
        if resultado:
            df_res = pd.DataFrame(resultado)
            df_res = df_res.sort_values(by='Prioridade', ascending=False)
            print(df_res.to_string(index=False))
            print(f"\nTotal de Prioridade Obtida: {prioridade_acumulada}")
        else:
            print("Nenhuma matéria foi selecionada (verifique se os horários disponíveis permitem combinações).")
    else:
        print("Solução ótima não encontrada.")

# --- EXEMPLOS DE USO ---

# Exemplo 1: Aluno não pode na Segunda-feira (horários 03 e 04)
print("\n>>> ALUNO 1 - COM RESTRIÇÕES")
indisponiveis_aluno1 = ["SEG01", "SEG02", "SEX01", "SEX02"]
otimizar_plano_estudos(
    'materias_prioridades.csv', 
    'turmas.csv', 
    'materias_arestas.csv', 
    'aluno01_elegiveis.csv',
    horarios_indisponiveis=indisponiveis_aluno1
)

# Exemplo 3: Sem restrições de horário
print("\n>>> ALUNO 1 - SEM RESTRIÇÕES")
otimizar_plano_estudos(
    'materias_prioridades.csv', 
    'turmas.csv', 
    'materias_arestas.csv', 
    'aluno01_elegiveis.csv'
)