from loan import Loan
from baseclass import BaseAgent
import numpy as np


class BaseBank(BaseAgent):
    deposit_systemic_shock = None
    h_theta = None
    max_interbank = None

    @classmethod
    def change_value_deposit_systemic(cls, new_value):
        cls.deposit_systemic_shock = new_value

    @classmethod
    def change_h_theta(cls, new_value):
        cls.h_theta = new_value

    @classmethod
    def change_max_interbank(cls, new_value):
        cls.max_interbank = new_value


class Bank(BaseBank):
    def __init__(self,
                 idx,
                 equity,
                 deposits,
                 capital_requirement,
                 ):
        super().__init__()
        self.idx = idx
        self.equity = equity
        self.deposits = deposits
        self.capital_requirement = capital_requirement
        self.firm_loans = []
        self.bank_loans = []
        self.sold_cds = []
        self.bought_cds = []
        self.max_credit = None

    def update_max_credit(self):
        self.max_credit = self.deposits / self.capital_requirement

    def asses_loan_request_firms(self, loans: list[Loan]):
        loan_offers = []
        for loan in loans:
            if loan.amount > self.max_credit:
                continue
            loan.update_interest_rate(self.policy_rate * (1 + np.random.uniform(0, self.h_theta) *
                                                          np.tanh((1 + np.random.uniform(0.9, 1.1) *
                                                                   loan.prob_default_borrower) *
                                                                  loan.financial_fragility_borrower)))

            loan_offers.append(loan)
        return loan_offers

    def asses_loan_request_banks(self, loan: Loan):
        return
