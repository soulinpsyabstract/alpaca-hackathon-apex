def calculate_position_size(account_balance, entry_price, stop_price, risk_percent=0.02):
    risk_amount = account_balance * risk_percent
    risk_per_share = abs(entry_price - stop_price)
    shares = int(risk_amount / risk_per_share)
    take_profit = entry_price + (risk_per_share * 3)
    return {"shares": shares, "entry": entry_price, "stop": stop_price, "take_profit": take_profit, "risk_amount": risk_amount, "potential_profit": risk_amount * 3}

if __name__ == "__main__":
    result = calculate_position_size(account_balance=10000, entry_price=420, stop_price=418, risk_percent=0.02)
    print(result)
