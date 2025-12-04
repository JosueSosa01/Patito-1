from scanner import build_lexer
from parser import build_parser

def parse_text(src: str):
    lexer = build_lexer()
    parser = build_parser()
    return parser.parse(src, lexer=lexer)

if __name__ == "__main__":
    import sys, io
    src = open(sys.argv[1],encoding="utf-8").read() if len(sys.argv)>1 else sys.stdin.read()
    ast = parse_text(src)
    print("AST")
    print(ast)
