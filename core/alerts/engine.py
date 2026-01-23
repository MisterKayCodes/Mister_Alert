class AlertEngine:
    def evaluate(
        self,
        *,
        now: datetime,
        symbol: str,
        price: Decimal,
        alerts: list[PriceAlert],
    ) -> list[Event]:
        ...
