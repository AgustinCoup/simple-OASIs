# Casos de estudio: refinamiento de contratos de Daikon con simple-OASIs

## Resumen

Se aplicó simple-OASIs a tres postcondiciones que Daikon infirió sobre el proyecto Java
`reliable-2048-mai-becerra` (clases `Cell` y `Board`), en **tres rondas**: (1) sobre la aserción original de
Daikon, (2) sobre la aserción refinada con ese feedback y (3) otra vez sobre ambas, con los prompts mejorados a partir
de las fallas observadas. Cada propuesta del LLM se **verificó ejecutando código real** (JUnit con Maven y mutantes
compilados), porque la herramienta no ejecuta nada.

| Caso | Método | Problema confirmado | Aserción final adoptada |
|---|---|---|---|
| 1 | `Cell.mergeWith` | **Fuerte y débil a la vez**: sobreajuste de Daikon y falta de `result.value == 2 * this.value`. Además, un caso borde del programa (desbordamiento con `2^30`) | `result != null && this.value == other.value && this.value > 0 && result.value == 2 * this.value`; el desbordamiento se resuelve con un parche propuesto |
| 2 | `Board.getScore` | **Fuerte** (cota de 2048) y **débil** (no exige que el getter deje el estado intacto; descubierto recién en la ronda 3) | `result == this.score && result >= 0 && this.score == \old(this.score)` |
| 3 | `Board.getEmptyPositions` | **Débil** | `result != null && result instanceof Set` y `result` es exactamente el conjunto de posiciones vacías |

**Resultados principales**
- **Tests propuestos para aserciones fuertes: 7 de 7 confirmados** al ejecutarlos (3 con los prompts v1 y 4 con los v2).
  Donde no había violación (caso 3, y los casos refinados), la herramienta no inventó ninguna.
- **Ronda 1 y 2 (prompts v1): 15 mutantes**, de los cuales **8 eran falsas alarmas por alcance** (mutaban otro método),
  1 era equivalente y 4 de las 15 entradas testigo estaban mal. Ese ruido tapó una debilidad real del caso 2.
- **Ronda 3 (prompts v2): 12 mutantes, los 12 dentro del alcance, ninguno equivalente y 12 de 12 testigos correctos.**
  Con el ruido fuera, la herramienta mostró que `getScore` puede modificar el estado sin que la aserción lo detecte
  (`return ++this.score` sobrevive a la aserción de Daikon y a la que habíamos refinado).
- **Dos hallazgos que no se habían buscado:** el desbordamiento de `Cell.mergeWith` con `2^30` y la debilidad de
  `getScore` frente a efectos secundarios. Esta última se debía en parte a que **la traducción manual de los contratos
  de Daikon descartó las cláusulas `orig(...)`** que sí lo detectaban.
- **Salvedad importante:** los prompts v2 se diseñaron mirando los errores de las rondas 1 y 2 sobre estos mismos tres
  casos. La mejora observada no es una validación independiente.

## Contexto

- **Proyecto:** `reliable-2048-mai-becerra`, juego 2048 en Java (paquete `ar.edu.unrc.game2048`).
- **Contratos de partida:** postcondiciones de `daikon-output-completo.txt` (Daikon 5.9.0, sobre trazas de tests
  manuales, EvoSuite y Randoop), traducidas a mano a expresiones Java (`return` → `result`; se descartaron las
  cláusulas con `orig(...)` y las que solo describen que el estado no cambia).
- **Herramienta:** simple-OASIs. Dos consultas por caso al LLM: una busca tests que violen la aserción
  (aserción demasiado fuerte) y otra busca mutantes que no la matan (aserción demasiado débil).
- **Modelo:** `nvidia/nemotron-3.5-super-vl:free` vía OpenRouter. Se quería usar Nemotron 3 Ultra gratuito,
  pero durante las corridas su proveedor estaba caído (OpenRouter informaba 0 % de disponibilidad en los
  últimos 5 minutos y la API devolvía error 504). Cada archivo de `salidas/` registra el modelo en su primera línea.
- **Dos corridas por caso** (`salidas/..._original_prompt_v1.txt` y `salidas/..._refinada_prompt_v1.txt`), una por ronda. El LLM no es
  determinista, así que los resultados son una muestra, no una medición estadística.
