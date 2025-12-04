from dataclasses import dataclass, field
from typing import Optional

from semantico import VirtualMemory, SemanticError


def _segment_map():
    ranges = []
    span = 1000
    for seg, types in VirtualMemory.BASES.items():
        for vtype, base in types.items():
            ranges.append((base, base + span, seg, vtype))
    return ranges


@dataclass
class Frame:
    func: str
    ret_ip: Optional[int] = None
    locals: dict = field(default_factory=dict)
    temps: dict = field(default_factory=dict)


class VirtualMachine:
    def __init__(self, cuadruplos, func_dir, const_table):
        self.cuadruplos = cuadruplos
        self.func_dir = func_dir
        self.const_mem = {addr: val for (val, _), addr in const_table.items()}
        self.global_mem = {}
        self.call_stack = []
        self.pending_frame: Optional[Frame] = None
        self.current_frame = Frame("global")
        self.ip = 0
        self._ranges = _segment_map()

    def run(self):
        while self.ip < len(self.cuadruplos):
            op, l, r, res = self.cuadruplos[self.ip]
            if op in {"+", "-", "*", "/"}:
                a, b = self._read(l), self._read(r)
                if op == "+": out = a + b
                elif op == "-": out = a - b
                elif op == "*": out = a * b
                else: out = a / b
                self._write(res, out)
            elif op in {"<", ">", "<=", ">=", "==", "!="}:
                a, b = self._read(l), self._read(r)
                if op == "<": out = a < b
                elif op == ">": out = a > b
                elif op == "<=": out = a <= b
                elif op == ">=": out = a >= b
                elif op == "==": out = a == b
                else: out = a != b
                self._write(res, out)
            elif op == "=":
                self._write(res, self._read(l))
            elif op == "PRINT":
                print(self._read(l))
            elif op == "GOTO":
                self.ip = res
                continue
            elif op == "GOTOF":
                cond = self._read(l)
                if not cond:
                    self.ip = res
                    continue
            elif op == "ERA":
                fname = l
                self.pending_frame = Frame(fname)
            elif op == "PARAM":
                if not self.pending_frame:
                    raise SemanticError("PARAM sin ERA")
                finfo = self.func_dir.get(self.pending_frame.func)
                if not finfo:
                    raise SemanticError(f"Función '{self.pending_frame.func}' no encontrada en VM")
                idx = res
                if idx >= len(finfo.params):
                    raise SemanticError(f"Índice de parámetro {idx} inválido para '{finfo.name}'")
                target_addr = finfo.params[idx].addr
                self._write_frame(self.pending_frame, target_addr, self._read(l))
            elif op == "GOSUB":
                fname = l
                finfo = self.func_dir.get(fname)
                if not finfo or finfo.start_quad is None:
                    raise SemanticError(f"Función '{fname}' sin punto de entrada")
                if not self.pending_frame:
                    raise SemanticError("GOSUB sin ERA")
                self.pending_frame.ret_ip = self.ip + 1
                self.call_stack.append(self.current_frame)
                self.current_frame = self.pending_frame
                self.pending_frame = None
                self.ip = finfo.start_quad
                continue
            elif op == "RET":
                if l is not None and res is not None:
                    self._write(res, self._read(l))
                self._return_from_function()
                continue
            elif op == "ENDFUNC":
                self._return_from_function()
                continue
            else:
                raise SemanticError(f"Operador de VM desconocido: {op}")
            self.ip += 1

    def _return_from_function(self):
        if not self.call_stack:
            self.ip = len(self.cuadruplos)
            return
        caller = self.call_stack.pop()
        ret_ip = self.current_frame.ret_ip
        self.current_frame = caller
        self.ip = ret_ip if ret_ip is not None else len(self.cuadruplos)

    def _resolve(self, addr):
        for start, end, seg, vtype in self._ranges:
            if start <= addr < end:
                return seg, vtype
        raise SemanticError(f"Dirección virtual fuera de rango: {addr}")

    def _target_mem(self, addr, frame=None):
        seg, _ = self._resolve(addr)
        frame = frame or self.current_frame
        if seg == "const":
            return self.const_mem
        if seg == "global":
            return self.global_mem
        if seg == "local":
            return frame.locals
        if seg == "temp":
            return frame.temps
        raise SemanticError(f"Segmento desconocido para dirección {addr}")

    def _read(self, addr):
        mem = self._target_mem(addr)
        if addr not in mem:
            raise SemanticError(f"Acceso a dirección sin valor {addr}")
        return mem[addr]

    def _write(self, addr, value):
        mem = self._target_mem(addr)
        mem[addr] = value

    def _write_frame(self, frame, addr, value):
        mem = self._target_mem(addr, frame=frame)
        mem[addr] = value
