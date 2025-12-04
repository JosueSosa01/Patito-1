from dataclasses import dataclass, field
from typing import Optional

ENTERO, FLOTANTE, STRING, BOOL, NULA = "entero", "flotante", "string", "bool", "nula"

class SemanticError(Exception):
    pass

@dataclass
class VarInfo:
    name: str
    vtype: str
    addr: int

@dataclass
class VarTable:
    by_name: dict = field(default_factory=dict)
    def declare(self, name, vtype, addr):
        if name in self.by_name:
            raise SemanticError(f"Variable '{name}' doblemente declarada")
        self.by_name[name] = VarInfo(name, vtype, addr)
    def lookup(self, name):
        return self.by_name.get(name)

def _zero_counts():
    return {ENTERO: 0, FLOTANTE: 0, STRING: 0, BOOL: 0}

@dataclass
class FuncInfo:
    name: str
    ret_type: Optional[str]
    param_types: list
    params: list = field(default_factory=list)
    vars: VarTable = field(default_factory=VarTable)
    start_quad: Optional[int] = None
    ret_addr: Optional[int] = None
    locals_count: dict = field(default_factory=_zero_counts)
    temps_count: dict = field(default_factory=_zero_counts)

class FuncDirectory:
    def __init__(self):
        self.funcs = {}
    def declare(self, name, ret_type, param_types):
        if name in self.funcs:
            raise SemanticError(f"Función '{name}' ya declarada")
        info = FuncInfo(name, ret_type, param_types)
        self.funcs[name] = info
        return info
    def get(self, name):
        return self.funcs.get(name)
    def all(self):
        return self.funcs.values()

class VirtualMemory:
    BASES = {
        'global': {ENTERO: 1000, FLOTANTE: 2000, STRING: 3000, BOOL: 4000},
        'temp':   {ENTERO: 5000, FLOTANTE: 6000, STRING: 7000, BOOL: 8000},
        'const':  {ENTERO: 9000, FLOTANTE: 10000, STRING: 11000, BOOL: 12000},
        'local':  {ENTERO: 13000, FLOTANTE: 14000, STRING: 15000, BOOL: 16000},
    }

    def __init__(self):
        self.counters = {seg: {t: 0 for t in types} for seg, types in self.BASES.items()}
        self.const_table = {}

    def _alloc(self, segment, vtype):
        if vtype not in self.BASES[segment]:
            raise SemanticError(f"Tipo '{vtype}' no soportado en memoria {segment}")
        idx = self.counters[segment][vtype]
        addr = self.BASES[segment][vtype] + idx
        self.counters[segment][vtype] += 1
        return addr

    def alloc_var(self, vtype, scope='global'):
        return self._alloc(scope, vtype)

    def alloc_temp(self, vtype):
        return self._alloc('temp', vtype)

    def reset_locals(self):
        for seg in ('local','temp'):
            for t in self.counters[seg]:
                self.counters[seg][t] = 0

    def usage(self, segment):
        return dict(self.counters[segment])

    def alloc_const(self, value, vtype):
        key = (value, vtype)
        if key in self.const_table:
            return self.const_table[key]
        addr = self._alloc('const', vtype)
        self.const_table[key] = addr
        return addr

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
        self.memory = VirtualMemory()
        self.vars = VarTable()

    def analyze(self, ast):
        if not isinstance(ast, tuple) or ast[0] != 'programa':
            raise SemanticError("AST inesperado")
        _, name, vars_node, funcs_node, cuerpo_node = ast
        self._handle_vars(vars_node)
        self._handle_funcs(funcs_node)
        self._handle_cuerpo(cuerpo_node)

    def _handle_funcs(self, funcs_node):
        # Analizador mínimo: hoy solo valida que la estructura exista.
        if not funcs_node:
            return
        _, fn_list = funcs_node
        for fn in fn_list:
            pass

    def _handle_vars(self, vars_node):
        if not vars_node: return
        tag, decls = vars_node
        for d in decls:
            _, id_list, tipo_node = d
            vtype = tipo_node[1]
            if vtype == NULA:
                raise SemanticError("Tipo 'nula' no es válido para variables")
            for name in id_list:
                addr = self.memory.alloc_var(vtype)
                self.vars.declare(name, vtype, addr)

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