- **La herramienta cambió entre rondas** (ver Limitaciones): los prompts ganaron la frase "limita la búsqueda" y el
  cliente ajusta el razonamiento si se agota el presupuesto de tokens. Todas las salidas guardadas corresponden a esa
  versión de los prompts (`prompt_v1`); después se aplicaron las mejoras descritas en la Evaluación.

## Metodología

1. Correr la herramienta: `docs/casos/correr_casos.ps1` (salidas crudas en `docs/casos/salidas/`).
2. **Tests propuestos:** se pegaron tal cual en una copia del proyecto y se corrieron con `mvn test`
   (`verificacion/tests_del_llm/`).
3. **Mutantes propuestos:** se aplicó cada cambio a una copia de `Cell.java` / `Board.java`, se compiló y se
   corrió un arnés (`verificacion/Verif.java`) que evalúa la aserción original y la refinada sobre el original
   y sobre cada mutante (`verificacion/mutar.py`; resultados en `verificacion/resultados_mutantes.txt`).
4. Se agregaron, como control, mutantes del propio `getScore` (caso 2).
5. Se decidió el refinamiento y se comprobó, ejecutando, que se cumple en el original y mata los mutantes.
6. **Segunda ronda:** se volvió a correr la herramienta sobre las aserciones refinadas y se repitió la verificación
   (tests con JUnit, mutantes y escenarios nuevos en el arnés). Donde el LLM afirmó "no hay mutantes", se probaron
   mutantes propios para contrastarlo.

7. **Tercera ronda:** tras mejorar los prompts se repitieron las seis corridas y se verificó igual (tests de
   `verificacion/tests_del_llm/prompt_v2/`, mutantes y escenarios nuevos en el arnés).

El proyecto original no se modificó; todo se hizo sobre copias.

---

## Caso 1: `Cell.mergeWith` (aserción fuerte y débil a la vez)

**Aserción (Daikon):**
`result != null && this.value == other.value && (this.value == 1 || this.value == 2 || this.value == 4) && (result.value == 2 || result.value == 4 || result.value == 8) && this.value < result.value && result.value % this.value == 0`

### Falsos positivos (aserción demasiado fuerte)
El LLM propuso 2 tests JUnit: fusionar `Cell(8)+Cell(8)` y `Cell(16)+Cell(16)`, y clasificó ambos como
"aserción demasiado fuerte; el programa es correcto".

| Test | Resultado real | ¿Viola la aserción? |
|---|---|---|
| `Cell(8).mergeWith(Cell(8))` | `Cell(16)` | **Sí** (confirmado con Maven/JUnit) |
| `Cell(16).mergeWith(Cell(16))` | `Cell(32)` | **Sí** (confirmado con Maven/JUnit) |

Diagnóstico confirmado: `this.value ∈ {1,2,4}` y `result.value ∈ {2,4,8}` son sobreajuste de Daikon a los
tests que solo fusionaron valores chicos. El programa es correcto: `Cell` admite cualquier potencia de 2.

### Falsos negativos (aserción demasiado débil)
El LLM propuso 3 mutantes; los 3 **sobreviven** a la aserción original y difieren del original:

| Mutante | Entrada | Original → mutante | Aserción original |
|---|---|---|---|
| `this.value * 4` | `Cell(2)+Cell(2)` | 4 → 8 | se cumple (sobrevive) |
| `this.value == 1 ? 4 : this.value * 2` | `Cell(1)+Cell(1)` | 2 → 4 | se cumple (sobrevive) |
| `this.value == 1 ? 8 : this.value * 2` | `Cell(1)+Cell(1)` | 2 → 8 | se cumple (sobrevive) |

Matiz descubierto al verificar: la supervivencia depende de la entrada. El mutante `*4` con `Cell(4)+Cell(4)`
produce 16, que cae fuera de `{2,4,8}`, y la parte sobreajustada de la aserción lo "mata" por accidente. La
debilidad (falta de `result.value == 2 * this.value`) queda tapada por el sobreajuste solo en ciertas entradas.

### Refinamiento
Ambas secciones de la salida **convergen** en la misma aserción, lo que da confianza:

`result != null && this.value == other.value && this.value > 0 && result.value == 2 * this.value`

**Validación ejecutando:** se cumple en el original para valores 1, 2, 4, 8, 16 y 32, y **mata los 3 mutantes**
(en `Cell(1)+Cell(1)` o `Cell(2)+Cell(2)`).

