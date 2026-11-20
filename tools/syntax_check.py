#!/usr/bin/env python3
"""Parses source files with tree-sitter and reports syntax errors (a check where the client can't be built here)."""
import sys
from tree_sitter import Language, Parser
import tree_sitter_java, tree_sitter_cpp, tree_sitter_swift
LANGS = {'.java': tree_sitter_java.language(), '.cpp': tree_sitter_cpp.language(), '.h': tree_sitter_cpp.language(), '.swift': tree_sitter_swift.language()}
bad = 0
for path in sys.argv[1:]:
    ext = path[path.rfind('.'):]
    parser = Parser(Language(LANGS[ext]))
    src = open(path, 'rb').read()
    tree = parser.parse(src)
    errors = []
    def walk(n):
        if n.type == 'ERROR' or n.is_missing:
            errors.append(n)
            return
        for c in n.children: walk(c)
    walk(tree.root_node)
    print(f'{"OK " if not errors else "ERR"} {path} {len(errors)}')
    for e in errors[:5]:
        line = e.start_point[0] + 1
        print('   line', line, src.splitlines()[line - 1][:140].decode(errors='replace'))
    bad += bool(errors)
sys.exit(1 if bad else 0)
