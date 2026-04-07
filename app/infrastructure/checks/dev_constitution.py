import os
import sys
import ast
import re
import argparse
from typing import List

# --- CONFIGURATION ---
MAX_LINES = 300
MAX_NESTING = 4
SECRET_PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',  # OpenAI Keys
    r'[0-9]{8,10}:[a-zA-Z0-9_-]{35}', # Telegram Bot Tokens
]

# Rule 3: Forbidden Layer Mixing
FORBIDDEN_MIX = [
    {"set": {"aiogram", "sqlalchemy"}, "msg": "Rule 3 Violation: Mixing 'Mouth' (aiogram) and 'Memory' (sqlalchemy) in one file."},
]

class ConstitutionVisitor(ast.NodeVisitor):
    def __init__(self, file_path):
        self.file_path = file_path
        self.errors = []
        self.current_depth = 0
        self.max_depth = 0
        self.imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        # Rule 12: No Silent Crashes
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.errors.append(f"Rule 12 Violation: Empty 'except' block (Silent Crash) at line {node.lineno}.")
        self.generic_visit(node)

    def generic_visit(self, node):
        # Rule 8: Boring Code (Nesting Depth)
        control_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try)
        is_control = isinstance(node, control_nodes)
        
        if is_control:
            self.current_depth += 1
            if self.current_depth > self.max_depth:
                self.max_depth = self.current_depth
        
        super().generic_visit(node)
        
        if is_control:
            self.current_depth -= 1

def check_file(file_path):
    errors = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.splitlines()

    # Rule 3: Single Responsibility (Mega-Files)
    if len(lines) > MAX_LINES:
        errors.append(f"Rule 3 Violation: Mega-file detected ({len(lines)} lines > {MAX_LINES}).")

    # Rule 14: Security (Secret Scanning)
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, content):
            errors.append("Rule 14 Violation: Potential Hardcoded Secret (API Key/Token) detected!")

    # AST Based Checks
    try:
        tree = ast.parse(content)
        visitor = ConstitutionVisitor(file_path)
        visitor.visit(tree)
        errors.extend(visitor.errors)

        # Rule 8: Nesting
        if visitor.max_depth > MAX_NESTING:
            errors.append(f"Rule 8 Violation: Deep nesting detected (Depth {visitor.max_depth} > {MAX_NESTING}). Refactor for 'Boring Code'.")

        # Rule 3: Layer Mixing
        for mix in FORBIDDEN_MIX:
            if mix["set"].issubset(visitor.imports):
                errors.append(mix["msg"])

    except SyntaxError as e:
        errors.append(f"Syntax Error while parsing: {e}")

    return errors

def check_dependencies(base_dir):
    req_path = os.path.join(base_dir, "requirements.txt")
    if not os.path.exists(req_path):
        return []
    
    errors = []
    with open(req_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Rule 13: Pinned Dependencies
                if "==" not in line and ">=" not in line:
                    errors.append(f"Rule 13 Violation: Unpinned dependency detected: '{line}'.")
    return errors

def main():
    parser = argparse.ArgumentParser(description="Mister Assistant Digital Constitution Enforcer")
    parser.add_argument("--dir", default=".", help="Directory to scan")
    parser.add_argument("--exclude", nargs='*', default=["venv", ".git", "__pycache__", "Mister_Starter_Pack", "infrastructure"], help="Dirs to exclude")
    args = parser.parse_args()

    total_errors = 0
    print(f"--- Running Digital Constitution Scan on: {os.path.abspath(args.dir)} ---\n")

    # 1. Dependency Check
    dep_errors = check_dependencies(args.dir)
    if dep_errors:
        print(f"File: requirements.txt")
        for err in dep_errors:
            print(f"  [X] {err}")
        total_errors += len(dep_errors)

    # 2. Source Code Check
    for root, dirs, files in os.walk(args.dir):
        # Filter exclusions
        dirs[:] = [d for d in dirs if d not in args.exclude]
        
        for file in files:
            if file.endswith(".py") and file != "dev_constitution.py" and file != "test_constitution.py":
                file_path = os.path.join(root, file)
                file_errors = check_file(file_path)
                if file_errors:
                    rel_path = os.path.relpath(file_path, args.dir)
                    print(f"File: {rel_path}")
                    for err in file_errors:
                        print(f"  [X] {err}")
                    total_errors += len(file_errors)
                    print()

    if total_errors == 0:
        print("CONSTITUTION PASSED: Your code is Senior-grade.")
        sys.exit(0)
    else:
        print(f"CONSTITUTION FAILED: {total_errors} violation(s) found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
