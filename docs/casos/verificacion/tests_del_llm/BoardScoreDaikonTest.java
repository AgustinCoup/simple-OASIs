package ar.edu.unrc.game2048;

import static org.junit.Assert.assertTrue;
import org.junit.Test;

public class BoardScoreDaikonTest {

    @Test
    public void getScore_puedeSerIgualAMayorQueWinningValue() {
        Board board = new Board(2, "1024,1024;0,0");
        board.moveLeft();

        int result = board.getScore();

        assertTrue(result == board.getScore());
        assertTrue(result >= 0);
        assertTrue(result < Board.WINNING_VALUE); // falla
    }
}
