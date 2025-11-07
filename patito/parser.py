import ply.yacc as yacc
from scanner import tokens, build_lexer

precedence = (
    ('left','EQ','NEQ','LT','GT','LE','GE'),
    ('left','MAS','MENOS'),
    ('left','MULT','DIV'),
    ('right','UMINUS'),
)

def p_programa(p):
    'programa : PROGRAM ID SEMICOLON vars funcs INICIO cuerpo FIN'
    p[0] = ('programa', p[2], p[4], p[5], p[7])

def p_vars(p):
    '''vars : VARS COLON var_decls
            | empty'''
    p[0] = ('vars', p[3]) if len(p) == 4 else ('vars', [])

def p_var_decls(p):
    '''var_decls : var_decl var_decls
                 | var_decl'''
    p[0] = [p[1]] + (p[2] if len(p) == 3 else [])

def p_var_decl(p):
    'var_decl : id_list COLON tipo SEMICOLON'
    p[0] = ('decl', p[1], p[3])

def p_id_list(p):
    '''id_list : ID COMMA id_list
               | ID'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]

def p_tipo(p):
    '''tipo : ENTERO
            | FLOTANTE
            | NULA'''
    p[0] = ('tipo', p[1].lower())

def p_funcs(p):
    'funcs : empty'
    p[0] = ('funcs', [])

def p_cuerpo(p):
    'cuerpo : estatutos'
    p[0] = ('cuerpo', p[1])

def p_estatutos(p):
    '''estatutos : estatuto estatutos
                 | empty'''
    p[0] = [p[1]] + p[2] if len(p) == 3 else []

def p_estatuto(p):
    '''estatuto : asigna SEMICOLON
                | imprime SEMICOLON
                | condicion
                | ciclo
                | llamada SEMICOLON'''
    p[0] = p[1]

def p_asigna(p):
    'asigna : ID IGUAL expresion'
    p[0] = ('asigna', p[1], p[3])

def p_imprime(p):
    'imprime : ESCRIBE LPAREN imprime_args RPAREN'
    p[0] = ('imprime', p[3])

def p_imprime_args(p):
    '''imprime_args : imprime_item COMMA imprime_args
                    | imprime_item'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]

def p_imprime_item(p):
    '''imprime_item : expresion
                    | LETRERO'''
    p[0] = ('cte', p[1]) if isinstance(p[1], str) else p[1]

def p_condicion(p):
    'condicion : SI LPAREN expresion RPAREN cuerpo sino_opt'
    p[0] = ('si', p[3], p[5], p[6])

def p_sino_opt(p):
    '''sino_opt : SINO cuerpo
                | empty'''
    p[0] = p[2] if len(p) == 3 else None

def p_ciclo(p):
    'ciclo : MIENTRAS LPAREN expresion RPAREN HAZ cuerpo'
    p[0] = ('mientras', p[3], p[6])

def p_llamada(p):
    'llamada : ID LPAREN llama_args_opt RPAREN'
    p[0] = ('call', p[1], p[3])

def p_llama_args_opt(p):
    '''llama_args_opt : expr_list
                      | empty'''
    p[0] = p[1]

def p_expr_list(p):
    '''expr_list : expresion COMMA expr_list
                 | expresion'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]

def p_expresion(p):
    '''expresion : exp relop exp
                 | exp'''
    p[0] = ('rel', p[2], p[1], p[3]) if len(p) == 4 else p[1]

def p_relop(p):
    '''relop : EQ
             | NEQ
             | LT
             | GT
             | LE
             | GE'''
    p[0] = p[1]

def p_exp(p):
    '''exp : exp MAS termino
           | exp MENOS termino
           | termino'''
    p[0] = ('bin', p[2], p[1], p[3]) if len(p) == 4 else p[1]

def p_termino(p):
    '''termino : termino MULT factor
               | termino DIV factor
               | factor'''
    p[0] = ('bin', p[2], p[1], p[3]) if len(p) == 4 else p[1]

def p_factor_group(p):
    'factor : LPAREN expresion RPAREN'
    p[0] = p[2]

def p_factor_unary(p):
    '''factor : MAS factor
              | MENOS factor %prec UMINUS'''
    p[0] = ('un', p[1], p[2])

def p_factor_rest(p):
    '''factor : cte
              | ID
              | llamada'''
    if isinstance(p[1], tuple) and p[1][0] == 'cte':
        p[0] = p[1]
    elif isinstance(p[1], str):
        p[0] = ('id', p[1])
    else:
        p[0] = p[1]

def p_cte(p):
    '''cte : CTE_ENT
           | CTE_FLOT
           | LETRERO'''
    p[0] = ('cte', p[1])

def p_empty(p):
    'empty :'
    p[0] = []

def p_error(p):
    if p:
        raise SyntaxError(f"Error de sintaxis en '{p.value}' (token {p.type}) línea {p.lineno}")
    else:
        raise SyntaxError("Error de sintaxis al final del archivo (EOF)")

def build_parser():
    return yacc.yacc(start='programa', debug=False, write_tables=False)
