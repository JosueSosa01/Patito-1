from scanner import build_lexer
from parser import build_parser
from semantico import SemanticAnalyzerMin, SemanticError

def parse_text(src: str):
    lexer = build_lexer()
    parser = build_parser()
    return parser.parse(src, lexer=lexer)

if __name__ == "__main__":
    import sys
    src = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv)>1 else sys.stdin.read()
    ast = parse_text(src)
    print("AST")
    print(ast)
    print("\nSemantico (mínimo)")
    try:
        SemanticAnalyzerMin().analyze(ast)
        print("OK")
    except SemanticError as e:
        print("Error semántico:", e)
        raise SystemExit(1)
#correr con python run_semantico.py ejemplos/hola.pato

