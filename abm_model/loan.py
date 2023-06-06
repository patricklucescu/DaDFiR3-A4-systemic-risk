

class Loan:
    def __init__(self,
                 lender,
                 borrower,
                 notional_amount,
                 financial_fragility_borrower,
                 prob_default_borrower=None,
                 interest_rate=None):
        self.lender = lender
        self.borrower = borrower
        self.notional_amount = notional_amount
        self.interest_rate = interest_rate
        self.financial_fragility_borrower = financial_fragility_borrower
        self.prob_default_borrower = prob_default_borrower

    def update_amount(self, new_value):
        self.notional_amount = new_value

    def update_interest_rate(self, new_value):
        self.interest_rate = new_value

