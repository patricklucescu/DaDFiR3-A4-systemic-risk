

class CDS:
    def __init__(self,
                 buyer,
                 seller,
                 reference_entity,
                 default_probability,
                 notional_amount,
                 tenor,
                 risk_free_rate):
        self.buyer = buyer
        self.seller = seller
        self.reference_entity = reference_entity
        self.default_probability = default_probability
        self.notional_amount = notional_amount
        self.tenor = tenor
        self.risk_free_rate = risk_free_rate
        self.spread = None

    def update_spread(self, spread):
        self.spread = spread
