

class CDS:
    """
    | CDS class represents a Credit Default Swap.
    """
    def __init__(self,
                 buyer: str,
                 seller: str,
                 reference_entity: str,
                 default_probability: float,
                 notional_amount: float,
                 spread: float,
                 tenor: float=1,
                 risk_free_rate: float=0):
        """
        | Constructor method that initializes the CDS object with the specific parameters.

        :param buyer: The buyer of the CDS.
        :param seller: The seller of the CDS.
        :param reference_entity: The reference entity for the CDS.
        :param default_probability: The default probability of the reference entity.
        :param notional_amount: The notional amount of the CDS.
        :param spread: The spread of the CDS.
        :param tenor: The tenor of the CDS. Default is 1.
        :param risk_free_rate: The risk-free rate. Default is 0.
        """
        self.buyer = buyer
        self.seller = seller
        self.reference_entity = reference_entity
        self.default_probability = default_probability
        self.notional_amount = notional_amount
        self.spread = spread
        self.tenor = tenor
        self.risk_free_rate = risk_free_rate

    def update_spread(self, spread):
        """
        | Update the spread of the CDS.

        :param spread: The new spread value.
        """
        self.spread = spread
