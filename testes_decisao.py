"""Validação do módulo de decisão: as 16 combinações + entradas inválidas.

Rodar:  python testes_decisao.py
Gera resultados_testes.csv com a comparação linha a linha.
"""
from __future__ import annotations

import csv
import io
import unittest
from itertools import product
from pathlib import Path

import decisao_rg as m

PASTA = Path(__file__).resolve().parent
# Valor de S escrito à mão a partir da ficha FC-01 (independente do código)
ESPERADO_PELA_FICHA = {12: 1, 13: 1, 15: 1}


def comparar_todas() -> list[dict]:
    linhas = []
    for a, b, c, d in product((0, 1), repeat=4):
        n = 8 * a + 4 * b + 2 * c + d
        saida_programa = m.orientacao(a, b, c, d)
        s_programa = 1 if "Documentação completa" in saida_programa else 0
        linhas.append({
            "linha": n, "A": a, "B": b, "C": c, "D": d,
            "esperado_ficha": ESPERADO_PELA_FICHA.get(n, 0),
            "regra_original": m.regra_original(a, b, c, d),
            "soma_mintermos": m.soma_de_mintermos(a, b, c, d),
            "produto_maxtermos": m.produto_de_maxtermos(a, b, c, d),
            "simplificada": m.simplificada(a, b, c, d),
            "de_morgan": m.com_de_morgan(a, b, c, d),
            "programa": s_programa,
        })
    for r in linhas:
        valores = [r[k] for k in ("esperado_ficha", "regra_original", "soma_mintermos",
                                  "produto_maxtermos", "simplificada", "de_morgan", "programa")]
        r["todas_iguais"] = "OK" if len(set(valores)) == 1 else "DIFERENTE"
    return linhas


class TestEquivalencia(unittest.TestCase):
    def test_16_combinacoes_equivalentes(self):
        for r in comparar_todas():
            with self.subTest(linha=r["linha"]):
                self.assertEqual(r["todas_iguais"], "OK", r)

    def test_mintermos(self):
        uns = [r["linha"] for r in comparar_todas() if r["simplificada"] == 1]
        self.assertEqual(uns, [12, 13, 15])

    def test_o_que_falta_coincide_com_S_negado(self):
        # S' = A' + B' + C·D'  ->  há algo faltando exatamente quando S = 0
        for a, b, c, d in product((0, 1), repeat=4):
            self.assertEqual(bool(m.o_que_falta(a, b, c, d)), m.simplificada(a, b, c, d) == 0)

    def test_toda_saida_tem_fonte_data_e_aviso(self):
        for a, b, c, d in product((0, 1), repeat=4):
            texto = m.orientacao(a, b, c, d)
            self.assertIn("FC-01", texto)
            self.assertIn(m.DATA_CONSULTA, texto)
            self.assertIn("não é um canal oficial", texto)


class TestEntradas(unittest.TestCase):
    def test_respostas_validas(self):
        for t in ("1", "s", "S", "sim", "Sim.", " SIM "):
            self.assertEqual(m.ler_resposta(t), 1)
        for t in ("0", "n", "não", "nao", "NÃO", "Não!"):
            self.assertEqual(m.ler_resposta(t), 0)

    def test_respostas_invalidas_dao_mensagem_amigavel(self):
        casos = {
            "": "não digitou",
            "   ": "não digitou",
            "talvez": "Não entendi",
            "2": "Não entendi",
            "x" * 50: "muito longa",
            "123.456.789-09": "dado pessoal",
            "eu@email.com": "dado pessoal",
        }
        for texto, trecho in casos.items():
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError) as ctx:
                    m.ler_resposta(texto)
                self.assertIn(trecho, str(ctx.exception))

    def test_orientacao_rejeita_valor_fora_de_0_1(self):
        with self.assertRaises(ValueError):
            m.orientacao(2, 1, 0, 0)

    def test_modo_interativo_com_erros_e_acerto(self):
        respostas = iter(["talvez", "sim", "s", "1", "não"])   # A (erro, depois sim), B, C, D
        saida = io.StringIO()
        s = m.conversar(entrada=lambda _: next(respostas), saida=lambda t="": print(t, file=saida))
        self.assertEqual(s, 0)                                   # roubo sem boletim
        self.assertIn("Não entendi", saida.getvalue())
        self.assertIn("boletim de ocorrência", saida.getvalue())

    def test_modo_interativo_desiste_apos_3_invalidas(self):
        respostas = iter(["", "???", "talvez"])
        saida = io.StringIO()
        s = m.conversar(entrada=lambda _: next(respostas), saida=lambda t="": print(t, file=saida))
        self.assertIsNone(s)
        self.assertIn("Vamos parar por aqui", saida.getvalue())

    def test_perda_nao_pergunta_boletim(self):
        respostas = iter(["sim", "sim", "não"])                  # D não é perguntado
        saida = io.StringIO()
        s = m.conversar(entrada=lambda _: next(respostas), saida=lambda t="": print(t, file=saida))
        self.assertEqual(s, 1)


def salvar_csv() -> Path:
    linhas = comparar_todas()
    caminho = PASTA / "resultados_testes.csv"
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    return caminho


if __name__ == "__main__":
    caminho = salvar_csv()
    linhas = comparar_todas()
    print("linha | A B C D | ficha original mintermos maxtermos simplif. DeMorgan programa | ok")
    for r in linhas:
        print(f"{r['linha']:5d} | {r['A']} {r['B']} {r['C']} {r['D']} |"
              f"   {r['esperado_ficha']}      {r['regra_original']}        {r['soma_mintermos']}         "
              f"{r['produto_maxtermos']}        {r['simplificada']}        {r['de_morgan']}        "
              f"{r['programa']}    | {r['todas_iguais']}")
    print(f"\nCombinações equivalentes: {sum(r['todas_iguais'] == 'OK' for r in linhas)}/16 "
          f"(tabela salva em {caminho.name})\n")
    unittest.main(verbosity=2)
