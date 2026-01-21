# test/run_position_size.py

from core.calculators.position_size import get_position_size

def main():
    print("="*30)
    print(" RISK-BASED POSITION SIZE CALCULATOR ")
    print("="*30)

    try:
        pair = input("Enter Asset Pair (e.g., BTCUSDT, EURUSD, XAUUSD): ").strip().upper()
        entry = float(input("Enter Entry Price: "))
        stop_loss = float(input("Enter Stop Loss Price: "))
        risk_usd = float(input("Enter Amount to Risk (USD): "))

        result = get_position_size(pair, entry, stop_loss, risk_usd)

        print("\n" + "-"*30)
        print(f"PAIR:         {pair}")
        print(f"PIPS AT RISK: {result['pips']}")
        print(f"LOT SIZE:     {result['lots']}")
        print("-"*30)

    except ValueError:
        print("\n[Error] Please enter valid numbers for prices and risk amount.")

if __name__ == "__main__":
    main()
