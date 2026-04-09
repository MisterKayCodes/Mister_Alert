import os, sys, ast, argparse

DEFAULT_FORBIDDEN_IMPORTS = {
    "core": ["aiogram", "sqlalchemy", "bot", "data", "services"],
    "bot": ["sqlalchemy", "data.models"], 
    "data": ["aiogram", "services", "bot"],
    "services": ["aiogram", "bot", "sqlalchemy"]
}

INTERNAL_LAYERS = ["data", "services", "bot", "utils", "infrastructure"]

def check_file_integrity(file_path, folder_name, rules, max_lines=300):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) > max_lines: return [f"File too long ({len(lines)} > {max_lines})"]
        try: 
            content = "".join(lines)
            tree = ast.parse(content)
        except Exception as e: return [f"Syntax Error: {e}"]
    
    errors = []
    
    # 1. Check for absolute import enforcement (app. prefix)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = []
            if isinstance(node, ast.ImportFrom):
                if node.module: modules.append(node.module)
            else:
                modules.extend([n.name for n in node.names])
            
            for mod in modules:
                first_part = mod.split('.')[0]
                if first_part in INTERNAL_LAYERS:
                    errors.append(f"Incorrect relative import: '{mod}'. Use 'app.{mod}' instead.")

    # 2. Check for illegal layer-to-layer imports
    # Checks both 'layer' and 'app.layer' variants
    forbidden = rules.get(folder_name, [])
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.ImportFrom):
                if node.module: names.append(node.module)
            else:
                names.extend([n.name for n in node.names])
            
            for name in names:
                if name:
                    for f in forbidden:
                        if name == f or name.startswith(f + ".") or \
                           name == f"app.{f}" or name.startswith(f"app.{f}."):
                            errors.append(f"Illegal layer-to-layer import: {name}")
                            break

    # 3. Check for Deep Nesting (Cyclomatic Complexity)
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
    if visitor.max_depth >= 5:
        errors.append(f"Spaghetti Warning: Deep nesting detected (depth {visitor.max_depth}). Refactor to reduce cyclomatic complexity.")

    return errors

def scan_organism(base_dir=".", max_lines=300):
    has_issues = False
    app_path = os.path.join(base_dir, "app")
    if not os.path.exists(app_path):
        app_path = base_dir if os.path.basename(os.path.abspath(base_dir)) == "app" else None
        if not app_path: return True 

    for layer in DEFAULT_FORBIDDEN_IMPORTS.keys():
        path = os.path.join(app_path, layer)
        if not os.path.exists(path): continue
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    errs = check_file_integrity(os.path.join(root, file), layer, DEFAULT_FORBIDDEN_IMPORTS, max_lines)
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