---

## Caso 2: `Board.getScore` (aserción fuerte; caso de control para debilidad)

**Aserción (Daikon):** `result == this.score && result >= 0 && result < Board.WINNING_VALUE`

### Falsos positivos (aserción demasiado fuerte)
El LLM propuso un test JUnit 4: tablero 2×2 `"1024,1024;0,0"`, `moveLeft()`, y comprobar
`result < Board.WINNING_VALUE`.

- **Confirmado:** al ejecutarlo, el test falla justo en esa línea. `getScore()` devuelve **2048**
  (`A2=false` en el arnés).
- Causa: `Board.move` hace `score += mergedCell.getValue()`, así que el puntaje acumulado puede superar 2048 en
  una partida normal. El programa es correcto; la cota es un artefacto de que los tests de Daikon nunca
  acumularon tanto puntaje.

### Falsos negativos (control)
Este caso se eligió como control, con la hipótesis de que `result == this.score` caracteriza a `getScore`, de modo
que no deberían sobrevivir mutantes de ese método. Los mutantes **puros** de `getScore` que agregamos (`return 0` y
`return score + 1`) **son matados** por la aserción original. **Pero la hipótesis estaba incompleta**: no se probaron
mutantes con efectos secundarios, que sí sobreviven (ver la tercera ronda).

Sin embargo, el LLM propuso 3 mutantes que **sí sobreviven**, y los 3 están en otros métodos:

| Mutante propuesto | Método mutado | Original → mutante | Sobrevive a la aserción |
|---|---|---|---|
| `score += nonEmpty.get(i).getValue()` | `Board.move` | 4 → 2 | sí |
| `score += 0` | `Board.move` | 4 → 0 | sí |
| `score += value` tras agregar celda | `Board.addRandomTile` | 0 → 4 (`new Board()`) | sí |

Las descripciones del LLM son correctas (los resultados coinciden con la ejecución), pero **no son evidencia de
debilidad de la aserción**: una postcondición de `getScore` no puede ni debe detectar bugs en `move`; eso
corresponde a las postcondiciones de `move`. Es una **falsa alarma por alcance**: la herramienta no limita los
mutantes al método del que habla la aserción.

### Refinamiento
`result == this.score && result >= 0` (solo se quita la cota superior).

**Validación ejecutando:** se cumple en el original en los 3 escenarios (incluido el de 2048) y mata los mutantes
puros de `getScore`.

> **Corrección posterior (ronda 3):** este refinamiento quedó incompleto. No mata mutantes con efectos secundarios
> y se completa con `this.score == \old(this.score)` (ver la tercera ronda).

---

## Caso 3: `Board.getEmptyPositions` (aserción débil)

**Aserción (Daikon):** `result != null && result.getClass() == java.util.HashSet.class`

### Falsos positivos (aserción demasiado fuerte)
El LLM **no encontró tests que la violen**, y es correcto: la aserción se cumple en todas las entradas
ejecutadas. Esto es un acierto: la herramienta reconoce cuándo no hay evidencia y no inventa casos.

Observación: el LLM agregó que la aserción es "demasiado fuerte como contrato" porque fija la clase concreta
(`HashSet`) y sugirió debilitarla a `result != null`. Ninguna ejecución respalda eso (es una opinión de diseño),
y esa sugerencia va en sentido contrario a la de la sección de mutantes. Decidir entre ambas es tarea del usuario.

### Falsos negativos (aserción demasiado débil)
| Mutante propuesto | Entrada del LLM | Resultado verificado |
|---|---|---|
| `!grid[r][c].isEmpty()` | `new Board(1, "5")` | **Entrada inválida**: `IllegalArgumentException` (5 no es potencia de 2). El mutante sí es válido: con `Board(1,"2")` el original da `{}` y el mutante `{(0,0)}` |
| `new Position(c, r)` | `Board(2, "0,2;0,0")` | original `{(0,0),(1,0),(1,1)}`, mutante `{(0,0),(0,1),(1,1)}`: coincide con lo dicho |
| bucles hasta `size - 1` | `Board(2, "0,0;0,0")` | original: 4 posiciones, mutante: `{(0,0)}`: coincide con lo dicho |

