import ply.lex as lex

reserved = {
    'programa':'PROGRAM','vars':'VARS','inicio':'INICIO','fin':'FIN',
    'entero':'ENTERO','flotante':'FLOTANTE','nula':'NULA',
    'escribe':'ESCRIBE','imprime':'ESCRIBE','mientras':'MIENTRAS','haz':'HAZ','si':'SI','sino':'SINO',
    'func':'FUNC','finf':'FINF','ret':'RET','regresa':'RET','funcs':'FUNCS',
}

tokens = (
    'ID','CTE_ENT','CTE_FLOT','LETRERO',
    'IGUAL','MAS','MENOS','MULT','DIV',
    'LPAREN','RPAREN','LBRACE','RBRACE',
    'SEMICOLON','COMMA','COLON',
    'EQ','NEQ','LT','GT','LE','GE',
)
# Evita duplicados cuando hay alias en reserved (imprime/escribe, ret/regresa, funcs)
tokens = tokens + tuple(dict.fromkeys(reserved.values()))

t_IGUAL = r'='
t_MAS = r'\+'
t_MENOS = r'-'
t_MULT = r'\*'
t_DIV = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_SEMICOLON = r';'
t_COMMA = r','
t_COLON = r':'

def t_LE(t): r'<='; return t
def t_GE(t): r'>='; return t
def t_EQ(t): r'=='; return t
def t_NEQ(t): r'!='; return t
def t_LT(t): r'<'; return t
def t_GT(t): r'>'; return t

def t_LETRERO(t):
    r'"([^"\\]|\\.)*"'
    t.value = bytes(t.value[1:-1],'utf-8').decode('unicode_escape')
    return t

def t_CTE_FLOT(t):
    r'[+\-]?\d+\.\d+'
    t.value = float(t.value); return t

def t_CTE_ENT(t):
    r'[+\-]?\d+'
    t.value = int(t.value); return t

def t_ID(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value,'ID'); return t

t_ignore = ' \t'

def t_comment_line(t): r'//[^\n]*'; pass
def t_comment_block(t): r'/\*([^*]|\*+[^*/])*\*/'; pass

def t_newline(t): r'\n+'; t.lexer.lineno += len(t.value)

def t_error(t):
    raise SyntaxError(f"Caracter ilegal '{t.value[0]}' en línea {t.lexer.lineno}")

def build_lexer(**kw): return lex.lex(**kw)
