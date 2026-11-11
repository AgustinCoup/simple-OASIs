import ar.edu.unrc.game2048.*;
import java.lang.reflect.Field;
import ar.edu.unrc.game2048.RandomNumGeneration.DeterministicRandom;
import java.util.*;

/** Arnés de verificación: evalúa aserciones originales (A*) y refinadas (R*) sobre las clases del classpath. */
public class Verif {
    static int scoreField(Board b) throws Exception {
        Field f = Board.class.getDeclaredField("score");
        f.setAccessible(true);
        return f.getInt(b);
    }

    static void p(String k, Object v) { System.out.println(k + " | " + v); }

    // ---- Caso 1: Cell.mergeWith ----
    static boolean A1(Cell t, Cell o, Cell r) {
        int v = t.getValue(), w = o.getValue();
        return r != null && v == w && (v == 1 || v == 2 || v == 4)
            && (r.getValue() == 2 || r.getValue() == 4 || r.getValue() == 8)
            && v < r.getValue() && r.getValue() % v == 0;
    }
    static boolean R1(Cell t, Cell o, Cell r) {
        return r != null && t.getValue() == o.getValue() && t.getValue() > 0 && r.getValue() == 2 * t.getValue();
    }

    // ---- Caso 2: Board.getScore ----
    static boolean A2(Board b, int res) throws Exception { return res == scoreField(b) && res >= 0 && res < Board.WINNING_VALUE; }
    static boolean R2(Board b, int res) throws Exception { return res == scoreField(b) && res >= 0; }

    // Versión que además exige que getScore no modifique el estado (equivale a usar \old(this.score)).
    static boolean R2p(Board b, int res, int antes) throws Exception {
        return res == scoreField(b) && res >= 0 && scoreField(b) == antes;
    }

