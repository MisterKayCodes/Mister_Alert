import os
import sys
import re
import ast
from loguru import logger

def get_integrity_data(file_path):
    """
    Scans a file for both registered handlers and defined buttons.
    Returns (handlers, buttons)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
        
    handlers = set()
    buttons = set()
    
    for node in ast.walk(tree):
        # 1. FIND HANDLERS: @router.callback_query(F.data == "...")
        if isinstance(node, ast.AsyncFunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    # Check for callback_query
                    if getattr(decorator.func, 'attr', '') == 'callback_query':
                        for arg in decorator.args:
                            # F.data == "..."
                            if isinstance(arg, ast.Compare):
                                if isinstance(arg.left, ast.Attribute) and arg.left.attr == 'data':
                                    if isinstance(arg.comparators[0], ast.Constant):
                                        handlers.add(arg.comparators[0].value)
                            # F.data.startswith("...")
                            elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
                                if arg.func.attr == 'startswith' and isinstance(arg.func.value, ast.Attribute):
                                    if arg.func.value.attr == 'data':
                                        if isinstance(arg.args[0], ast.Constant):
                                            handlers.add(arg.args[0].value)

        # 2. FIND BUTTONS: InlineKeyboardButton(..., callback_data="...")
        if isinstance(node, ast.Call):
            if getattr(node.func, 'attr', '') == 'InlineKeyboardButton' or \
               getattr(node.func, 'id', '') == 'InlineKeyboardButton':
                for kw in node.keywords:
                    if kw.arg == 'callback_data' and isinstance(kw.value, ast.Constant):
                        buttons.add(kw.value.value)
                    elif kw.arg == 'callback_data' and isinstance(kw.value, ast.JoinedStr):
                        # Handle f-strings prefix
                        for val in kw.value.values:
                            if isinstance(val, ast.Constant):
                                buttons.add(val.value)
                                break
                                
    return handlers, buttons

def run_check():
    logger.info("🛡️ Running Static Integrity Check (AST)...")
    file_path = "app/bot/routers/marketing/dashboard.py"
    
    if not os.path.exists(file_path):
        logger.error(f"File {file_path} not found!")
        return False
        
    handlers, buttons = get_integrity_data(file_path)
    
    failures = 0
    passed = 0
    
    logger.info(f"Detected Handlers: {len(handlers)}")
    logger.info(f"Detected Buttons: {len(buttons)}")
    
    for btn in buttons:
        # Check exact or prefix
        is_handled = btn in handlers or any(btn.startswith(h) for h in handlers)
        
        if is_handled:
            passed += 1
        else:
            logger.error(f"❌ ORPHANED BUTTON: '{btn}' has no handler in dashboard.py")
            failures += 1
            
    if failures == 0:
        logger.success(f"✓ Integrity verified. All {passed} buttons are handled.")
        return True
    else:
        logger.critical(f"Integrity check failed: {failures} orphaned buttons found.")
        return False

if __name__ == "__main__":
    if not run_check():
        sys.exit(1)