Los 3 mutantes sobreviven a la aserción original. Como en el caso 1, la supervivencia depende de la entrada:
`new Position(c, r)` es indistinguible en tableros simétricos, como el vacío.

### Refinamiento
`result != null && result.getClass() == HashSet.class && result` **es exactamente** el conjunto de posiciones
`(r,c)` con `grid[r][c].isEmpty()`. Para comprobarlo se calculó el conjunto esperado con `getCell` (otro método),
no con el que se está especificando.

**Validación ejecutando:** se cumple en el original en 4 tableros válidos y **mata los 3 mutantes**.

**Aserción final adoptada (tras la segunda ronda):** se reemplaza `result.getClass() == HashSet.class` por
`result instanceof Set`, como sugirió el LLM, para no atar el contrato a la implementación:
`result != null && result instanceof java.util.Set && result` es exactamente el conjunto de posiciones vacías.
Se volvió a validar ejecutando: se cumple en el original y mata los 3 mutantes (cada uno muere en al menos un
tablero; `new Position(c, r)` solo sobrevive en tableros simétricos).

---

## Segunda ronda: aserciones refinadas

Se corrió la herramienta sobre cada aserción refinada (`salidas/..._refinada_prompt_v1.txt`) y se verificó igual que antes
(`verificacion/resultados_mutantes.txt` incluye los mutantes y escenarios nuevos).

### Caso 1: `Cell.mergeWith` con `result != null && this.value == other.value && this.value > 0 && result.value == 2 * this.value`

**Aserción demasiado fuerte: hallazgo real.** El LLM propuso `new Cell(1073741824)` (2^30, el mayor valor válido)
fusionada con otra igual. Se ejecutó con JUnit y el test falla como predijo: `a.canMergeWith(b)` es `true`, pero
`mergeWith` calcula `this.value * 2`, que desborda a `-2147483648`, y el constructor lanza
`IllegalArgumentException: Cell value cannot be negative or not a power of two: -2147483648`.

Cómo interpretarlo (es una decisión del usuario):
- El LLM lo rotuló "aserción demasiado fuerte", pero eso es discutible. Una postcondición describe lo que vale
  **cuando el método retorna**, y aquí no hay retorno: ninguna llamada que termine normalmente viola la aserción.
  Lo que no se cumple es el comportamiento excepcional: el Javadoc de `mergeWith` dice que lanza
  `IllegalArgumentException` solo si las celdas no se pueden fusionar, y aquí sí se pueden.
- Opciones: (a) acotar el contrato con una precondición (`this.value <= Integer.MAX_VALUE / 2`, o sea valores hasta
  2^29); (b) corregir el programa para detectar el desbordamiento y lanzar una excepción con un mensaje claro; o
  (c) dejarlo así, porque 2^30 no se alcanza en partidas normales (en un tablero 4x4 el máximo teórico es 2^17).

**Aserción demasiado débil: "No encontré mutantes no matados".** Se contrastó con mutantes propios de `mergeWith`:

| Mutante propio | Resultado |
|---|---|
| quitar la guarda `if (!canMergeWith(other)) throw ...` | **muere**: con `Cell(2)+Cell(4)` devuelve 4 y se viola `this.value == other.value` |
| `this.value << 1` en lugar de `this.value * 2` | equivalente (se comporta igual, incluso en el desbordamiento) |
| `this.value + other.value` en lugar de `this.value * 2` | equivalente (los valores son iguales) |

La conclusión del LLM es consistente: con la aserción refinada no sobrevive ningún mutante no equivalente de los
probados. La "aserción más fuerte" que sugiere igualmente (`result != this`, `result.repOK()`) no agrega nada:
son propiedades que ya se cumplen siempre.

**Corrección propuesta para el programa (decisión tomada: proponerla, no aplicarla).** El desbordamiento es un
defecto de comportamiento excepcional, así que la propuesta es corregir `Cell.mergeWith`, no debilitar la
aserción. El parche (`docs/casos/propuestas/Cell_mergeWith_overflow.patch`) cambia una línea y documenta la excepción:

```diff
      * @throws IllegalArgumentException if the cells cannot be merged
+     * @throws ArithmeticException if the merged value does not fit in an int (this.value * 2 overflows)
 ...
-        return new Cell(this.value * 2);
+        return new Cell(Math.multiplyExact(this.value, 2));
```

