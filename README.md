# TCC - Modelo de otimização da grade horária para discentes da FACOM/UFU
Código fonte do TCC Modelo de otimização da grade horária para discentes da FACOM/UFU - v1.0


> ATENÇÃO:   
> Para evitar erros no uso do modelo, por favor clonar ou baixar a pasta e abrir ela como pasta raiz no VSCODE para que o programa consiga localizar os arquivos definidos de forma dinâmica no programa (sempre na pasta raiz).


## Instalando dependências

As bibliotecas utilizadas para criação e utilização do modelo estão listadas no arquivo `requirements.txt` e o comando utilize o comando  `pip install -r requirements.txt` após a  instalação Python 3 no CMD para a instalação das bibliotecas usadas e suas versões.

## 1. Algoritmo de Prioridades


> ATENÇÃO:   
> Se você for um aluno do curso de Sistemas de Informação - FACOM/UFU do Curriculo 2022/2 não é necessário realizar a parte 1, pois o arquivo `materias_prioridade.csv` já está montado de acordo com esse curriculo.


O primeiro passo para utilizar o modelo é o cálculo da prioridade das matérias.

O documento `materias_prioridade.csv` é gerado pelo arquivo `...\Iterations & Graph Creation Code\grafos_prioridade.py`, pórem para utilizá-lo é necessário mapear as materias no formato `materias_nos.csv` e os pré-requisitos no formato `materias_arestas.csv`.

- O arquivo `materias_nos.csv` é responsável pela base do dígrafo que será gerado e contém as informações do nós (disciplina), os seus campos começam todos com o valor de prioridade igual a 0 e o algoritmo irá gerar `materias_prioridade.csv` já com o valor de prioridade no documento.

- O arquivo `materias_arestas.csv` é responsável por informar a relação de pré-requisito das materias para construção do grafo, o arquivo só terá informações de origem e destino onde a origem é a matéria que é pré-requisito para o destino.
Exemplo: Origem (Cálculo 1) -> Destino (Álgebra Linear)


## 2. Dados para o Modelo


> ATENÇÃO:   
> Apesar de não ser necessário o passo 1 para o aluno do curso de Sistemas de Informação - FACOM/UFU do Curriculo 2022/2, o passo 2 deve ser feito por todos os alunos que desejam utilizar o modelo.


Antes de entrar no arquivo `modelo_v5.py` é necessário criar o arquivo `turmas.csv` e `alunoXX_elegiveis.csv`.

- O arquivo `alunoXX_elegiveis.csv` contém todas as matérias que o aluno não fez e precisa fazer para se formar. Caso seja aluno do curso de SI do Curriculo 2022/2 basta retirár do arquivo as materias que já obteve aprovação. Caso seja estudante de outro curso, liste as materias que precisa realizar com o mesmo id e nome usados pelo arquivo `materias_arestas.csv` / `materias_prioridade.csv`.

- O arquivo `turmas.csv` precisa ser revisado por todos, até alunos de SI pois os horarios são alterados a cada semestre. o arquivo utiliza a abstração desenvolvida pelo TCC (SEG01, SEG02, ... , SEX03, SEX04) porém se deseja realizar materias em no periodo da tarde ou manhã, basta seguir um modelo que abstraia e crie esses slots exemplo: SEG8, SEG9, SEG10 até SEG22 pensando em slots para marcar o horario da matéria.

- Importante ressaltar que a forma como é descritos os slots de tempo no arquivo `turmas.csv` deve ser o mesmo para informar BLOQUEIOS, então caso seja criado outra abstração isso precisa ser refletido na chamada do modelo.

## 3. Chamada para o Modelo

Pronto! todos os arquivos estão corretos e você está pronto para usar o modelo. Basta entrar no programa `modelo_v5.py` e no final do arquivo realizar a seguinte chamada:

```py

indisponiveis_alunoXX = ["SEX01", "SEX02"]

otimizar_plano_estudos(
    'materias_prioridades.csv',
    'turmas.csv', 
    'materias_arestas.csv', 
    'alunoXX_elegiveis.csv',
    horarios_indisponiveis=indisponiveis_alunoXX,
    qtd_optativas=2
)

```

Entenda que a variavel `indisponiveis_alunoXX` receberá os bloqueios, slots no qual não consegue se comprometer as aulas. Caso não tenha nenhum bloqueio de horários a chamada deve ser realizada da seguinte forma:

```py

otimizar_plano_estudos(
    'materias_prioridades.csv',
    'turmas.csv', 
    'materias_arestas.csv', 
    'alunoXX_elegiveis.csv',
    qtd_optativas=2
)

```

A variavel `qtd_optativas` é referente a quantidade de optativas que precisa realizar para se graduar deixe 2 caso seja aluno de SI FACOM/UFU e não tenha realizado nenhuma optativa, ao ser aprovado em uma troque para 1 ao realizar as duas esse valor deve ser igual a 0.

Com essa chamada montada no final do arquivo, basta executar o programa e terá o retorno com a grade sugerida para matricula no seguinte modelo:

```

Meta de Optativas: Máximo 2
Horários Bloqueados: ['SEX01', 'SEX02']
Conjunto R (Elegíveis totais): 12
Subconjunto R_opt (Optativas elegíveis): 2

=== GRADE SUGERIDA ===
                           Disciplina        Tipo Turma  Prioridade                   Horários
      Programação Orientada a Objetos Obrigatória    EX        4200 QUA01, QUA02, SEX03, SEX04
                     Banco de Dados I Obrigatória    EX        2400 SEG01, SEG02, QUA03, QUA04
                Estrutura de Dados II Obrigatória    EX        1800 TER01, TER02, QUI03, QUI04
Matemática para Ciência da Computação Obrigatória     S         600 SEG03, SEG04, QUI01, QUI02
------------------------------------------------------------
Total Prioridade Acumulada: 9000

```

Assim, estará claro qual turma e qual disciplina é a recomendação de matricula com as suas prioridades e total.

Obrigado!