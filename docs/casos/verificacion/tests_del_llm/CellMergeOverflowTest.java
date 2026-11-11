package ar.edu.unrc.game2048;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

// Test propuesto por el LLM en la segunda corrida (caso 1, aserción refinada).
// Único cambio: el nombre de la clase (el original se llamaba CellMergePostconditionTest).
class CellMergeOverflowTest {

    @Test
    void mergeWithMaxPowerOfTwoViolatesPostconditionBecauseOfIntOverflow() {
        Cell a = new Cell(1073741824); // 2^30, válida
        Cell b = new Cell(1073741824); // 2^30, válida

        assertTrue(a.canMergeWith(b));

        try {
            Cell result = a.mergeWith(b);
            assertTrue(result != null
                    && a.getValue() == b.getValue()
                    && a.getValue() > 0
                    && result.getValue() == 2 * a.getValue(),
                    "La postcondición de mergeWith no se cumple");
        } catch (IllegalArgumentException e) {
            fail("mergeWith lanzó excepción para entradas válidas; "
                 + "la postcondición asume que siempre hay resultado (demasiado fuerte).");
        }
    }
}