Verificado ejecutando, sobre una copia (el proyecto original no se modificó):
- El parche **aplica limpio** sobre `Cell.java` del proyecto.
- Los **tests existentes siguen pasando**: `BoardTest` 47/47 y `CellTest` 22/22.
- El comportamiento normal no cambia, y con `2^30 + 2^30` ahora se lanza `ArithmeticException("integer overflow")`
  en lugar de la `IllegalArgumentException` con el mensaje engañoso sobre valores negativos.
- Se agregó `docs/casos/propuestas/CellMergeOverflowFixTest.java` (3 tests): **pasan con el parche y el de
  desbordamiento falla sobre el original**.

Con el parche, la aserción refinada del caso 1 no necesita cambios: describe los retornos normales y el
comportamiento excepcional queda documentado en el Javadoc.

### Caso 2: `Board.getScore` con `result == this.score && result >= 0`

**Aserción demasiado fuerte:** "no se pueden generar tests". Es consistente con la ejecución: la aserción se cumple
en todos los escenarios (incluido el de 2048).

**Aserción demasiado débil:** 3 mutantes, ninguno relevante *en esta ronda* (en la tercera, con otros prompts, sí aparecieron mutantes relevantes).

| Mutante propuesto | Método | Resultado verificado |
|---|---|---|
| `private int score = 10;` | campo | **Equivalente**: todos los constructores (salvo el de copia) hacen `this.score = 0`, así que `new Board().getScore()` sigue siendo 0. El LLM afirmó lo contrario |
| quitar `score += mergedCell.getValue()` | `Board.move` | Real: `Board(2,"2,2;0,0").moveLeft()` da score 4 en el original y 0 en el mutante. Fuera de alcance |
| `score += value` en `addRandomTile` | `Board.addRandomTile` | Real: `new Board()` da score 0 en el original y 4 en el mutante. Fuera de alcance |

Es la misma **falsa alarma por alcance** de la primera ronda: las postcondiciones de `move` y `addRandomTile`
son las que deben detectar esos bugs, no la de `getScore`. Además, el LLM propone como "aserción más fuerte" cosas
sobre `move`, que no tienen que ver con `getScore`.

### Caso 3: `Board.getEmptyPositions` con el conjunto exacto de posiciones vacías

**Aserción demasiado fuerte:** sin tests, correcto. El LLM vuelve a decir que fijar `HashSet.class` acopla la
aserción a la implementación y sugiere `instanceof Set` más el contenido exacto. Es una opinión de diseño sin
violación ejecutable detrás (la misma de la primera ronda). Adoptarla o no es decisión del usuario.

**Aserción demasiado débil:** 3 mutantes, los 3 fuera de alcance (ninguno toca `getEmptyPositions`).

| Mutante propuesto | Método | Entrada del LLM | Resultado verificado |
|---|---|---|---|
| `< 90 ? 4 : 2` | `addRandomTile` | `new Board(1, "0")` | **Testigo inválido**: el constructor con `setup` no agrega fichas, así que original y mutante dan igual (`{(0,0)}`). Con `DeterministicRandom` sí cambian los valores del tablero, pero no el conjunto de vacías |
| `moved = this.equals(previous)` | `Board.move` | `Board(2,"2,2;0,0").moveLeft()` | Correcto: original devuelve `true` con 2 vacías, mutante `false` con 3 |
| `empty.iterator().next()` | `addRandomTile` | `Board(2,"2,0;0,0")` | **Testigo inválido**: mismo motivo. Con `DeterministicRandom([1,50,1,50])` las vacías sí difieren (`{(0,1),(1,0)}` contra `{(0,1),(1,1)}`) |

Aparece un error nuevo del LLM: **confunde constructores**. Dice que el constructor invoca `addRandomTile` dos veces,
pero eso vale para `Board(int, IRandom)`, no para `Board(int, String)`.

### Qué muestra la segunda ronda
Con los prompts v1, tras refinar, la herramienta pareció dejar de encontrar debilidades dentro del alcance de cada
aserción: lo que reportaba era ruido de alcance (8 de 15 mutantes) y, en el caso 1, un caso borde genuino. **La
tercera ronda mostró que esa conclusión era optimista**: en el caso 2 el ruido tapaba una debilidad real.

---

## Tercera ronda: prompts mejorados (`prompt_v2`)

