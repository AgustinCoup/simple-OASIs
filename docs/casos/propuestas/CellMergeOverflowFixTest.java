package ar.edu.unrc.game2048;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

// Test para el parche Cell_mergeWith_overflow.patch (ver docs/casos_de_estudio.md, caso 1).
class CellMergeOverflowFixTest {

    @Test
    void mergeDeDosPotencias2a30LanzaArithmeticException() {
        Cell a = new Cell(1 << 30);
        Cell b = new Cell(1 << 30);
        assertTrue(a.canMergeWith(b));
        assertThrows(ArithmeticException.class, () -> a.mergeWith(b));
    }

    @Test
    void mergeDeLaMayorFusionPosibleSigueFuncionando() {
        Cell a = new Cell(1 << 29);
        Cell b = new Cell(1 << 29);
        assertEquals(1 << 30, a.mergeWith(b).getValue());
    }

    @Test
    void celdasNoFusionablesSiguenLanzandoIllegalArgument() {
        assertThrows(IllegalArgumentException.class, () -> new Cell(2).mergeWith(new Cell(4)));
    }
}