    static String ceros(int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            if (i > 0) sb.append(';');
            for (int j = 0; j < n; j++) { if (j > 0) sb.append(','); sb.append('0'); }
        }
        return sb.toString();
    }

    // ---- Caso 3: Board.getEmptyPositions ----
    static boolean A3(Set<Board.Position> r) { return r != null && r.getClass() == HashSet.class; }
    static boolean R3(Board b, Set<Board.Position> r) {
        if (r == null || !(r instanceof Set)) return false;  // aserción final: instanceof Set (sin fijar HashSet)
        Set<Board.Position> esperado = new HashSet<>();
        for (int i = 0; i < b.getSize(); i++)
            for (int j = 0; j < b.getSize(); j++)
                if (b.getCell(i, j).isEmpty()) esperado.add(new Board.Position(i, j));
        return r.equals(esperado);
    }

    static String sorted(Set<Board.Position> s) {
        List<String> l = new ArrayList<>();
        for (Board.Position x : s) l.add("(" + x.row + "," + x.col + ")");
        Collections.sort(l);
        return l.toString();
    }

    public static void main(String[] args) throws Exception {
        for (int v : new int[]{1, 2, 4, 8, 16, 32}) {
            Cell a = new Cell(v), b = new Cell(v);
            Cell r = a.mergeWith(b);
            p("C1 merge(" + v + "," + v + ")", "result=" + r.getValue() + " A1=" + A1(a, b, r) + " R1=" + R1(a, b, r));
        }

        Board b = new Board(4, "2,0,0,0;2,0,0,0;0,0,0,0;0,0,0,0");
        b.moveUp();
        int res = b.getScore();
        p("C2 moveUp sobre 2/2 en columna", "getScore=" + res + " A2=" + A2(b, res) + " R2=" + R2(b, res));

        Board b2 = new Board(2, "1024,1024;0,0");
        b2.moveLeft();
        res = b2.getScore();
        p("C2 moveLeft sobre 1024,1024", "getScore=" + res + " A2=" + A2(b2, res) + " R2=" + R2(b2, res));

        Board b3 = new Board();
        res = b3.getScore();
        p("C2 new Board()", "getScore=" + res + " A2=" + A2(b3, res) + " R2=" + R2(b3, res));

        String[][] casos3 = {{"1", "5"}, {"1", "2"}, {"2", "0,2;0,0"}, {"2", "0,0;0,0"}, {"4", "2,0,0,0;0,4,0,0;0,0,0,0;0,0,0,8"}};
        for (String[] c : casos3) {
            try {
                Board bb = new Board(Integer.parseInt(c[0]), c[1]);
                Set<Board.Position> r = bb.getEmptyPositions();
                p("C3 Board(" + c[0] + ",\"" + c[1] + "\")", "vacias=" + sorted(r) + " A3=" + A3(r) + " R3=" + R3(bb, r));
            } catch (Exception e) {
                p("C3 Board(" + c[0] + ",\"" + c[1] + "\")", "EXCEPCION " + e.getClass().getSimpleName() + ": " + e.getMessage());
            }
        }

        // ---------- Segunda corrida (aserciones refinadas): casos borde y escenarios del LLM ----------
        try {
            Cell a = new Cell(2), c = new Cell(4);
            Cell r = a.mergeWith(c);
            p("C1b merge(2,4) [valores distintos]", "result=" + r.getValue() + " R1=" + R1(a, c, r));
        } catch (Exception e) {
            p("C1b merge(2,4) [valores distintos]", "EXCEPCION " + e.getClass().getSimpleName());
        }
        try {
            Cell a = new Cell(1 << 30), c = new Cell(1 << 30);
            Cell r = a.mergeWith(c);
            p("C1b merge(2^30,2^30)", "result=" + r.getValue() + " R1=" + R1(a, c, r));
        } catch (Exception e) {
            p("C1b merge(2^30,2^30)", "EXCEPCION " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }

        Board s2 = new Board(2, "2,2;0,0");
        s2.moveLeft();
        p("C2b moveLeft sobre 2,2", "getScore=" + s2.getScore());

        Board t1 = new Board(1, "0");
        p("C3b Board(1,\"0\")", "vacias=" + sorted(t1.getEmptyPositions()));
        Board t2 = new Board(2, "2,0;0,0");
        p("C3b Board(2,\"2,0;0,0\")", "vacias=" + sorted(t2.getEmptyPositions()));
        Board t3 = new Board(2, "2,2;0,0");
        boolean mv = t3.moveLeft();
        p("C3b Board(2,\"2,2;0,0\").moveLeft()", "devuelve=" + mv + " cantidad_vacias=" + t3.getEmptyPositions().size());
        for (List<Integer> seq : List.of(List.of(0, 95, 0, 5), List.of(1, 50, 1, 50))) {
            Board d = new Board(2, new DeterministicRandom(seq));
            p("C3b Board(2, DeterministicRandom" + seq + ")",
              "tablero=" + d.toString().trim().replace("\n", " / ") + " vacias=" + sorted(d.getEmptyPositions()));
        }

        // ---------- Tercera ronda (prompts v2) ----------
        // Caso 2: mutantes de getScore con efectos secundarios
        Board q = new Board(2, "2,2;0,0");
        q.moveLeft();
        int antes = scoreField(q);
        int r2 = q.getScore();
        p("C2c getScore tras moveLeft(2,2)", "score_antes=" + antes + " resultado=" + r2 + " score_despues=" + scoreField(q)
          + " R2=" + R2(q, r2) + " R2pura=" + R2p(q, r2, antes));
        Board q0 = new Board();
        antes = scoreField(q0);
        r2 = q0.getScore();
        p("C2c getScore en new Board()", "score_antes=" + antes + " resultado=" + r2 + " score_despues=" + scoreField(q0)
          + " R2=" + R2(q0, r2) + " R2pura=" + R2p(q0, r2, antes));

        // Caso 3: testigos propuestos por el LLM y propiedades de la salida
        String[][] casos3c = {{"2", "2,0;0,0"}, {"2", "2,0;2,2"}, {"4", "2,2,2,2;2,2,2,2;2,2,2,2;2,2,2,0"}, {"2", "0,2;4,0"}};
        for (String[] c : casos3c) {
            Board bb = new Board(Integer.parseInt(c[0]), c[1]);
            Set<Board.Position> r = bb.getEmptyPositions();
            String mut;
            try { r.add(new Board.Position(0, 0)); r.remove(new Board.Position(0, 0)); mut = "modificable"; }
            catch (UnsupportedOperationException e) { mut = "NO modificable"; }
            Set<Board.Position> r3 = bb.getEmptyPositions();
            p("C3c Board(" + c[0] + ",\"" + c[1] + "\")", "vacias=" + sorted(r3) + " clase=" + r3.getClass().getSimpleName()
              + " " + mut + " R3=" + R3(bb, r3));
        }
        for (int n = 2; n <= 6; n++) {
            Board bb = new Board(n, ceros(n));
            p("C3c orden de iteracion, tablero vacio " + n + "x" + n, bb.getEmptyPositions().toString());
        }
    }
}
