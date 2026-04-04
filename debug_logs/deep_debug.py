import pydantic
import sys
print(f"Pydantic version: {pydantic.__version__}")
print(f"Pydantic file: {pydantic.__file__}")
try:
    from pydantic import BaseSettings
    print("✅ BaseSettings found in pydantic (Legacy V1 style)")
except ImportError:
    print("❌ BaseSettings NOT found in pydantic (V2 style)")

try:
    from pydantic_settings import BaseSettings
    print("✅ BaseSettings found in pydantic_settings (V2 style)")
except ImportError:
    print("❌ BaseSettings NOT found in pydantic_settings")

print("\n--- Search for 'BaseSettings' in loaded modules ---")
for name, module in sys.modules.items():
    if "pydantic" in name:
        if hasattr(module, "BaseSettings"):
            print(f"Found BaseSettings in: {name}")