Se repitieron las seis corridas con los prompts nuevos (`salidas/..._original.txt` y `salidas/..._refinada.txt`; las de
las rondas 1 y 2 quedaron como `..._prompt_v1.txt`). Mismo modelo (`nemotron-3.5-super-vl:free`).

### Comparación

| Indicador | Prompts v1 (rondas 1 y 2) | Prompts v2 (ronda 3) |
|---|---|---|
| Tests propuestos / confirmados al ejecutarlos | 3 / 3 | 4 / 4 |
| Estilo de los tests | mixto (`assertFalse` en unos, `assertTrue` en otros) | uno solo: `assertTrue` sobre la aserción, falla si se viola (4 de 4) |
| Mutantes propuestos | 15 | 12 |
| Mutantes fuera del alcance de la aserción | **8** | **0** |
| Mutantes equivalentes | 1 | 0 |
| Entradas testigo que muestran la diferencia dicha | 11 de 15 | **12 de 12** |
| Sugerencias de cambio sin haber encontrado nada | varias | ninguna |
| Clasificación del desbordamiento de `Cell` | "aserción demasiado fuerte" (discutible) | "no es una violación de postcondición de retorno normal" |

### Caso 1: `Cell.mergeWith`
- **Aserción original:** 2 tests (8+8 y 16+16), ambos **fallan** al ejecutarlos, es decir, confirman la violación. 2 mutantes
  (`* 4` y `v == 1 ? 4 : v * 2`), los mismos de la ronda 1, con testigos correctos. Sugiere
  `result.value == 2 * this.value`: la misma aserción refinada.
- **Aserción refinada:** "No encontré tests" y "No encontré mutantes". Sobre el desbordamiento con `2^30` dice
  que lanza excepción antes de retornar y por lo tanto no viola una postcondición de retorno normal: es la lectura
  correcta (ver ronda 2). No sugiere cambios, como corresponde.

### Caso 2: `Board.getScore`: una debilidad real que las rondas anteriores no vieron
- **Aserción original:** 2 tests con tablero 4x4 y `moveLeft()`: puntaje 2048 y 4096, ambos **fallan** al ejecutarlos (confirmados).
  Sugiere quitar la cota superior.
- **Mutantes (todos de `getScore`, ya dentro del alcance):** `return this.score = 0;` y `this.score = 0; return this.score;`
  (en la aserción original) y `return ++this.score;` y `return this.score += 1;` (en la refinada).

| Mutante | Con `moveLeft` (score antes = 4) | Con `new Board()` (score antes = 0) | Aserción refinada | Con "no modifica el estado" |
|---|---|---|---|---|
| `return this.score = 0` | devuelve 0, deja score en 0 | igual que el original | **sobrevive** | muere |
| `this.score = 0; return this.score` | devuelve 0, deja score en 0 | igual que el original | **sobrevive** | muere |
| `return ++this.score` | devuelve 5, deja score en 5 | devuelve 1, deja score en 1 | **sobrevive** | muere |
| `return this.score += 1` | devuelve 5, deja score en 5 | devuelve 1, deja score en 1 | **sobrevive** | muere |

La aserción compara `result` con el `this.score` posterior a la llamada, así que no puede ver que el método lo
modificó. La **debilidad es real y estaba en el contrato desde el principio**: en la salida de Daikon, `getScore` tenía
`return == orig(this.score)` (junto con `this.score == return`), que las mataba. **Los descarté yo al traducir los
contratos** (dejé afuera las cláusulas con `orig(...)` por considerarlas triviales). Es decir, la herramienta detectó
una pérdida de información de nuestra propia traducción.

Además, mi hipótesis de "caso de control" (ronda 1) estaba equivocada: `result == this.score` no caracteriza a un getter.

**Aserción final adoptada:** `result == this.score && result >= 0 && this.score == \old(this.score)`. Verificada ejecutando:
se cumple en el original y mata los 4 mutantes. Con `new Board()` los dos que ponen el score en 0 coinciden con el
original, porque ya valía 0; mueren en el escenario con puntaje distinto de 0.
- **Aserción refinada (la de la ronda 2):** no encontró tests (correcto). Las salidas guardadas analizaron esa versión,
  anterior a esta corrección.

