import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("1. Importing core.events...")
try:
    import core.events
    print("   Success")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

print("2. Importing data.database...")
try:
    import data.database
    print("   Success")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

print("3. Importing data.repository...")
try:
    import data.repository
    print("   Success")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

print("4. Importing services.event_bus...")
try:
    import services.event_bus
    print("   Success")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

print("5. Importing services.alert_manager...")
try:
    import services.alert_manager
    print("   Success")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

print("6. Importing services.trade_manager...")
try:
    import services.trade_manager
    print("   Success")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

print("\n🎉 ALL IMPORTS SUCCESSFUL")
