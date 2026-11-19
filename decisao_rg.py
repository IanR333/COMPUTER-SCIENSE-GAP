"""Módulo de decisão lógica do Citizen Assist AI — segunda via do RG.

Contribuição de Computer Science (Global Solution FIAP). Funciona sozinho,
sem IA e sem internet: só lógica booleana.

Pergunta que o módulo responde:
    "Com o que você tem em mãos, a sua documentação para a 2ª via do RG está completa?"

Variáveis de entrada (1 = sim, 0 = não):
    A  tem certidão de nascimento ou de casamento (original ou cópia autenticada)
    B  tem comprovante de residência dos últimos 90 dias
    C  o motivo é roubo ou furto (1) | o motivo é perda/extravio (0)
    D  tem boletim de ocorrência

Saída:
    S = 1  documentação completa: pode comparecer ao atendimento agendado
    S = 0  documentação incompleta: providencie o que falta antes

Regra (ficha FC-01): precisa de A e de B; se for roubo ou furto, precisa também
do boletim; se for perda, basta a declaração de extravio, assinada no balcão.

    Forma canônica:  S = Σm(12, 13, 15) = A·B·C'·D' + A·B·C'·D + A·B·C·D
    Simplificada:    S = A·B·(C' + D)
    Com De Morgan:   S = A·B·(C·D')'      e     S' = A' + B' + C·D'

Privacidade: o módulo só pergunta sim/não. Não pede nem guarda nome, CPF,
número de documento, endereço ou telefone.
"""
from __future__ import annotations

import re
import sys
from itertools import product

FONTE = ("Central do Cidadão de Aurora (fictícia), ficha FC-01 — Carteira de Identidade (RG): "
         "primeira e segunda via, versão de 01/10/2026")
DATA_CONSULTA = "18/11/2026"
AVISO = ("Aviso: protótipo educacional, não é um canal oficial. Ele não agenda, não consulta "
         "cadastro e não garante a emissão do documento. Confirme sempre no portal ou no balcão "
         "da Central do Cidadão. Não informe dados pessoais.")

VARIAVEIS = {
    "A": "Você tem a certidão de nascimento ou de casamento (original ou cópia autenticada)?",
    "B": "Você tem um comprovante de residência dos últimos 90 dias?",
    "C": "O RG foi roubado ou furtado? (responda 'não' se foi perdido)",
    "D": "Você tem o boletim de ocorrência?",
}

MINTERMOS = (12, 13, 15)          # linhas da tabela-verdade em que S = 1
MAXTERMOS = tuple(i for i in range(16) if i not in MINTERMOS)

SIM = {"1", "s", "sim", "si", "yes", "y"}
NAO = {"0", "n", "nao", "não", "no"}
LIMITE_TEXTO = 20
TENTATIVAS = 3


# ------------------------------------------------------------------ as 5 formas da mesma regra
def regra_original(a: int, b: int, c: int, d: int) -> int:
    """Tradução direta do texto da ficha FC-01, com condicionais."""
    if not a:                       # sem certidão de nascimento ou casamento
        return 0
    if not b:                       # sem comprovante de residência recente
        return 0
    if c:                           # roubo ou furto: o boletim é obrigatório
        return 1 if d else 0
    return 1                        # perda: basta a declaração de extravio no balcão


def soma_de_mintermos(a: int, b: int, c: int, d: int) -> int:
    """Forma canônica SOP: S = A·B·C'·D' + A·B·C'·D + A·B·C·D."""
    na, nb, nc, nd = 1 - a, 1 - b, 1 - c, 1 - d
    return (a & b & nc & nd) | (a & b & nc & d) | (a & b & c & d)


def produto_de_maxtermos(a: int, b: int, c: int, d: int) -> int:
    """Forma canônica POS: S = ΠM(0..11, 14). Cada maxtermo vale 0 só na sua linha."""
    linha = 8 * a + 4 * b + 2 * c + d
    resultado = 1
    for m in MAXTERMOS:
        bits = [(m >> k) & 1 for k in (3, 2, 1, 0)]          # A, B, C, D da linha m
        # maxtermo: soma em que a variável aparece complementada quando o bit é 1
        termo = 0
        for valor, bit in zip((a, b, c, d), bits):
            termo |= (1 - valor) if bit else valor
        resultado &= termo
    assert resultado == (1 if linha in MINTERMOS else 0)
    return resultado


def simplificada(a: int, b: int, c: int, d: int) -> int:
    """Expressão simplificada (álgebra e mapa de Karnaugh): S = A·B·(C' + D)."""
    return a & b & ((1 - c) | d)


def com_de_morgan(a: int, b: int, c: int, d: int) -> int:
    """Forma equivalente por De Morgan: S = A·B·(C·D')'."""
    return a & b & (1 - (c & (1 - d)))


# ------------------------------------------------------------------ orientação ao cidadão
def o_que_falta(a: int, b: int, c: int, d: int) -> list[str]:
    """Usa S' = A' + B' + C·D' para dizer por que a documentação está incompleta."""
    falta = []
    if not a:
        falta.append("certidão de nascimento ou de casamento (original ou cópia autenticada)")
    if not b:
        falta.append("comprovante de residência dos últimos 90 dias")
    if c and not d:
        falta.append("boletim de ocorrência (exigido em caso de roubo ou furto)")
    return falta