### Caso 3: `Board.getEmptyPositions`
- **Aserción original:** sin tests (correcto). 3 mutantes de `getEmptyPositions` (`!isEmpty`, `Position(c, r)`,
  bucles hasta `size - 1`), los 3 con **testigos que se verificaron correctos** (en la ronda 1 uno era inválido y varios
  no ejercitaban el cambio). Sugiere el conjunto exacto: la misma refinación que adoptamos.
- **Aserción refinada (conjunto exacto, `instanceof Set`):** sin tests (correcto). 3 mutantes dentro del alcance que
  **sobreviven**, todos verificados:

| Mutante | Qué cambia realmente |
|---|---|
| `new HashSet<>()` por `new LinkedHashSet<>()` | La clase concreta y el orden de iteración. Con `DeterministicRandom([1,50,1,50])` las fichas iniciales caen en otras posiciones |
| `return Collections.unmodifiableSet(empty)` | El conjunto devuelto ya no se puede modificar (`add` lanza `UnsupportedOperationException`) |
| bucles en orden inverso | El orden de iteración del `HashSet` (en 2x2: `[(1,0),(0,0),(1,1),(0,1)]` pasa a `[(1,0),(1,1),(0,0),(0,1)]`); en esa partida determinística el tablero coincide, pero no siempre |

Los tres sobreviven **por diseño**: la aserción final no fija la clase concreta, la mutabilidad ni el orden. Es
coherente con la decisión de usar `instanceof Set`. Queda anotado un riesgo para los desarrolladores: como
`addRandomTile` elige con `empty.stream().skip(randomIndex)`, **la reproducibilidad de las partidas con semilla depende
del orden de iteración del `HashSet`**, que no forma parte de ningún contrato. Se mantiene la aserción adoptada.

### Qué muestra la tercera ronda
- Las reglas de los prompts funcionaron donde se midió: el alcance de los mutantes, la validez de los testigos, la
  ausencia de mutantes equivalentes y el estilo único de test.
- Al quitar el ruido, la herramienta encontró una debilidad real que había pasado desapercibida.
- Con prudencia: son 12 mutantes y 4 tests, una sola corrida y un solo modelo, y las reglas se derivaron de estos mismos casos.

---

## Evaluación de la herramienta

Lo que sigue describe la versión v1 de los prompts (rondas 1 y 2); el efecto de las mejoras está medido en la tercera ronda.

**Lo que funcionó**
- Los tests propuestos para aserciones fuertes fueron correctos (3 de 3 en la primera ronda) y dieron con la
  causa (sobreajuste de Daikon, acumulación de puntaje).
- Cuando no había nada que reportar (falsos positivos del caso 3 en ambas rondas, del caso 2 en la segunda), no
  inventó violaciones.
- En la segunda ronda encontró un caso borde real (desbordamiento en `Cell`) que no se había considerado.
- En el caso 1, las dos consultas independientes convergieron en la misma aserción refinada.
- Los mutantes eran, en su gran mayoría, cambios plausibles que sí alteran el comportamiento (14 de 15).

**Lo que falló o requiere cuidado**
- **Falsa alarma por alcance, repetida:** 8 de 15 mutantes cambian un método distinto del que describe la aserción
  (caso 2 en las dos rondas, caso 3 en la segunda). Sin verificar, un usuario podría concluir erróneamente que la
  aserción está subespecificada.
- **Afirmaciones falsas dichas con certeza:** un mutante equivalente presentado como cambio de comportamiento
  (`score = 10`); una entrada inválida (`Board(1,"5")`) usada como testigo.
- **Confusión de constructores:** dos testigos no muestran la diferencia que dicen mostrar (caso 3, 2.ª ronda).
  En total, 4 de 15 testigos de mutantes están mal (1 en la primera ronda y 3 en la segunda).
- **Rótulos discutibles:** el desbordamiento de `Cell` se etiqueta "aserción demasiado fuerte" cuando es más bien
  un tema de comportamiento excepcional o de programa.
- **Sugerencias que no corresponden:** propone "aserciones más fuertes" aun cuando no encontró debilidad (caso 1)
  o sobre otros métodos (casos 2 y 3).
- **Estilo de test inconsistente:** a veces el test pasa cuando la aserción se viola (`assertFalse`), a veces falla.
- Sin ejecución no hay garantía: todo esto se supo porque se verificó a mano.

