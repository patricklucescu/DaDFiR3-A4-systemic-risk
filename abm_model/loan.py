

class Loan:
    """
    | Loan class which describes a loan contract between a borrower and a lender.
    """
    def __init__(self,
                 lender,
                 borrower,
                 notional_amount,
                 financial_fragility_borrower,
                 prob_default_borrower=None,
                 interest_rate=None):
        """
        | Set up the characteristics of a loan.

        :param lender: The lender of the loan.
        :param borrower: The borrower of the loan.
        :param notional_amount: The notional amount of the loan.
        :param financial_fragility_borrower: The financial fragility of the borrower.
        :param prob_default_borrower: The default probability of the borrower.
        :param interest_rate: The loan interest rate that the borrower has to pay.
        """
        self.lender = lender
        self.borrower = borrower
        self.notional_amount = notional_amount
        self.interest_rate = interest_rate
        self.financial_fragility_borrower = financial_fragility_borrower
        self.prob_default_borrower = prob_default_borrower

    def update_amount(self, new_value):
        """
        | Updates the notional amount of the loan.

        :param new_value: New notional amount.
        """
        self.notional_amount = new_value

    def update_interest_rate(self, new_value):
        """
        | Updates the loan interest rate.

        :param new_value: Loan interest rate.
        """
        self.interest_rate = new_value
