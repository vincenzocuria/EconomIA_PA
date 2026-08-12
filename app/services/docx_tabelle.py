"""Helper riusabili per tabelle Word (stile modulo ufficiale)."""
from docx.document import Document as DocumentObject
from docx.shared import Cm, Pt
from docx.table import Table, _Cell


def tabella_griglia(doc: DocumentObject, rows: int, cols: int, col_cm: float = 9.29) -> Table:
    t = doc.add_table(rows=rows, cols=cols)
    t.style = "Table Grid"
    t.autofit = True
    for row in t.rows:
        for cell in row.cells:
            cell.width = Cm(col_cm)
    return t


def cella_multiline(cell: _Cell, linee: list[str], font_pt: float = 14, bold: bool = False) -> None:
    """Sostituisce il contenuto della cella con testo a più righe (break Word)."""
    p = cell.paragraphs[0]
    p.clear()
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0
    for i, linea in enumerate(linee):
        if i:
            p.add_run().add_break()
        run = p.add_run(linea)
        run.font.size = Pt(font_pt)
        run.bold = bold