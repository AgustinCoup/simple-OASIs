"""Aplica cada mutante a una copia del código, lo compila y corre el arnés Verif.

Uso:  python mutar.py [filtro ...]      (p. ej. `python mutar.py C3` corre solo los mutantes del caso 3)
El proyecto original se indica con la variable PROYECTO (por defecto, la carpeta hermana
`reliable-2048-mai-becerra` dentro de Seminario). No se modifica: se compila sobre copias en ./mut/.
"""
import os, re, shutil, subprocess, sys

SC = os.path.dirname(os.path.abspath(__file__))
PROYECTO = os.environ.get("PROYECTO") or os.path.abspath(os.path.join(SC, *[".."] * 5, "reliable-2048-mai-becerra"))
SRC = os.path.join(PROYECTO, "src", "main", "java")
LIB = os.path.join(PROYECTO, "lib", "randoop-all-4.3.4.jar")
WORK = os.path.join(SC, "mut")
CELL = "ar/edu/unrc/game2048/Cell.java"
BOARD = "ar/edu/unrc/game2048/Board.java"

M = {
    "ORIGINAL": None,
    # caso 1 (propuestos por el LLM)
    "C1-M1 (*4)": (CELL, "return new Cell(this.value * 2);", "return new Cell(this.value * 4);"),
    "C1-M2 (v==1?4)": (CELL, "return new Cell(this.value * 2);", "return new Cell(this.value == 1 ? 4 : this.value * 2);"),
    "C1-M3 (v==1?8)": (CELL, "return new Cell(this.value * 2);", "return new Cell(this.value == 1 ? 8 : this.value * 2);"),
    # caso 2 (propuestos por el LLM; ninguno toca getScore)
    "C2-M1 (move: suma operando)": (BOARD, "score += mergedCell.getValue();", "score += nonEmpty.get(i).getValue();"),
    "C2-M2 (move: suma 0)": (BOARD, "score += mergedCell.getValue();", "score += 0;"),
    "C2-M3 (addRandomTile suma)": (BOARD, "grid[pos.row][pos.col] = new Cell(value);", "grid[pos.row][pos.col] = new Cell(value); score += value;"),
    # caso 2: mutantes DEL MÉTODO ESPECIFICADO (getScore), agregados por nosotros como control
    "C2-G1 (getScore: return 0)": (BOARD, "public int getScore() {\n        return score;", "public int getScore() {\n        return 0;"),
    "C2-G2 (getScore: score+1)": (BOARD, "public int getScore() {\n        return score;", "public int getScore() {\n        return score + 1;"),
    # caso 3 (propuestos por el LLM)
    "C3-M1 (!isEmpty)": (BOARD, "if (grid[r][c].isEmpty()) {\n                    empty.add(new Position(r, c));",
                         "if (!grid[r][c].isEmpty()) {\n                    empty.add(new Position(r, c));"),
    "C3-M2 (Position(c,r))": (BOARD, "empty.add(new Position(r, c));", "empty.add(new Position(c, r));"),
    "C3-M3 (size-1)": (BOARD, "Set<Position> empty = new HashSet<>();\n        for (int r = 0; r < size; r++) {\n            for (int c = 0; c < size; c++) {\n                if (grid[r][c].isEmpty()) {",
                       "Set<Position> empty = new HashSet<>();\n        for (int r = 0; r < size - 1; r++) {\n            for (int c = 0; c < size - 1; c++) {\n                if (grid[r][c].isEmpty()) {"),
    # caso 1, segunda corrida: el LLM dijo que no hay mutantes; probamos los nuestros
    "C1-X1 (sin guarda canMergeWith)": (CELL, "if (!canMergeWith(other)) {\n            throw new IllegalArgumentException(\n                \"Cannot merge cells: \" + this + \" and \" + other\n            );\n        }", ""),
    "C1-X2 (value << 1)": (CELL, "return new Cell(this.value * 2);", "return new Cell(this.value << 1);"),
    "C1-X3 (value + other.value)": (CELL, "return new Cell(this.value * 2);", "return new Cell(this.value + other.value);"),
    # caso 2, segunda corrida (propuestos por el LLM)
    "C2R-M1 (score = 10 inicial)": (BOARD, "private int score;", "private int score = 10;"),
    "C2R-M2 (move sin sumar)": (BOARD, "score += mergedCell.getValue();", ""),
    # caso 3, segunda corrida (propuestos por el LLM; ninguno toca getEmptyPositions)
    "C3R-M1 (2/4 invertido)": (BOARD, "< 90 ? 2 : 4;", "< 90 ? 4 : 2;"),
    "C3R-M2 (moved invertido)": (BOARD, "boolean moved = !this.equals(previous);", "boolean moved = this.equals(previous);"),
    "C3R-M3 (primer elemento del iterador)": (BOARD, "Position pos = empty.stream().skip(randomIndex).findFirst().get();", "Position pos = empty.iterator().next();"),
    # tercera ronda (prompts v2): mutantes de getScore con efectos secundarios (propuestos por el LLM)
    "C2V2-G3 (return this.score = 0)": (BOARD, "public int getScore() {\n        return score;", "public int getScore() {\n        return this.score = 0;"),
    "C2V2-G4 (this.score = 0; return this.score)": (BOARD, "public int getScore() {\n        return score;", "public int getScore() {\n        this.score = 0; return this.score;"),
    "C2V2-G5 (return ++this.score)": (BOARD, "public int getScore() {\n        return score;", "public int getScore() {\n        return ++this.score;"),
    "C2V2-G6 (return this.score += 1)": (BOARD, "public int getScore() {\n        return score;", "public int getScore() {\n        return this.score += 1;"),
    # tercera ronda: mutantes de getEmptyPositions (propuestos por el LLM)
    "C3V2-M1 (LinkedHashSet)": (BOARD, "Set<Position> empty = new HashSet<>();\n        for (int r", "Set<Position> empty = new java.util.LinkedHashSet<>();\n        for (int r"),
    "C3V2-M2 (unmodifiableSet)": (BOARD, "return empty;", "return java.util.Collections.unmodifiableSet(empty);"),
    "C3V2-M3 (bucles inversos)": (BOARD, "Set<Position> empty = new HashSet<>();\n        for (int r = 0; r < size; r++) {\n            for (int c = 0; c < size; c++) {", "Set<Position> empty = new HashSet<>();\n        for (int r = size - 1; r >= 0; r--) {\n            for (int c = size - 1; c >= 0; c--) {"),
}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", **kw)


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    sel = sys.argv[1:]
    for name, mut in M.items():
        if sel and not any(s in name for s in sel):
            continue
        tag = re.sub(r"\W+", "_", name)
        src = os.path.join(WORK, tag, "src")
        cls = os.path.join(WORK, tag, "classes")
        shutil.copytree(SRC, src)
        os.makedirs(cls)
        if mut:
            f, old, new = mut
            path = os.path.join(src, f)
            text = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
            assert text.count(old) == 1, f"{name}: el patrón aparece {text.count(old)} veces"
            open(path, "w", encoding="utf-8", newline="").write(text.replace(old, new))
        files = [os.path.join(d, x) for d, _, fs in os.walk(src) for x in fs if x.endswith(".java")]
        c = run(["javac", "-nowarn", "-cp", LIB, "-d", cls] + files)
        if c.returncode:
            print(f"### {name}: NO COMPILA\n{c.stderr}")
            continue
        v = run(["javac", "-cp", cls, "-d", os.path.join(WORK, tag), os.path.join(SC, "Verif.java")])
        if v.returncode:
            print(v.stderr); sys.exit(1)
        r = run(["java", "-ea", "-cp", os.pathsep.join([cls, os.path.join(WORK, tag), LIB]), "Verif"])
        print(f"### {name}")
        print(r.stdout.rstrip() or r.stderr.rstrip()[:600])
        print()


main()
