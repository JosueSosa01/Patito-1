from scanner import build_lexer
from parser import build_parser
from semantico import QuadGenerator, SemanticError
from vm import VirtualMachine

def parse_text(src: str):
    lexer = build_lexer()
    parser = build_parser()
    return parser.parse(src, lexer=lexer)

if __name__ == "__main__":
    import sys
    run_flag = False
    args = sys.argv[1:]
    if "--run" in args:
        run_flag = True
        args.remove("--run")
    src = open(args[0], encoding="utf-8").read() if args else sys.stdin.read()
    ast = parse_text(src)
    print("AST")
    print(ast)
    try:
        gen = QuadGenerator()
        quads = gen.analyze(ast)
        print("\nDirecciones virtuales (globales):")
        for name, info in gen.global_vars.by_name.items():
            print(f"  {name} [{info.vtype}] -> {info.addr}")
        print("\nFunciones:")
        for f in gen.funcs.all():
            params = ", ".join([f"{p.name}:{p.vtype}" for p in f.params]) if f.params else "-"
            print(f"  {f.name}({params}) -> {f.ret_type or 'void'} inicio={f.start_quad} ret={f.ret_addr}")
        print("\nConstantes:")
        for (val, t), addr in sorted(gen.memory.const_table.items(), key=lambda kv: kv[1]):
            print(f"  {repr(val)} [{t}] -> {addr}")
        print("\nCuadruplos")
        for i, q in enumerate(quads):
            print(i, ":", q)
        if run_flag:
            print("\nEjecución")
            vm = VirtualMachine(quads, gen.funcs, gen.memory.const_table)
            vm.run()
    except SemanticError as e:
        print("Error semantico:", e)
        raise SystemExit(1)
