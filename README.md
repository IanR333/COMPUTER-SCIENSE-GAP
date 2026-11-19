# Citizen Assist AI: módulo de decisão lógica (Computer Science)

Trabalho de Computer Science da Global Solution (FIAP). Esse módulo responde uma pergunta só: **com o que a pessoa tem em mãos, a documentação para a segunda via do RG está completa?**

Integrantes: Ian Rodrigues Martins (RM 570540), Patrick Fernandes Martins (RM 572899) e Gabriel Del Pizzo Pintor (RM 570436).

Relatório: [`relatorio/relatorio_logica_booleana.pdf`](relatorio/relatorio_logica_booleana.pdf)

## Variáveis

| | 1 | 0 |
|---|---|---|
| A | tem certidão de nascimento ou casamento | não tem |
| B | tem comprovante de residência (até 90 dias) | não tem |
| C | foi roubo ou furto | foi perda |
| D | tem boletim de ocorrência | não tem |
| S | documentação completa | falta alguma coisa |

Regra tirada da ficha FC-01 da Central do Cidadão de Aurora (fictícia, versão de 01/10/2026, consultada em 18/11/2026). Cópia em `referencias/`. Depois de simplificar com álgebra e mapa de Karnaugh:

```
S = A·B·(C' + D)
```

## Como rodar

```
python decisao_rg.py            # faz as perguntas
python decisao_rg.py 1 1 1 0    # testa uma combinação direto
python decisao_rg.py --tabela   # mostra a tabela-verdade
python testes_decisao.py        # roda os testes (16 combinações)
```

Os circuitos estão em `circuitverse/`. Para abrir: circuitverse.org > Launch Simulator > Project > Import Project.

A tabela-verdade e o mapa de Karnaugh estão em `tabela_verdade_karnaugh.xlsx`.

Obs.: é um protótipo de estudo com regras de fichas fictícias. Não é canal oficial e não substitui o atendimento da Central do Cidadão.
