"""Gera tabela_verdade_karnaugh.xlsx: tabela-verdade com fórmulas e mapa de Karnaugh."""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

PASTA = Path(__file__).resolve().parent
F = "Arial"
fino = Side(style="thin", color="000000")
grosso_azul = Side(style="thick", color="2F6FDB")
grosso_lar = Side(style="thick", color="E07B00")
borda = Border(left=fino, right=fino, top=fino, bottom=fino)
cab = PatternFill("solid", fgColor="D9D9D9")
verde = PatternFill("solid", fgColor="D9EAD3")
cinza = PatternFill("solid", fgColor="F2F4F7")
centro = Alignment(horizontal="center", vertical="center", wrap_text=True)

wb = Workbook()
ws = wb.active
ws.title = "Tabela-verdade"
ws["A1"] = "Tabela-verdade: documentação para a 2ª via do RG (ficha FC-01)"
ws["A1"].font = Font(name=F, bold=True, size=12, color="000000")
ws.merge_cells("A1:I1")
heads = ["m", "A", "B", "C", "D", "C'", "C' + D", "S", "Orientação"]
for j, h in enumerate(heads, 1):
    c = ws.cell(row=3, column=j, value=h)
    c.font = Font(name=F, bold=True, color="000000")
    c.fill = cab
    c.alignment = centro
    c.border = borda
for m in range(16):
    r = 4 + m
    bits = [(m >> k) & 1 for k in (3, 2, 1, 0)]
    vals = [m, *bits,
            f"=1-D{r}",
            f"=MAX(F{r},E{r})",
            f"=IF(AND(B{r}=1,C{r}=1,OR(D{r}=0,E{r}=1)),1,0)",
            f'=IF(H{r}=1,"Completa: pode ir ao atendimento","Incompleta: providenciar o que falta")']
    for j, v in enumerate(vals, 1):
        c = ws.cell(row=r, column=j, value=v)
        c.font = Font(name=F, size=10, bold=(j == 8))
        c.alignment = centro if j < 9 else Alignment(vertical="center")
        c.border = borda
        c.fill = cinza if m % 2 == 0 else PatternFill()
ws.conditional_formatting.add("A4:I19", CellIsRule(operator="equal", formula=["1"], fill=verde)) if False else None
from openpyxl.formatting.rule import FormulaRule
ws.conditional_formatting.add("A4:I19", FormulaRule(formula=["$H4=1"], fill=verde, font=Font(name=F, bold=True, color="1A5E2A")))
leg = [
    "A = 1: tem certidão de nascimento ou casamento   |   B = 1: tem comprovante de residência (até 90 dias)",
    "C = 1: roubo ou furto (0 = perda)   |   D = 1: tem boletim de ocorrência",
    "S = A·B·(C' + D)   →   S = Σm(12, 13, 15)",
    "Fonte: Central do Cidadão de Aurora (fictícia), ficha FC-01, versão 01/10/2026. Consulta: 18/11/2026.",
]
for i, t in enumerate(leg):
    c = ws.cell(row=21 + i, column=1, value=t)
    c.font = Font(name=F, size=9, italic=(i == 3), bold=(i == 2), color="333333")
for col, w in zip("ABCDEFGHI", (6, 6, 6, 6, 6, 7, 9, 6, 38)):
    ws.column_dimensions[col].width = w
ws.sheet_view.showGridLines = False

# ------------------------------------------------------------------ mapa de Karnaugh
k = wb.create_sheet("Mapa de Karnaugh")
k["A1"] = "Mapa de Karnaugh de S(A, B, C, D)"
k["A1"].font = Font(name=F, bold=True, size=12, color="000000")
k.merge_cells("A1:F1")
gray = ["00", "01", "11", "10"]
k["B3"] = "AB \\ CD"
k["B3"].font = Font(name=F, bold=True)
k["B3"].alignment = centro
k["B3"].border = borda
for j, cd in enumerate(gray):
    c = k.cell(row=3, column=3 + j, value=cd)
    c.font = Font(name=F, bold=True, color="000000"); c.fill = cab; c.alignment = centro; c.border = borda
for i, ab in enumerate(gray):
    c = k.cell(row=4 + i, column=2, value=ab)
    c.font = Font(name=F, bold=True, color="000000"); c.fill = cab; c.alignment = centro; c.border = borda
    k.row_dimensions[4 + i].height = 40
    for j, cd in enumerate(gray):
        m = int(ab + cd, 2)
        c = k.cell(row=4 + i, column=3 + j, value=f"=INDEX('Tabela-verdade'!$H$4:$H$19,{m + 1})")
        c.font = Font(name=F, size=16, bold=True)
        c.alignment = centro
        c.border = borda
        c.number_format = '0;;0'
# linha AB = 11 -> row 6; colunas CD = 00, 01, 11 -> C, D, E
azul = PatternFill("solid", fgColor="CFE0FA")
lar = PatternFill("solid", fgColor="FBE2C4")
mix = PatternFill("solid", fgColor="E6D6F0")
k["C6"].fill = azul
k["D6"].fill = mix
k["E6"].fill = lar
k["C6"].border = Border(left=grosso_azul, top=grosso_azul, bottom=grosso_azul, right=fino)
k["D6"].border = Border(left=fino, top=grosso_lar, bottom=grosso_azul, right=fino)
k["E6"].border = Border(left=fino, top=grosso_lar, bottom=grosso_lar, right=grosso_lar)
# números dos mintermos em uma grade auxiliar
k["H3"] = "Mintermos"
k["H3"].font = Font(name=F, bold=True, size=9, color="555555")
for i, ab in enumerate(gray):
    for j, cd in enumerate(gray):
        c = k.cell(row=4 + i, column=8 + j, value=f"m{int(ab + cd, 2)}")
        c.font = Font(name=F, size=9, color="555555"); c.alignment = centro; c.border = borda
notas = [
    ("Grupo 1 (azul): m12 + m13  →  A·B·C'", "2F6FDB"),
    ("Grupo 2 (laranja): m13 + m15  →  A·B·D", "E07B00"),
    ("m13 (roxo) pertence aos dois grupos", "6B3FA0"),
    ("S = A·B·C' + A·B·D = A·B·(C' + D)", "1F2430"),
]
for i, (t, cor) in enumerate(notas):
    c = k.cell(row=9 + i, column=2, value=t)
    c.font = Font(name=F, bold=True, size=11, color=cor)
k.column_dimensions["A"].width = 2
k.column_dimensions["B"].width = 10
for col in "CDEF":
    k.column_dimensions[col].width = 9
k.column_dimensions["G"].width = 3
for col in "HIJK":
    k.column_dimensions[col].width = 6
k.sheet_view.showGridLines = False
for s in (ws, k):
    s.page_setup.orientation = "landscape"
    s.page_setup.fitToWidth = 1
    s.sheet_properties.pageSetUpPr.fitToPage = True
wb.save(PASTA / "tabela_verdade_karnaugh.xlsx")
print("ok")
