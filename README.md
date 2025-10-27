1. Archivos Clave del Proyecto
scanner.py
Escucha el código y lo convierte en "tokens" (palabras y símbolos atómicos) siendo esta la capa léxica.
parser.py
Toma los tokens y los agrupa según las reglas de la gramática. Verifica que la sintaxis sea correcta y construye el AST.
run.py
Es el que ejecutamos. Lee los archivos .pato que definamos, llama al escáner y al analizador, y nos muestra el resultado (el AST).


2. Lo que Sabe scanner.py 
El escáner tiene definidas todas las palabras y símbolos que reconoce:
2.1. Palabras Clave
Define las palabras reservadas de nuestro lenguaje:
programa, vars, inicio, fin, entero, flotante, nula, escribe, mientras, haz, si, sino.
2.2. Tokens Especiales
Reconoce cosas como:
Identificadores (ID).
Constantes (CTE_ENT, CTE_FLOT, LETRERO).
Operadores (MAS, MENOS, MULT, DIV, IGUAL, etc.).
Símbolos de Control (paréntesis, llaves, ;, ,, :).
Además, es lo suficientemente inteligente como para ignorar los comentarios (// y /* ... */) y los espacios en blanco.
3. Lo que entiende parser.py 
El analizador se asegura de que la estructura de nuestro código sea válida.
3.1. Prioridad en Operaciones
Sabe qué hacer primero en las expresiones matemáticas:
Signos unarios (cambio de signo, UMINUS).
Multiplicación y División (MULT, DIV).
Suma y Resta (MAS, MENOS).
Comparaciones (EQ, LT, GT, etc.).
3.2. Estructuras que Reconoce
Asegura que el código siga estas reglas:
Estructura Base: Todo debe ir entre programa...fin.
Variables: Tienen que declararse después de vars: con su tipo (entero, flotante, nula).
Estatutos: Maneja la Asignación (ID = expresion), la Impresión (escribe), y las llamadas a funciones.
Estructuras de Control:
Condicional: si (expresion) cuerpo sino cuerpo_opt.
Ciclo: mientras (expresion) haz cuerpo.
4. Ejemplos de Archivos de Prueba (.pato)
Usamos estos archivos para ver si nuestro Lexer y Parser funcionan bien.
hola.pato
Es un código válido que tiene de todo: declaraciones, asignaciones, aritmética, un si/sino y un ciclo mientras. 
hola1.pato (El que puede Fallar)
Tiene un error sintáctico sutil. Hay un punto y coma extra (;) justo después de la condición si (x > 20);. El parser podría marcar esto como error.
hola2.pato (El que Falla)
A este le falta un punto y coma.l escribe("mayor", y) dentro del bloque si no termina en punto y coma (;), lo que definitivamente causará un error de sintaxis.

LOs tres archivos de prueba son útiles para comprobar que realmente se este utilizando correctamente. Estos tres se corren con el comando: 
python run.py ejemplos/hola2.pato

Este es específicamente para correr el ejemplo número 3 llamado “hola2.pato”.
