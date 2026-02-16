import pulp
import pandas as pd

def otimizar_plano_estudos(arq_prioridades, arq_turmas, arq_arestas, arq_aluno_pendencias, 
                           horarios_indisponiveis=None, qtd_optativas=0):
    
    if horarios_indisponiveis is None: 
        horarios_indisponiveis = []

    print(f"Meta de Optativas: Máximo {qtd_optativas}")
    if horarios_indisponiveis:
        print(f"Horários Bloqueados: {horarios_indisponiveis}")

    # ====================================================
    # 1. CARREGAMENTO DOS DADOS
    # ====================================================
    try:
        df_dados = pd.read_csv(arq_prioridades)
        df_turmas = pd.read_csv(arq_turmas)
        df_arestas = pd.read_csv(arq_arestas)
        df_pendencias = pd.read_csv(arq_aluno_pendencias)
    except FileNotFoundError as e:
        print(f"Erro Crítico: Arquivo não encontrado - {e.filename}")
        return

    # ====================================================
    # 2. PRÉ-PROCESSAMENTO (GRAFOS E CONJUNTOS)
    # ====================================================
    
    dados_materia = df_dados.set_index('id').to_dict('index')
    # print(dados_materia)
    
    # Histórico e Pendências
    todas_materias = set(df_dados['id'].unique())
    pendencias_ids = set(df_pendencias['id_materia'].unique())
    concluidas_ids = todas_materias - pendencias_ids
    
    # Grafo de Pré-requisitos
    grafo_req = {}
    for _, row in df_arestas.iterrows():
        grafo_req.setdefault(row['destino'], []).append(row['origem'])
    
    # print(grafo_req)

    # --- DEFINIÇÃO DOS CONJUNTOS MATEMÁTICOS ---
    
    # Conjunto R: Todas as Matérias Elegíveis
    # Critério: (Pré-requisitos Cumpridos) E (Existe Oferta de Turma)
    R = [] 
    materias_ofertadas = set(df_turmas['id_materia'].unique())

    for m in pendencias_ids:
        reqs = grafo_req.get(m, [])
        requisitos_ok = all(r in concluidas_ids for r in reqs)
        
        if requisitos_ok and (m in materias_ofertadas):
            R.append(m)

    # Conjunto R_opt: Subconjunto de R contendo apenas Optativas
    # Critério: m pertence a R E obrigatoria == 0
    R_opt = [m for m in R if dados_materia[m].get('obrigatoria', 1) == 0]

    print(f"Conjunto R (Elegíveis totais): {len(R)}")
    print(f"Subconjunto R_opt (Optativas elegíveis): {len(R_opt)}")

    if not R:
        print("Nenhuma matéria elegível disponível para matrícula.")
        return

    # ====================================================
    # 3. MODELAGEM (PuLP)
    # ====================================================
    prob = pulp.LpProblem("Grade_Horaria_Otimizada", pulp.LpMaximize)
    
    # Filtra o DataFrame de turmas para usar apenas matérias de R
    df_oferta_R = df_turmas[df_turmas['id_materia'].isin(R)]
    
    # Variáveis de Decisão: x_ik (matéria i, turma k)
    vars_x = {}
    info_slots = {} # OTIMIZAÇÃO: Armazena slots limpos para uso posterior

    for _, row in df_oferta_R.iterrows():
        i, k = row['id_materia'], row['id_turma']
        
        # Parse dos slots (Ex: "SEG01, SEG02" -> ['SEG01', 'SEG02'])
        raw_slots = str(row['slots']).split(',')
        slots_turma = [s.strip().replace('"', '').replace("'", "") for s in raw_slots if s.strip()]
        
        # Filtro de Indisponibilidade (Conjunto U do modelo)
        # Se a turma colide com horário bloqueado pelo aluno, nem cria a variável (x_ik = 0)
        if any(s in horarios_indisponiveis for s in slots_turma):
            continue 
            
        vars_x[(i, k)] = pulp.LpVariable(f"x_{i}_{k}", cat='Binary')
        info_slots[(i, k)] = slots_turma # Guarda para exibir e verificar choque

    if not vars_x:
        print("Não há turmas disponíveis (todas conflitam com os horários bloqueados).")
        return

    # --- EQUAÇÕES DO MODELO MATEMÁTICO ---

    # (1) FUNÇÃO OBJETIVO: Maximize sum(p_i * x_ik) para todo i em R
    # Maximizar a prioridade total das matérias escolhidas
    prob += pulp.lpSum([
        vars_x[(i, k)] * dados_materia[i]['prioridade']
        for (i, k) in vars_x.keys()
    ])
    
    # (2) RESTRIÇÃO DE UNICIDADE: sum(x_ik) <= 1 para todo i em R
    # Aluno não pode pegar a mesma matéria duas vezes
    for i in R:
        turmas_de_i = [vars_x[(mat, turma)] for (mat, turma) in vars_x if mat == i]
        if turmas_de_i:
            prob += pulp.lpSum(turmas_de_i) <= 1

    # (3) RESTRIÇÃO DE OPTATIVAS: sum(x_ik) <= Q_opt para todo i em R_opt
    # Limita a quantidade de optativas escolhidas
    turmas_optativas = [
        vars_x[(i, k)] 
        for (i, k) in vars_x 
        if i in R_opt  # Filtra pelo subconjunto R_opt
    ]
    if turmas_optativas:
        prob += pulp.lpSum(turmas_optativas) <= qtd_optativas

    # (4) CHOQUE DE HORÁRIO: sum(x_ik) <= 1 para todo t em T
    # Garante que não haja duas aulas no mesmo horário
    mapa_slots = {}
    for (i, k), var in vars_x.items():
        # Usa o dicionário info_slots (otimizado) ao invés de ler o DF novamente
        for t in info_slots[(i, k)]:
            if t not in mapa_slots: mapa_slots[t] = []
            mapa_slots[t].append(var)
            
    for t, lista_vars in mapa_slots.items():
        prob += pulp.lpSum(lista_vars) <= 1

    # ====================================================
    # 4. RESOLVER E EXIBIR
    # ====================================================

    # Resolve sem imprimir log do solver no terminal (msg=0)
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    status = pulp.LpStatus[prob.status]
    
    if status == 'Optimal':
        print("\n=== GRADE SUGERIDA ===")
        res = []
        total_prio = 0
        
        for (i, k), var in vars_x.items():
            if pulp.value(var) >= 0.9:
                prio = dados_materia[i]['prioridade']
                tipo = "Optativa" if i in R_opt else "Obrigatória"
                
                total_prio += prio
                
                res.append({
                    "Disciplina": dados_materia[i]['nome'],
                    "Tipo": tipo,
                    "Turma": k,
                    "Prioridade": prio,
                    "Horários": ", ".join(info_slots[(i, k)]) # Adicionado conforme solicitado
                })
        
        if res:
            df_res = pd.DataFrame(res)
            # Ordenação com Horários no final
            df_res = df_res.sort_values(by=['Tipo', 'Prioridade'], ascending=[True, False])
            
            print(df_res.to_string(index=False))
            print("-" * 60)
            print(f"Total Prioridade Acumulada: {total_prio}")
        else:
            print("O modelo encontrou uma solução ótima, mas nenhuma matéria foi selecionada.")
            print("(Verifique se a meta de optativas é 0 e se há obrigatórias disponíveis nos horários livres).")
    else:
        print(f"Solução ótima não encontrada. Status: {status}")

# ====================================================
# EXEMPLOS DE USO
# ====================================================

# Exemplo: AlunoXX precisa de exatamente 1 optativa
# otimizar_plano_estudos(
#    'materias_prioridades.csv', 
#    'turmas.csv', 
#    'materias_arestas.csv', 
#    'alunoXX_elegiveis.csv',
#    horarios_indisponiveis=["SEG01"],
#    qtd_optativas=1
# )

# otimizar_plano_estudos(
#     'materias_prioridades.csv', 
#     'turmas.csv', 
#     'materias_arestas.csv', 
#     'aluno01_elegiveis.csv',
#     qtd_optativas=1
# )

indisponiveis_aluno2 = ["SEX01", "SEX02"]
otimizar_plano_estudos(
    'materias_prioridades.csv',
    'turmas.csv', 
    'materias_arestas.csv', 
    'aluno02_elegiveis.csv',
    horarios_indisponiveis=indisponiveis_aluno2,
    qtd_optativas=2
)