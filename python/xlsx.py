import zipfile
from typing import List, Sequence, Tuple
from xml.sax.saxutils import escape

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
{sheet_overrides}
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

WIDTH_PADDING = 3
MIN_WIDTH = 8
MAX_WIDTH = 60


def column_name(index: int) -> str:
    name = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


def column_widths(rows: Sequence[Sequence[str]]) -> List[float]:
    widths: List[float] = []
    for row in rows:
        for i, value in enumerate(row):
            width = min(max(len(str(value)) + WIDTH_PADDING, MIN_WIDTH), MAX_WIDTH)
            if i >= len(widths):
                widths.append(width)
            elif width > widths[i]:
                widths[i] = width
    return widths


def sheet_xml(rows: Sequence[Sequence[str]], merges: Sequence[str]) -> str:
    cols = ""
    widths = column_widths(rows)
    if widths:
        cols = "<cols>" + "".join(
            f'<col min="{i}" max="{i}" width="{w:.2f}" customWidth="1"/>'
            for i, w in enumerate(widths, start=1)
        ) + "</cols>"

    lines = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            if value == "":
                continue
            ref = f"{column_name(col_index)}{row_index}"
            cells.append(
                f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">'
                f"{escape(str(value))}</t></is></c>"
            )
        lines.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    merge_xml = ""
    if merges:
        merge_xml = f'<mergeCells count="{len(merges)}">' + "".join(
            f'<mergeCell ref="{ref}"/>' for ref in merges
        ) + "</mergeCells>"

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'{cols}<sheetData>{"".join(lines)}</sheetData>{merge_xml}</worksheet>'
    )


def write_workbook(path: str, sheets: List[Tuple[str, Sequence[Sequence[str]], Sequence[str]]]) -> None:
    overrides = "\n".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, len(sheets) + 1)
    )
    workbook_sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
        for i, (name, _, _) in enumerate(sheets, start=1)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{workbook_sheets}</sheets></workbook>"
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{i}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, len(sheets) + 1)
        )
        + "</Relationships>"
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES.format(sheet_overrides=overrides))
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        for i, (_, rows, merges) in enumerate(sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows, merges))
