

class CDS:
    def __init__(self,
                 buyer,
                 seller,
                 reference_entity,
                 prob_default,
                 notional_amount,
                 tenor,
                 risk_free_rate):
        self.buyer = buyer
        self.seller = seller
        self.reference_entity = reference_entity
        self.prob_default = prob_default
        self.notional_amount = notional_amount
        self.tenor = tenor
        self.risk_free_rate = risk_free_rate
        self.spread = None

