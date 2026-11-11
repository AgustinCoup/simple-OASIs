package ar.edu.unrc.game2048;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CellMergePostconditionTest {

    @Test
    void mergeOchoConOchoViolaPostcondicionInferida() {
        Cell a = new Cell(8);
        Cell b = new Cell(8);
        Cell result = a.mergeWith(b);

        assertNotNull(result);
        assertEquals(16, result.getValue());

        boolean post = result != null
            && a.getValue() == b.getValue()
            && (a.getValue() == 1 || a.getValue() == 2 || a.getValue() == 4)
            && (result.getValue() == 2 || result.getValue() == 4 || result.getValue() == 8)
            && a.getValue() < result.getValue()
            && result.getValue() % a.getValue() == 0;

        assertFalse(post, "La postcondición inferida rechaza 8 + 8 = 16");
    }

    @Test
    void mergeDieciseisConDieciseisViolaPostcondicionInferida() {
        Cell a = new Cell(16);
        Cell b = new Cell(16);
        Cell result = a.mergeWith(b);

        assertNotNull(result);
        assertEquals(32, result.getValue());

        boolean post = result != null
            && a.getValue() == b.getValue()
            && (a.getValue() == 1 || a.getValue() == 2 || a.getValue() == 4)
            && (result.getValue() == 2 || result.getValue() == 4 || result.getValue() == 8)
            && a.getValue() < result.getValue()
            && result.getValue() % a.getValue() == 0;

        assertFalse(post, "La postcondición inferida rechaza 16 + 16 = 32");
    }
}
