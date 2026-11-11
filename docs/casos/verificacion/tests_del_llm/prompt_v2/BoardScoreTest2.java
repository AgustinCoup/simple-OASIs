import static org.junit.Assert.assertTrue;
import org.junit.Test;
import ar.edu.unrc.game2048.Board;

public class BoardScoreTest2 {
    @Test
    public void scoreExceedsWinningValue() {
        Board board = new Board(4, "0,0,0,0;0,0,0,0;0,0,0,0;1024,1024,1024,1024");
        assertTrue(board.moveLeft());
        int result = board.getScore();
        boolean contrato = result == board.getScore() && result >= 0 && result < Board.WINNING_VALUE;
        assertTrue(contrato);
    }
}
