package ar.edu.unrc.game2048;

import org.junit.Test;
import static org.junit.Assert.assertTrue;

public class CellMergeWithPostconditionTest {

    @Test
    public void mergeWith_8_y_8_devuelve_16_y_viola_postcondicion() {
        Cell origen = new Cell(8);
        Cell otro = new Cell(8);
        Cell resultado = origen.mergeWith(otro);

        boolean post = resultado != null
            && origen.getValue() == otro.getValue()
            && (origen.getValue() == 1 || origen.getValue() == 2 || origen.getValue() == 4)
            && (resultado.getValue() == 2 || resultado.getValue() == 4 || resultado.getValue() == 8)
            && origen.getValue() < resultado.getValue()
            && resultado.getValue() % origen.getValue() == 0;

        assertTrue("La postcondición inferida no debe rechazarse para 8 + 8", post);
    }

    @Test
    public void mergeWith_16_y_16_devuelve_32_y_viola_postcondicion() {
        Cell origen = new Cell(16);
        Cell otro = new Cell(16);
        Cell resultado = origen.mergeWith(otro);

        boolean post = resultado != null
            && origen.getValue() == otro.getValue()
            && (origen.getValue() == 1 || origen.getValue() == 2 || origen.getValue() == 4)
            && (resultado.getValue() == 2 || resultado.getValue() == 4 || resultado.getValue() == 8)
            && origen.getValue() < resultado.getValue()
            && resultado.getValue() % origen.getValue() == 0;

        assertTrue("La postcondición inferida no debe rechazarse para 16 + 16", post);
    }
}
