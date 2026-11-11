import static org.junit.Assert.assertTrue;
import org.junit.Test;
import ar.edu.unrc.game2048.Board;

public class BoardScoreTest1 {
    @Test
    public void scoreReachesWinningValue() {
        Board board = new Board(4, "0,0,0,0;0,0,0,0;0,0,0,0;1024,1024,0,0");
        assertTrue(board.moveLeft());
        int result = board.getScore();
        boolean contrato = result == board.getScore() && result >= 0 && result < Board.WINNING_VALUE;
        assertTrue(contrato);
    }
}
