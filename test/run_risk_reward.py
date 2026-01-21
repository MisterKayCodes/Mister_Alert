from core.calculators.risk_reward import calculate_risk_reward

def main():
    print("="*30)
    print(" RISK/REWARD CALCULATOR ")
    print("="*30)
    
    try:
        pair = input("Enter Asset (e.g., BTCUSDT, EURUSD, XAUUSD): ").strip().upper()
        position = input("Position Type (LONG/SHORT): ").strip().upper()
        entry = float(input("Entry Price: "))
        stop_loss = float(input("Stop Loss Price: "))
        take_profit = float(input("Take Profit Price: "))
        
        result = calculate_risk_reward(pair, position, entry, stop_loss, take_profit)
        
        print("\n" + "-"*30)
        print(f"POSITION:   {result['position']}")
        print(f"RISK:       {result['risk_pips']} pips")
        print(f"REWARD:     {result['reward_pips']} pips")
        print(f"R:R RATIO:  {result['risk_reward_ratio']}")
        print("-"*30)
        
    except ValueError as e:
        print(f"\n[Error] {e}")

if __name__ == "__main__":
    main()