def orientacao(a: int, b: int, c: int, d: int) -> str:
    """Texto mostrado ao usuário. A decisão vem SÓ da expressão simplificada."""
    for nome, v in zip("ABCD", (a, b, c, d)):
        if v not in (0, 1):
            raise ValueError(f"{nome} precisa ser 0 ou 1")
    s = simplificada(a, b, c, d)
    linhas = [f"Entradas: A={a} B={b} C={c} D={d}  ->  S={s}", ""]
    if s:
        linhas.append("Documentação completa: você pode comparecer ao atendimento agendado.")
        linhas.append("Leve os documentos originais:")
        linhas.append("  1. Certidão de nascimento ou de casamento.")
        linhas.append("  2. Comprovante de residência dos últimos 90 dias.")
        if c:
            linhas.append("  3. Boletim de ocorrência.")
        else:
            linhas.append("  3. A declaração de extravio é assinada no próprio balcão (sem boletim).")
        linhas.append("Lembre: o agendamento é obrigatório e é feito pelo portal; a taxa é de R$ 38,00.")
    else:
        linhas.append("Documentação incompleta. Antes de ir ao atendimento, providencie:")
        for i, item in enumerate(o_que_falta(a, b, c, d), 1):
            linhas.append(f"  {i}. {item}")
    linhas += ["", f"Fonte: {FONTE} (consultada em {DATA_CONSULTA}).", AVISO]
    return "\n".join(linhas)


# ------------------------------------------------------------------ entrada do usuário
_PARECE_DADO_PESSOAL = re.compile(r"\d{3}\D?\d{3}\D?\d{3}|@|\d{4,}")


def ler_resposta(texto: str) -> int:
    """Converte a resposta em 0/1. Levanta ValueError com mensagem amigável se for inválida."""
    bruto = (texto or "").strip()
    if not bruto:
        raise ValueError("Você não digitou nada. Responda sim ou não.")
    if len(bruto) > LIMITE_TEXTO:
        raise ValueError("Resposta muito longa. Responda só sim ou não.")
    if _PARECE_DADO_PESSOAL.search(bruto):
        raise ValueError("Parece um dado pessoal. Não informe números de documento, telefone ou "
                         "e-mail. Responda só sim ou não.")
    t = bruto.lower().replace("ã", "a").rstrip(".!")
    if t in SIM:
        return 1
    if t in NAO:
        return 0
    raise ValueError("Não entendi. Responda sim (s / 1) ou não (n / 0).")


def tabela_verdade() -> list[dict]:
    linhas = []
    for a, b, c, d in product((0, 1), repeat=4):
        linhas.append({"linha": 8 * a + 4 * b + 2 * c + d, "A": a, "B": b, "C": c, "D": d,
                       "S": simplificada(a, b, c, d)})
    return linhas


def imprimir_tabela() -> None:
    print(" m | A B C D | S")
    print("---+---------+--")
    for r in tabela_verdade():
        print(f"{r['linha']:2d} | {r['A']} {r['B']} {r['C']} {r['D']} | {r['S']}")


def conversar(entrada=input, saida=print) -> int | None:
    """Modo interativo. Devolve S, ou None se o usuário desistir após respostas inválidas."""
    saida("Citizen Assist AI — documentos para a 2ª via do RG")
    saida("Responda com sim ou não. Não informe dados pessoais.\n")
    valores = {}
    for nome, pergunta in VARIAVEIS.items():
        if nome == "D" and valores["C"] == 0:
            valores["D"] = 0        # na perda o boletim não muda a resposta (S não depende de D)
            continue
        for tentativa in range(TENTATIVAS):
            try:
                valores[nome] = ler_resposta(entrada(f"{nome}) {pergunta} "))
                break
            except ValueError as erro:
                saida(f"   {erro}")
        else:
            saida("\nVamos parar por aqui. Quando quiser, comece de novo respondendo sim ou não.")
            saida(AVISO)
            return None
    saida("")
    saida(orientacao(valores["A"], valores["B"], valores["C"], valores["D"]))
    return simplificada(valores["A"], valores["B"], valores["C"], valores["D"])


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("--tabela", "-t"):
        imprimir_tabela()
        return 0
    if argv:
        if len(argv) != 4:
            print("Uso: python decisao_rg.py            (modo de perguntas)\n"
                  "     python decisao_rg.py A B C D    (ex.: 1 1 0 0)\n"
                  "     python decisao_rg.py --tabela   (tabela-verdade)")
            return 2
        try:
            a, b, c, d = (ler_resposta(x) for x in argv)
        except ValueError as erro:
            print(f"Entrada inválida: {erro}")
            return 2
        print(orientacao(a, b, c, d))
        return 0
    try:
        conversar()
    except (EOFError, KeyboardInterrupt):
        print("\nAtendimento encerrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
