import sys
import os
import traceback

print(f"PYTHONPATH: {sys.path[0]}")

try:
    print("Attempting to import alert_config...")
    import alert_config
    print(f"Successfully imported alert_config from {alert_config.__file__}")
except ImportError as e:
    print(f"FAILED to import alert_config: {e}")
    traceback.print_exc()

try:
    print("\nAttempting to import data.database...")
    from data import database
    print(f"Successfully imported data.database from {database.__file__}")
except ImportError as e:
    print(f"FAILED to import data.database: {e}")
    traceback.print_exc()
