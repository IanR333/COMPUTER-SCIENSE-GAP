"""Gera os circuitos em formato do CircuitVerse (.cv) e confere a lógica de cada um.

Rodar:  python gerar_circuitverse.py
Saída:  circuitverse/circuito_simplificado.cv  e  circuitverse/circuito_original.cv
Abrir no CircuitVerse: Project > Import Project (ou Open Offline / importar arquivo .cv).
"""
from __future__ import annotations

import json
import random
from itertools import product
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "circuitverse"
PASTA.mkdir(exist_ok=True)
INPUT, OUTPUT, INTER = 0, 1, 2


class Circuito:
    def __init__(self, nome):
        self.nome = nome
        self.nodes = []          # allNodes
        self.elems = {}          # objectType -> lista
        self.logica = []         # (tipo, [nós de entrada], nó de saída) para conferir

    # --------------------------------------------------------- nós
    def _no(self, x, y, tipo, absx, absy):
        self.nodes.append({"x": x, "y": y, "type": tipo, "bitWidth": 1, "label": "",
                           "connections": [], "_abs": (absx, absy)})
        return len(self.nodes) - 1

    def ligar(self, a, b):
        self.nodes[a]["connections"].append(b)
        self.nodes[b]["connections"].append(a)

    def fio(self, origem, pontos, destino=None):
        """Liga origem -> pontos intermediários (x, y) -> destino. Devolve o último nó."""
        atual = origem
        for (x, y) in pontos:
            n = self._no(x, y, INTER, x, y)
            self.ligar(atual, n)
            atual = n
        if destino is not None:
            self.ligar(atual, destino)
            return destino
        return atual

    def pos(self, n):
        return self.nodes[n]["_abs"]

    # --------------------------------------------------------- elementos
    def _elem(self, tipo, x, y, direcao, custom, label="", label_dir="LEFT"):
        self.elems.setdefault(tipo, []).append({
            "x": x, "y": y, "objectType": tipo, "label": label, "direction": direcao,
            "labelDirection": label_dir, "propagationDelay": 10, "customData": custom})

    def entrada(self, nome, x, y, ordem):
        out = self._no(10, 0, OUTPUT, x + 10, y)
        lid = "".join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(20))
        self._elem("Input", x, y, "RIGHT", {
            "nodes": {"output1": out}, "values": {"state": 0},
            "constructorParamaters": ["RIGHT", 1, {"x": 5, "y": 15 + 20 * ordem, "id": lid}]},
            label=nome, label_dir="LEFT")
        self.logica.append(("IN", nome, out))
        return out

    def saida(self, nome, x, y):
        inp = self._no(10, 0, INPUT, x - 10, y)          # direção LEFT: nó fica à esquerda
        lid = "".join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(20))
        self._elem("Output", x, y, "LEFT", {
            "nodes": {"inp1": inp},
            "constructorParamaters": ["LEFT", 1, {"x": 95, "y": 15, "id": lid}]},
            label=nome, label_dir="RIGHT")
        self.logica.append(("OUT", nome, inp))
        return inp

    def nao(self, x, y):
        i = self._no(-10, 0, INPUT, x - 10, y)
        o = self._no(20, 0, OUTPUT, x + 20, y)
        self._elem("NotGate", x, y, "RIGHT", {
            "constructorParamaters": ["RIGHT", 1], "nodes": {"output1": o, "inp1": i}})
        self.logica.append(("NOT", [i], o))
        return i, o

    def _porta(self, tipo, x, y, n):
        """Mesma ordem de criação de nós do AndGate/OrGate do CircuitVerse."""
        offs = []
        if n % 2 == 1:
            i = 0
            while i < n / 2 - 1:
                offs.append(-10 * (i + 1)); i += 1
            offs.append(0)
            i = n / 2 + 1
            while i < n:
                offs.append(int(10 * (i + 1 - n / 2 - 1))); i += 1
        else:
            for i in range(n // 2):
                offs.append(-10 * (i + 1))
            for i in range(n // 2, n):
                offs.append(10 * (i + 1 - n // 2))
        ins = [self._no(-10, dy, INPUT, x - 10, y + dy) for dy in offs]
        o = self._no(20, 0, OUTPUT, x + 20, y)
        self._elem(tipo, x, y, "RIGHT", {
            "constructorParamaters": ["RIGHT", n, 1], "nodes": {"inp": ins, "output1": o}})
        self.logica.append(("AND" if tipo == "AndGate" else "OR", ins, o))
        return {y + dy: idx for dy, idx in zip(offs, ins)}, o   # mapa: y absoluto -> nó

    def e(self, x, y, n):
        return self._porta("AndGate", x, y, n)

    def ou(self, x, y, n):
        return self._porta("OrGate", x, y, n)

    # --------------------------------------------------------- barramento vertical
    def trilho(self, origem, x, ys):
        """Leva o sinal da origem até a coluna x e desce, criando um nó em cada y de ys."""
        ox, oy = self.pos(origem)
        topo = self._no(x, oy, INTER, x, oy)
        self.ligar(origem, topo)
        nos, atual = {}, topo
        for y in sorted(ys):
            if y == oy:
                nos[y] = topo
                continue
            n = self._no(x, y, INTER, x, y)
            self.ligar(atual, n)
            atual = n
            nos[y] = n
        return nos

    # --------------------------------------------------------- simulação para conferir
    def simular(self, valores: dict) -> int:
        # componentes conectados por fios = mesma rede
        pai = list(range(len(self.nodes)))

        def raiz(a):
            while pai[a] != a:
                pai[a] = pai[pai[a]]
                a = pai[a]
            return a
        for i, n in enumerate(self.nodes):
            for j in n["connections"]:
                pai[raiz(i)] = raiz(j)
        rede = {}
        for kind, a, b in self.logica:
            if kind == "IN":
                rede[raiz(b)] = valores[a]
        for _ in range(10):
            for kind, a, b in self.logica:
                if kind in ("AND", "OR", "NOT"):
                    vs = [rede.get(raiz(i)) for i in a]
                    if None in vs:
                        continue
                    v = (1 - vs[0]) if kind == "NOT" else (int(all(vs)) if kind == "AND" else int(any(vs)))
                    rede[raiz(b)] = v
        saida = [b for kind, a, b in self.logica if kind == "OUT"][0]
        return rede.get(raiz(saida))

    def conferir(self):
        for i, n in enumerate(self.nodes):          # ligações simétricas
            for j in n["connections"]:
                assert i in self.nodes[j]["connections"]
        for a, b, c, d in product((0, 1), repeat=4):
            s = self.simular({"A": a, "B": b, "C": c, "D": d})
            esperado = a & b & ((1 - c) | d)
            assert s == esperado, (self.nome, a, b, c, d, s, esperado)

    def salvar(self, arquivo):
        sid = random.randint(10**12, 10**13 - 1)
        nodes = [{k: v for k, v in n.items() if k != "_abs"} for n in self.nodes]
        escopo = {
            "layout": {"width": 100, "height": 40, "title_x": 50, "title_y": 13, "titleEnabled": True},
            "verilogMetadata": {"isVerilogCircuit": False, "isMainCircuit": False,
                                "code": "// Write Some Verilog Code Here!", "subCircuitScopeIds": []},
            "allNodes": nodes,
            "id": sid,
            "name": self.nome,
            **self.elems,
            "restrictedCircuitElementsUsed": [],
            "nodes": [i for i, n in enumerate(self.nodes) if n["type"] == INTER],
        }
        dados = {"name": self.nome, "timePeriod": 500, "clockEnabled": True,
                 "projectId": "".join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(20)),
                 "focussedCircuit": sid, "orderedTabs": [str(sid)], "scopes": [escopo]}
        (PASTA / arquivo).write_text(json.dumps(dados), encoding="utf-8")


def simplificado():
    c = Circuito("Citizen Assist - S = A.B.(C' + D)")
    a = c.entrada("A", 100, 60, 0)
    b = c.entrada("B", 100, 100, 1)
    cc = c.entrada("C", 100, 220, 2)
    d = c.entrada("D", 100, 280, 3)
    ni, no = c.nao(200, 220)
    c.fio(cc, [], ni)                                    # C -> NOT
    entradas_or, o_or = c.ou(300, 250, 2)                # entradas em y 240 e 260
    c.fio(no, [(250, 220), (250, 240)], entradas_or[240])  # C' -> OR
    c.fio(d, [(250, 280), (250, 260)], entradas_or[260])   # D  -> OR
    entradas_and, o_and = c.e(420, 100, 3)               # entradas em y 90, 100, 110
    c.fio(a, [(380, 60), (380, 90)], entradas_and[90])     # A -> AND
    c.fio(b, [], entradas_and[100])                        # B -> AND
    c.fio(o_or, [(380, 250), (380, 110)], entradas_and[110])  # (C'+D) -> AND
    s = c.saida("S", 520, 100)
    c.fio(o_and, [], s)
    return c


def original():
    c = Circuito("Citizen Assist - S original (soma de mintermos)")
    srcs = {k: c.entrada(k, 60, 40 + 20 * i, i) for i, k in enumerate("ABCD")}
    # inversores
    ni_c, no_c = c.nao(240, 120)
    ni_d, no_d = c.nao(240, 140)
    # portas AND de 4 entradas: centros e literais (y relativo -> sinal)
    ands = []
    for cy, lits in ((200, ("A", "B", "C'", "D'")), (300, ("A", "B", "C'", "D")), (400, ("A", "B", "C", "D"))):
        mapa, o = c.e(400, cy, 4)
        ys = sorted(mapa)                                # cy-20, cy-10, cy+10, cy+20
        ands.append(({lit: (y, mapa[y]) for lit, y in zip(lits, ys)}, o))
    trilho_x = {"A": 120, "B": 140, "C": 160, "D": 180, "C'": 300, "D'": 320}
    taps = {k: [] for k in trilho_x}
    for lits, _ in ands:
        for lit, (y, _) in lits.items():
            taps[lit].append(y)
    taps["C"].append(120)
    taps["D"].append(140)
    trilhos = {k: c.trilho(srcs[k], trilho_x[k], taps[k]) for k in "ABCD"}
    c.fio(trilhos["C"][120], [], ni_c)
    c.fio(trilhos["D"][140], [], ni_d)
    trilhos["C'"] = c.trilho(no_c, trilho_x["C'"], taps["C'"])
    trilhos["D'"] = c.trilho(no_d, trilho_x["D'"], taps["D'"])
    for lits, _ in ands:
        for lit, (y, no_porta) in lits.items():
            c.fio(trilhos[lit][y], [], no_porta)
    mapa_or, o_or = c.ou(520, 300, 3)                    # entradas em y 290, 300, 310
    (m12, o1), (m13, o2), (m15, o3) = ands
    c.fio(o1, [(460, 200), (460, 290)], mapa_or[290])
    c.fio(o2, [], mapa_or[300])
    c.fio(o3, [(470, 400), (470, 310)], mapa_or[310])
    s = c.saida("S", 600, 300)
    c.fio(o_or, [], s)
    return c


if __name__ == "__main__":
    random.seed(42)
    for circ, arq in ((simplificado(), "circuito_simplificado.cv"), (original(), "circuito_original.cv")):
        circ.conferir()
        circ.salvar(arq)
        print(f"{arq}: 16/16 combinações conferidas ({len(circ.nodes)} nós)")
