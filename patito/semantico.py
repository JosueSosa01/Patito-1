from dataclasses import dataclass, field

ENTERO, FLOTANTE, STRING, BOOL, NULA = "entero", "flotante", "string", "bool", "nula"

class SemanticError(Exception):
    pass

@dataclass
class VarInfo:
    name: str
    vtype: str

@dataclass
class VarTable:
    by_name: dict = field(default_factory=dict)
    def declare(self, name, vtype):
        if name in self.by_name:
            raise SemanticError(f"Variable '{name}' doblemente declarada")
        self.by_name[name] = VarInfo(name, vtype)
    def lookup(self, name):
        return self.by_name.get(name)

ARIT = {"+","-","*","/"}
RELOP = {"<",">","<=",">=","==","!="}
SEMANTIC_CUBE = {}

def _allow(op, l, r, res):
    SEMANTIC_CUBE[(op,l,r)] = res

for op in ARIT:
    _allow(op, ENTERO,   ENTERO,   ENTERO)
    _allow(op, ENTERO,   FLOTANTE, FLOTANTE)
    _allow(op, FLOTANTE, ENTERO,   FLOTANTE)
    _allow(op, FLOTANTE, FLOTANTE, FLOTANTE)
for op in RELOP:
    _allow(op, ENTERO,   ENTERO,   BOOL)
    _allow(op, ENTERO,   FLOTANTE, BOOL)
    _allow(op, FLOTANTE, ENTERO,   BOOL)
    _allow(op, FLOTANTE, FLOTANTE, BOOL)
_allow("==", STRING, STRING, BOOL)
_allow("!=", STRING, STRING, BOOL)

def result_type(op, lt, rt):
    return SEMANTIC_CUBE.get((op, lt, rt))

class SemanticAnalyzerMin:
    def __init__(self):
        self.vars = VarTable()

    def analyze(self, ast):
        if not isinstance(ast, tuple) or ast[0] != 'programa':
            raise SemanticError("AST inesperado")
        _, name, vars_node, funcs_node, cuerpo_node = ast
        self._handle_vars(vars_node)
        self._handle_cuerpo(cuerpo_node)

    def _handle_vars(self, vars_node):
        if not vars_node: return
        tag, decls = vars_node
        for d in decls:
            _, id_list, tipo_node = d
            vtype = tipo_node[1]
            if vtype == NULA:
                raise SemanticError("Tipo 'nula' no es válido para variables")
            for name in id_list:
                self.vars.declare(name, vtype)

    def _handle_cuerpo(self, cuerpo_node):
        _, stats = cuerpo_node
        for st in stats:
            self._handle_stat(st)

    def _handle_stat(self, st):
        if not isinstance(st, tuple): 
            return
        tag = st[0]
        if tag == 'asigna':
            _, name, expr = st
            vinfo = self.vars.lookup(name)
            if not vinfo:
                raise SemanticError(f"Variable '{name}' no declarada")
            texpr = self._type_of(expr)
            if not self._assign_ok(vinfo.vtype, texpr):
                raise SemanticError(f"Tipos incompatibles: {vinfo.vtype} = {texpr}")
        elif tag == 'imprime':
            _, items = st
            for it in items:
                self._type_of(it) 
        elif tag == 'si':
            _, cond, cuerpo, sino = st
            t = self._type_of(cond)
            if t != BOOL:
                raise SemanticError(f"La condición de 'si' debe ser bool (no {t})")
            self._handle_cuerpo(cuerpo)
            if sino: self._handle_cuerpo(sino)
        elif tag == 'mientras':
            _, cond, cuerpo = st
            t = self._type_of(cond)
            if t != BOOL:
                raise SemanticError(f"La condición de 'mientras' debe ser bool (no {t})")
            self._handle_cuerpo(cuerpo)

    def _type_of(self, node):
        if isinstance(node, tuple):
            tag = node[0]
            if tag == 'cte':
                val = node[1]
                if isinstance(val, int): return ENTERO
                if isinstance(val, float): return FLOTANTE
                if isinstance(val, str): return STRING
            elif tag == 'id':
                name = node[1]
                vinfo = self.vars.lookup(name)
                if not vinfo:
                    raise SemanticError(f"Variable '{name}' no declarada")
                return vinfo.vtype
            elif tag == 'bin':
                _, op, l, r = node
                lt, rt = self._type_of(l), self._type_of(r)
                res = result_type(op, lt, rt)
                if not res:
                    raise SemanticError(f"Operación inválida: {lt} {op} {rt}")
                return res
            elif tag == 'rel':
                _, op, l, r = node
                lt, rt = self._type_of(l), self._type_of(r)
                res = result_type(op, lt, rt)
                if not res:
                    raise SemanticError(f"Operación inválida: {lt} {op} {rt}")
                return res
            elif tag == 'un':
                _, op, arg = node
                t = self._type_of(arg)
                if t not in (ENTERO, FLOTANTE):
                    raise SemanticError(f"Operador unario '{op}' no aplica a {t}")
                return t
        raise SemanticError("Expresión inválida")

    def _assign_ok(self, ltype, rtype):
        if ltype == rtype: 
            return True
        if ltype == FLOTANTE and rtype == ENTERO:
            return True
        return False
