
import sys
import os

try:
    import pydantic
    print(f"Pydantic version: {pydantic.__version__}")
except ImportError as e:
    print(f"Pydantic ImportError: {e}")

try:
    from pydantic_settings import BaseSettings
    print("pydantic_settings imported successfully")
except ImportError as e:
    print(f"pydantic-settings ImportError: {e}")

try:
    import config
    print("Config imported successfully")
    from config import settings
    print(f"Settings database_url: {settings.database_url}")
except Exception as e:
    print(f"Config Import Error: {e}")
    import traceback
    traceback.print_exc()
