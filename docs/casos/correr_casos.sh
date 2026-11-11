#!/usr/bin/env bash
set -u

# Ejecutar desde cualquier directorio:
#   export OPENROUTER_API_KEY="sk-or-..."
#   export OASIS_MODEL="nvidia/nemotron-3.5-super-vl:free"  # opcional
#   ./docs/casos/correr_casos.sh
#
# Si ya existe la salida de un caso en docs/casos/salidas/, se salta.
# Para repetirlo, borrar ese archivo.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
MODEL="${OASIS_MODEL:-nvidia/nemotron-3-ultra-550b-a55b:free}"
export PYTHONIOENCODING=utf-8

run_case() {
    local id="$1"
    local program="$2"
    local assertion="$3"
    local output="$PROJECT_ROOT/docs/casos/salidas/$id.txt"
    local result
    local status

    if [[ -f "$output" ]]; then
        printf '== %s: ya existe, se salta\n' "$id"
        return 0
    fi

    printf '== %s (modelo %s) -> %s\n' "$id" "$MODEL" "$output"
    result="$(cd "$PROJECT_ROOT" && python3 -m oasis "$program" "$assertion")"
    status=$?
    if [[ $status -eq 0 ]]; then
        {
            printf '# Modelo: %s\n' "$MODEL"
            printf '%s\n' "$result"
        } > "$output"
    else
        printf '   FALLO (código %s): no se guardó salida; volvé a correr el script para reintentar\n' "$status"
    fi
}

run_case "caso1_cell_mergeWith_original" "docs/casos/Cell.java" \
    "Postcondicion de Cell.mergeWith(Cell other), contrato inferido por Daikon: result != null && this.value == other.value && (this.value == 1 || this.value == 2 || this.value == 4) && (result.value == 2 || result.value == 4 || result.value == 8) && this.value < result.value && result.value % this.value == 0"
run_case "caso2_board_getScore_original" "docs/casos/Board.java" \
    "Postcondicion de Board.getScore(), contrato inferido por Daikon: result == this.score && result >= 0 && result < Board.WINNING_VALUE"
run_case "caso3_board_getEmptyPositions_original" "docs/casos/Board.java" \
    "Postcondicion de Board.getEmptyPositions(), contrato inferido por Daikon: result != null && result.getClass() == java.util.HashSet.class"
run_case "caso1_cell_mergeWith_refinada" "docs/casos/Cell.java" \
    "Postcondicion de Cell.mergeWith(Cell other): result != null && this.value == other.value && this.value > 0 && result.value == 2 * this.value"
run_case "caso2_board_getScore_refinada" "docs/casos/Board.java" \
    "Postcondicion de Board.getScore(): result == this.score && result >= 0"
run_case "caso3_board_getEmptyPositions_refinada" "docs/casos/Board.java" \
    "Postcondicion de Board.getEmptyPositions(), result != null && result instanceof java.util.Set && result es exactamente el conjunto de posiciones (r,c) tales que grid[r][c].isEmpty()"
