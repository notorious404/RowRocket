from typing import List, Dict


def detect_pipe_tables_in_text(text: str) -> List[Dict[str, object]]:
    """
    Detect pipe-style tables in raw text.

    A "pipe row" is any line that:
    - Contains at least 2 '|' characters.
    - When split on '|', contains at least 2 cells and at least 2 non-empty cells.

    Consecutive pipe rows with the same number of columns are grouped
    into a single table block.

    Returns a list of dicts:
    {
      "raw_block": str,        # original text block
      "rows": List[List[str]]  # parsed cell rows
    }
    """
    tables: List[Dict[str, object]] = []
    lines = [ln.rstrip("\n\r") for ln in text.splitlines()]

    def line_to_cells(line: str):
        # must contain at least 2 pipes
        if line.count("|") < 2:
            return None
        # ignore very short lines
        if len(line.strip()) < 3:
            return None

        # drop leading/trailing pipes and split
        parts = [c.strip() for c in line.strip().strip("|").split("|")]

        # at least 2 cells and at least 2 non-empty cells
        if len(parts) < 2:
            return None
        non_empty = [c for c in parts if c]
        if len(non_empty) < 2:
            return None

        return parts

    current_rows: List[List[str]] = []
    current_lines: List[str] = []
    current_cols = None

    for ln in lines:
        cells = line_to_cells(ln)
        if cells is None:
            # End of a current table block
            if current_rows:
                tables.append(
                    {
                        "raw_block": "\n".join(current_lines),
                        "rows": current_rows,
                    }
                )
                current_rows = []
                current_lines = []
                current_cols = None
            continue

        # Start a new block
        if not current_rows:
            current_rows = [cells]
            current_lines = [ln]
            current_cols = len(cells)
        else:
            # Same column count => same table
            if len(cells) == current_cols:
                current_rows.append(cells)
                current_lines.append(ln)
            else:
                # Column mismatch => close previous, start new
                tables.append(
                    {
                        "raw_block": "\n".join(current_lines),
                        "rows": current_rows,
                    }
                )
                current_rows = [cells]
                current_lines = [ln]
                current_cols = len(cells)

    # Flush at end
    if current_rows:
        tables.append(
            {
                "raw_block": "\n".join(current_lines),
                "rows": current_rows,
            }
        )

    return tables