**Mejoras aplicadas a los prompts (`oasis/prompts.py`)**, a partir de lo observado:
1. Los mutantes deben cambiar **solo el método** del que habla la aserción (evidencia: 8 de 15 mutantes fuera de alcance).
2. Las entradas deben respetar los invariantes, indicar el constructor o método exacto y ejercitar la línea mutada
   (evidencia: testigos inválidos o que no muestran la diferencia, 4 de 15).
3. Los tests de violación deben **fallar** cuando la aserción se viola, sin invertirla con `assertFalse` (estilo único).
4. Los mutantes no deben ser equivalentes: hay que comprobar que el resultado cambia (evidencia: `score = 10`).
5. Si el test falla porque el método lanza una excepción en lugar de retornar, hay que decirlo (una postcondición
   describe solo los retornos normales; evidencia: el rótulo del desbordamiento de `Cell`).
6. Solo se sugiere una aserción nueva si se encontró algo (evidencia: sugerencias sin hallazgo en los casos 1, 2 y 3).

Un test automático (`test_prompts_contienen_las_reglas_de_calidad`) comprueba que las reglas estén en los prompts.
Su efecto se midió en la tercera ronda (ver arriba), con las salvedades indicadas allí.

## Limitaciones

- Una corrida por caso y por ronda (tres rondas) y un solo modelo (`nemotron-3.5-super-vl:free`, no Ultra, por la caída
  del proveedor). Con otro modelo o corrida los hallazgos pueden variar.
- **La herramienta cambió entre rondas.** Para evitar respuestas vacías por agotamiento de tokens se subió el
  presupuesto y se agregó a los prompts "limita la búsqueda: si no encuentras ninguno, responde que no encontraste".
  Según las horas de modificación de los archivos, las corridas refinadas de los casos 1 y 3 usaron el prompt nuevo
  y la del caso 2 el anterior. La frase puede empujar al LLM a responder "no encontré"; por eso la conclusión
  "sin mutantes" del caso 1 se contrastó con mutantes propios. Para la tercera ronda se mejoraron los prompts a partir
  de las fallas de las dos primeras sobre estos mismos tres casos, así que la mejora no es una validación independiente.
- Solo tres contratos de dos clases; los contratos se tradujeron a mano de la sintaxis de Daikon.
- La validación de los refinamientos es empírica (entradas concretas), no una demostración de corrección.
- Los refinamientos son los que surgieron del feedback y se validaron; la decisión final de adoptarlos es del
  usuario, como establece OASIs. Las decisiones tomadas figuran en la sección siguiente.

## Decisiones tomadas

1. **Caso 1 (desbordamiento con `2^30`):** se **propone corregir el programa** (`Math.multiplyExact`), sin aplicarlo al
   proyecto original. Parche y tests en `docs/casos/propuestas/`.
2. **Caso 2:** la aserción final exige además que `getScore` no modifique el estado (`this.score == \old(this.score)`).
3. **Caso 3:** la aserción final usa `result instanceof Set` más el contenido exacto, sin fijar `HashSet`, `modificable`
   ni el orden de iteración.
4. **Herramienta:** se aplicaron las mejoras de prompt de la Evaluación y se midieron en la tercera ronda.
5. **Modelo:** se mantiene `nemotron-3.5-super-vl:free`; no se repiten las corridas con Nemotron 3 Ultra.

**Sin pendientes de la entrega.** Opcional: repetir las corridas con otro modelo o varias veces para medir la variabilidad.

## Cómo reproducir

```
# Corridas con el LLM (PowerShell, desde simple-OASIs)
$env:OPENROUTER_API_KEY="sk-or-..."
$env:OASIS_MODEL="nvidia/nemotron-3.5-super-vl:free"
.\docs\casos\correr_casos.ps1   # corre original y refinada; salta las salidas ya guardadas (borrar el archivo para repetir)

# Verificación de mutantes (sin LLM; necesita JDK y el proyecto de 2048)
python docs\casos\verificacion\mutar.py
```

Parche propuesto y su test: `docs/casos/propuestas/` (aplicar con `git apply --ignore-whitespace` sobre una copia del proyecto).

Tests del LLM verificados: `docs/casos/verificacion/tests_del_llm/` (rondas 1 y 2) y `.../prompt_v2/` (ronda 3) (se pegan en `src/test/java/ar/edu/unrc/game2048/`
de una copia del proyecto y se corren con `mvn -o test`).
