import os, sys, ast, argparse

DEFAULT_FORBIDDEN_IMPORTS = {
    "core": ["aiogram", "sqlalchemy", "bot", "data", "services"],
    "bot": ["sqlalchemy", "data.models"], 
    "data": ["aiogram", "services", "bot"],
    "services": ["aiogram", "bot", "sqlalchemy"]
}

def check_file_integrity(file_path, folder_name, rules, max_lines=200):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) > max_lines: return [f"File too long ({len(lines)} > {max_lines})"]
        try: tree = ast.parse("".join(lines))
        except Exception as e: return [f"Syntax Error: {e}"]
    
    errors = []
    forbidden = rules.get(folder_name, [])
    
    # 1. Check for illegal imports
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    names.append(node.module)
            else:
                names.extend([n.name for n in node.names])
            
            for name in names:
                if name:
                    # Fix: Ensure it's the package itself or a sub-package (e.g. 'data' or 'data.models')
                    # and not just a name starting with it (e.g. 'dataclasses')
                    for f in forbidden:
                        if name == f or name.startswith(f + "."):
                            errors.append(f"Illegal import: {name}")
                            break

    # 2. Check for Deep Nesting (Cyclomatic Complexity)
    class NestingVisitor(ast.NodeVisitor):
        def __init__(self):
            self.max_depth = 0
            self.current_depth = 0
            self.control_flow_nodes = (ast.If, ast.For, ast.While, ast.Try, ast.With)

        def generic_visit(self, node):
            is_control_flow = isinstance(node, self.control_flow_nodes)
            if is_control_flow:
                self.current_depth += 1
                if self.current_depth > self.max_depth:
                    self.max_depth = self.current_depth
            
            super().generic_visit(node)
            
            if is_control_flow:
                self.current_depth -= 1

    visitor = NestingVisitor()
    visitor.visit(tree)
    if visitor.max_depth >= 4:
        errors.append(f"Spaghetti Warning: Deep nesting detected (depth {visitor.max_depth}). Refactor to reduce cyclomatic complexity.")

    return errors

def scan_organism(base_dir=".", max_lines=200):
    has_issues = False
    app_path = os.path.join(base_dir, "app")
    if not os.path.exists(app_path):
        # Fallback for when running from within the app folder or tests
        app_path = base_dir if os.path.basename(os.path.abspath(base_dir)) == "app" else None
        if not app_path: return True 

    for layer in DEFAULT_FORBIDDEN_IMPORTS.keys():
        path = os.path.join(app_path, layer)
        if not os.path.exists(path): continue
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    errs = check_file_integrity(os.path.join(root, file), layer, DEFAULT_FORBIDDEN_IMPORTS, max_lines)
                    # Also check for 'app.' prefixed versions of forbidden imports
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        file_content = f.read()
                        for forbidden in DEFAULT_FORBIDDEN_IMPORTS[layer]:
                            if f"from app.{forbidden}" in file_content or f"import app.{forbidden}" in file_content:
                                errs.append(f"Illegal import: app.{forbidden}")
                    
                    for e in errs: 
                        print(f"[!] {os.path.join(root, file)}: {e}")
                        has_issues = True
    return not has_issues

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Base directory to scan")
    args = parser.parse_args()
    
    if not scan_organism(args.dir):
        sys.exit(1)
    else:
        print("[OK] Architecture inspection passed.")
