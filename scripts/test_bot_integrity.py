import os
import sys
import re
import ast
from loguru import logger

def _get_val(node):
    """Deepest nesting level 1."""
    if isinstance(node, ast.Constant):
        return node.value
    return None

def _is_data_attr(node):
    """Deepest nesting level 1."""
    return isinstance(node, ast.Attribute) and node.attr == 'data'

def _check_eq(arg):
    """Deepest nesting level 2."""
    if not isinstance(arg, ast.Compare):
        return None
    if _is_data_attr(arg.left):
        return _get_val(arg.comparators[0])
    return None

def _check_start(arg):
    """Deepest nesting level 2."""
    if not isinstance(arg, ast.Call):
        return None
    func = arg.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr == 'startswith' and _is_data_attr(func.value):
        return _get_val(arg.args[0])
    return None

def _extract_handler(node):
    """Deepest nesting level 3."""
    if not isinstance(node, ast.AsyncFunctionDef):
        return None
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        if getattr(dec.func, 'attr', '') != 'callback_query':
            continue
        for arg in dec.args:
            res = _check_eq(arg) or _check_start(arg)
            if res:
                return res
    return None

def _extract_button(node):
    """Deepest nesting level 3."""
    if not isinstance(node, ast.Call):
        return None
    name = getattr(node.func, 'attr', '') or getattr(node.func, 'id', '')
    if name != 'InlineKeyboardButton':
        return None
    for kw in node.keywords:
        if kw.arg != 'callback_data':
            continue
        if isinstance(kw.value, ast.Constant):
            return kw.value.value
        if isinstance(kw.value, ast.JoinedStr):
            for v in kw.value.values:
                res = _get_val(v)
                if res: return res
    return None

def get_integrity_data(file_path):
    """Scans a file for both registered handlers and defined buttons."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    h_set, b_set = set(), set()
    for node in ast.walk(tree):
        h = _extract_handler(node)
        if h: h_set.add(h)
        b = _extract_button(node)
        if b: b_set.add(b)
    return h_set, b_set

def run_check():
    logger.info("🛡️ Running Static Integrity Check (AST)...")
    base = "app/bot/routers/marketing"
    files = [os.path.join(base, f) for f in os.listdir(base) if f.endswith(".py")]
    h_all, b_all = set(), set()
    for f in files:
        h, b = get_integrity_data(f)
        h_all.update(h)
        b_all.update(b)
    
    fails = 0
    for btn in b_all:
        is_h = btn in h_all or any(btn.startswith(x) for x in h_all)
        if not is_h:
            logger.error(f"❌ ORPHANED: '{btn}'")
            fails += 1
    if fails == 0:
        logger.success(f"✓ Integrity verified ({len(b_all)} buttons).")
        return True
    return False

if __name__ == "__main__":
    if not run_check():
        sys.exit(1)