class QuadGenerator(SemanticAnalyzerMin):
    def __init__(self):
        super().__init__()
        self.funcs = FuncDirectory()
        self.global_vars = VarTable()
        self.current_vars = self.global_vars
        self.current_func = None
        self.pilaO = []
        self.pilaTipos = []
        self.pilaOp = []
        self.cuadruplos = []
        self.temp_tally = {ENTERO: 0, FLOTANTE: 0, STRING: 0, BOOL: 0}
        self.main_temp_usage = _zero_counts()
        self._pending_gosubs = {}

    def new_temp(self, vtype):
        self.temp_tally[vtype] += 1
        return self.memory.alloc_temp(vtype)

    def analyze(self, ast):
        if not isinstance(ast, tuple) or ast[0] != 'programa':
            raise SemanticError("AST inesperado")
        _, name, vars_node, funcs_node, cuerpo_node = ast
        func_nodes = funcs_node[1] if funcs_node else []
        self._predeclare_funcs(func_nodes)
        # variables globales
        self._handle_vars(vars_node, scope='global', vtable=self.global_vars)
        # salto inicial a main
        self.cuadruplos.append(('GOTO', None, None, None))
        jump_main_idx = 0
        # generar funciones
        for fn in func_nodes:
            self._gen_func(fn)
        # generar main como cuerpo global
        self.memory.reset_locals()
        self.current_vars = self.global_vars
        self.current_func = None
        main_start = len(self.cuadruplos)
        self.cuadruplos[jump_main_idx] = ('GOTO', None, None, main_start)
        self._gen_cuerpo(cuerpo_node)
        self.main_temp_usage = self.memory.usage('temp')
        self._patch_pending_gosubs()
        return self.cuadruplos

    def _predeclare_funcs(self, func_nodes):
        for fn in func_nodes:
            _, name, params, tipo_ret, _, _ = fn
            ret_type = tipo_ret[1]
            ret_type = None if ret_type in (None, NULA) else ret_type
            param_types = [p[1][1] for p in params] if params else []
            self.funcs.declare(name, ret_type, param_types)

    def _patch_pending_gosubs(self):
        for fname, idxs in self._pending_gosubs.items():
            finfo = self.funcs.get(fname)
            if not finfo or finfo.start_quad is None:
                raise SemanticError(f"Función '{fname}' llamada pero no definida")
            for i in idxs:
                op, a, b, _ = self.cuadruplos[i]
                self.cuadruplos[i] = (op, a, b, finfo.start_quad)

    def _handle_vars(self, vars_node, scope='global', vtable=None):
        if not vars_node: 
            return
        vtable = vtable or self.current_vars
        tag, decls = vars_node
        for d in decls:
            _, id_list, tipo_node = d
            vtype = tipo_node[1]
            if vtype == NULA:
                raise SemanticError("Tipo 'nula' no es válido para variables")
            for name in id_list:
                addr = self.memory.alloc_var(vtype, scope=scope if scope else 'global')
                vtable.declare(name, vtype, addr)

    def _lookup_var(self, name):
        if self.current_vars and name in self.current_vars.by_name:
            return self.current_vars.lookup(name)
        return self.global_vars.lookup(name)

    def _gen_func(self, func_node):
        _, name, params, tipo_ret, vars_node, cuerpo_node = func_node
        finfo = self.funcs.get(name)
        if not finfo:
            raise SemanticError(f"Función '{name}' no declarada")
        self.memory.reset_locals()
        self.current_func = name
        self.current_vars = finfo.vars
        # return slot
        if finfo.ret_type:
            finfo.ret_addr = self.memory.alloc_var(finfo.ret_type, scope='global')
        # params
        if params:
            for (pname, ptipo), ptype in zip(params, finfo.param_types):
                vtype = ptipo[1]
                if vtype != ptype:
                    raise SemanticError(f"Tipo de parámetro '{pname}' no coincide con la firma")
                addr = self.memory.alloc_var(vtype, scope='local')
                vinfo = VarInfo(pname, vtype, addr)
                finfo.params.append(vinfo)
                finfo.vars.declare(pname, vtype, addr)
        # locals
        self._handle_vars(vars_node, scope='local', vtable=finfo.vars)
        finfo.start_quad = len(self.cuadruplos)
        self._gen_cuerpo(cuerpo_node)
        finfo.locals_count = self.memory.usage('local')
        finfo.temps_count = self.memory.usage('temp')
        self.cuadruplos.append(('ENDFUNC', None, None, None))
        self.current_func = None
        self.current_vars = self.global_vars

    def _reset_stacks(self):
        self.pilaO = []
        self.pilaTipos = []
        self.pilaOp = []

    def _gen_cuerpo(self, cuerpo_node):
        tag = cuerpo_node[0]
        if tag != 'cuerpo':
            raise SemanticError("Nodo de cuerpo inválido")
        stats = cuerpo_node[1]
        for st in stats:
            self._gen_stat(st)

    def _gen_stat(self, st):
        if not isinstance(st, tuple):
            return
        tag = st[0]
        if tag == 'asigna':
            _, name, expr = st
            vinfo = self._lookup_var(name)
            if not vinfo:
                raise SemanticError(f"Variable '{name}' no declarada")
            self._reset_stacks()
            res, t = self._gen_expr(expr)
            if not self._assign_ok(vinfo.vtype, t):
                raise SemanticError(f"Tipos incompatibles en asignación a '{name}'")
            self.cuadruplos.append(('=', res, None, vinfo.addr))
        elif tag == 'imprime':
            _, items = st
            for item in items:
                self._reset_stacks()
                res, t = self._gen_expr(item)
                self.cuadruplos.append(('PRINT', res, None, None))
        elif tag == 'call':
            self._emit_call(st, expect_value=False)
        elif tag == 'ret':
            self._emit_return(st)
        elif tag == 'si':
            _, cond, cuerpo, sino = st
            self._reset_stacks()
            cond_addr, cond_type = self._gen_expr(cond)
            if cond_type != BOOL:
                raise SemanticError("La condición de 'si' debe ser bool")
            self.cuadruplos.append(('GOTOF', cond_addr, None, None))
            gotof_idx = len(self.cuadruplos) - 1
            self._gen_cuerpo(cuerpo)
            if sino:
                self.cuadruplos.append(('GOTO', None, None, None))
                end_idx = len(self.cuadruplos) - 1
                self.cuadruplos[gotof_idx] = ('GOTOF', cond_addr, None, len(self.cuadruplos))
                self._gen_cuerpo(sino)
                self.cuadruplos[end_idx] = ('GOTO', None, None, len(self.cuadruplos))
            else:
                self.cuadruplos[gotof_idx] = ('GOTOF', cond_addr, None, len(self.cuadruplos))
        elif tag == 'mientras':
            _, cond, cuerpo = st
            loop_start = len(self.cuadruplos)
            self._reset_stacks()
            cond_addr, cond_type = self._gen_expr(cond)
            if cond_type != BOOL:
                raise SemanticError("La condición de 'mientras' debe ser bool")
            self.cuadruplos.append(('GOTOF', cond_addr, None, None))
            gotof_idx = len(self.cuadruplos) - 1
            self._gen_cuerpo(cuerpo)
            self.cuadruplos.append(('GOTO', None, None, loop_start))
            self.cuadruplos[gotof_idx] = ('GOTOF', cond_addr, None, len(self.cuadruplos))

    def _emit_return(self, st):
        if not self.current_func:
            raise SemanticError("RET solo es válido dentro de una función")
        finfo = self.funcs.get(self.current_func)
        _, expr = st
        if expr is None:
            if finfo.ret_type:
                raise SemanticError(f"La función '{finfo.name}' debe regresar {finfo.ret_type}")
            self.cuadruplos.append(('RET', None, None, None))
            return
        if not finfo.ret_type:
            raise SemanticError(f"La función '{finfo.name}' no debe regresar valor")
        self._reset_stacks()
        res, t = self._gen_expr(expr)
        if not self._assign_ok(finfo.ret_type, t):
            raise SemanticError(f"Tipo de retorno inválido: se esperaba {finfo.ret_type}, obtuvo {t}")
        self.cuadruplos.append(('RET', res, None, finfo.ret_addr))

    def _emit_call(self, st, expect_value=True):
        _, name, args = st
        finfo = self.funcs.get(name)
        if not finfo:
            raise SemanticError(f"Función '{name}' no declarada")
        args = args or []
        if len(args) != len(finfo.param_types):
            raise SemanticError(f"Función '{name}' espera {len(finfo.param_types)} params, recibió {len(args)}")
        self.cuadruplos.append(('ERA', name, None, None))
        for idx, (arg, expected_type) in enumerate(zip(args, finfo.param_types)):
            res, t = self._eval_arg(arg)
            if not self._assign_ok(expected_type, t):
                raise SemanticError(f"Tipo de argumento {idx} inválido en llamada a '{name}'")
            self.cuadruplos.append(('PARAM', res, None, idx))
        target_quad = finfo.start_quad
        if target_quad is None:
            # se parchea al final
            self._pending_gosubs.setdefault(name, []).append(len(self.cuadruplos))
        self.cuadruplos.append(('GOSUB', name, None, target_quad))
        if finfo.ret_type and expect_value:
            temp = self.new_temp(finfo.ret_type)
            self.cuadruplos.append(('=', finfo.ret_addr, None, temp))
            return temp, finfo.ret_type
        return None, None

    def _gen_expr(self, node):
        self._walk_expr(node)
        if not self.pilaO:
            raise SemanticError("Expresión vacía")
        res = self.pilaO.pop()
        t = self.pilaTipos.pop()
        self.pilaOp.clear()
        return res, t

    def _walk_expr(self, node):
        if not isinstance(node, tuple):
            raise SemanticError("Nodo de expresión inválido")
        tag = node[0]
        if tag == 'cte':
            val = node[1]
            if isinstance(val, int):
                t = ENTERO
            elif isinstance(val, float):
                t = FLOTANTE
            elif isinstance(val, bool):
                t = BOOL
            else:
                t = STRING
            addr = self.memory.alloc_const(val, t)
            self.pilaO.append(addr)
            self.pilaTipos.append(t)
        elif tag == 'id':
            name = node[1]
            vinfo = self._lookup_var(name)
            if not vinfo:
                raise SemanticError(f"Variable '{name}' no declarada")
            self.pilaO.append(vinfo.addr)
            self.pilaTipos.append(vinfo.vtype)
        elif tag == 'bin':
            _, op, left, right = node
            self._walk_expr(left)
            self._walk_expr(right)
            self._make_binary(op)
        elif tag == 'un':
            _, op, arg = node
            self._walk_expr(arg)
            self._make_unary(op)
        elif tag == 'rel':
            _, op, left, right = node
            self._walk_expr(left)
            self._walk_expr(right)
            self._make_binary(op)
        elif tag == 'call':
            temp, t = self._emit_call(node, expect_value=True)
            if temp is None or t is None:
                raise SemanticError(f"La función '{node[1]}' no regresa valor")
            self.pilaO.append(temp)
            self.pilaTipos.append(t)
        else:
            raise SemanticError("Tipo de nodo de expresión desconocido")

    def _make_binary(self, op):
        if len(self.pilaO) < 2:
            raise SemanticError("Faltan operandos para operación binaria")
        r = self.pilaO.pop()
        tr = self.pilaTipos.pop()
        l = self.pilaO.pop()
        tl = self.pilaTipos.pop()
        res_t = result_type(op, tl, tr)
        if not res_t:
            raise SemanticError(f"Operación '{op}' no válida para tipos {tl} y {tr}")
        temp = self.new_temp(res_t)
        self.cuadruplos.append((op, l, r, temp))
        self.pilaO.append(temp)
        self.pilaTipos.append(res_t)

    def _make_unary(self, op):
        if not self.pilaO:
            raise SemanticError("Falta operando para operación unaria")
        operand = self.pilaO.pop()
        t = self.pilaTipos.pop()
        if t not in (ENTERO, FLOTANTE):
            raise SemanticError(f"Operador unario '{op}' no aplica a {t}")
        temp = self.new_temp(t)
        self.cuadruplos.append((op, operand, None, temp))
        self.pilaO.append(temp)
        self.pilaTipos.append(t)

    def _eval_arg(self, expr):
        saved = (self.pilaO, self.pilaTipos, self.pilaOp)
        self.pilaO, self.pilaTipos, self.pilaOp = [], [], []
        res, t = self._gen_expr(expr)
        self.pilaO, self.pilaTipos, self.pilaOp = saved
        return res, t
