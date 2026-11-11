# Corre la herramienta sobre los casos de estudio (aserción original de Daikon y aserción refinada).
# Ejecutar desde la raíz de simple-OASIs, sin argumentos:
#   $env:OPENROUTER_API_KEY="sk-or-..."
#   $env:OASIS_MODEL="nvidia/nemotron-3.5-super-vl:free"   # opcional (por defecto, Nemotron 3 Ultra gratis)
#   .\docs\casos\correr_casos.ps1
# Si ya existe la salida de un caso en docs/casos/salidas/, se salta. Para repetirlo, borrá ese archivo.
# Las aserciones van sin tildes a propósito: PowerShell 5.1 pasa mal los argumentos con tildes a Python.

$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8  # leer la salida de Python como UTF-8

$casos = @(
    @{ id = "caso1_cell_mergeWith_original"; programa = "docs/casos/Cell.java";
       aserto = "Postcondicion de Cell.mergeWith(Cell other), contrato inferido por Daikon: result != null && this.value == other.value && (this.value == 1 || this.value == 2 || this.value == 4) && (result.value == 2 || result.value == 4 || result.value == 8) && this.value < result.value && result.value % this.value == 0" },
    @{ id = "caso2_board_getScore_original"; programa = "docs/casos/Board.java";
       aserto = "Postcondicion de Board.getScore(), contrato inferido por Daikon: result == this.score && result >= 0 && result < Board.WINNING_VALUE" },
    @{ id = "caso3_board_getEmptyPositions_original"; programa = "docs/casos/Board.java";
       aserto = "Postcondicion de Board.getEmptyPositions(), contrato inferido por Daikon: result != null && result.getClass() == java.util.HashSet.class" },

    # Refinamientos decididos tras la verificacion manual (ver docs/casos_de_estudio.md)
    @{ id = "caso1_cell_mergeWith_refinada"; programa = "docs/casos/Cell.java";
       aserto = "Postcondicion de Cell.mergeWith(Cell other): result != null && this.value == other.value && this.value > 0 && result.value == 2 * this.value" },
    @{ id = "caso2_board_getScore_refinada"; programa = "docs/casos/Board.java";
       aserto = "Postcondicion de Board.getScore(): result == this.score && result >= 0" },
    @{ id = "caso3_board_getEmptyPositions_refinada"; programa = "docs/casos/Board.java";
       aserto = "Postcondicion de Board.getEmptyPositions(): result != null && result instanceof java.util.Set && result es exactamente el conjunto de posiciones (r,c) tales que grid[r][c].isEmpty()" }
)

$modelo = if ($env:OASIS_MODEL) { $env:OASIS_MODEL } else { "nvidia/nemotron-3-ultra-550b-a55b:free" }

foreach ($c in $casos) {
    $out = "docs/casos/salidas/$($c.id).txt"
    if (Test-Path $out) { Write-Host "== $($c.id): ya existe, se salta"; continue }
    Write-Host "== $($c.id) (modelo $modelo) -> $out"
    $salida = python -m oasis $c.programa $c.aserto
    if ($LASTEXITCODE -eq 0) {
        # Solo se guarda si la herramienta terminó bien; así un fallo no deja un archivo a medias.
        @("# Modelo: $modelo") + $salida | Out-File -Encoding utf8 $out
    } else {
        Write-Host "   FALLO (código $LASTEXITCODE): no se guardó salida; volvé a correr el script para reintentar"
    }
}
