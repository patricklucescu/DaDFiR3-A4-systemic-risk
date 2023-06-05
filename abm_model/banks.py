from abm_model.loan import Loan
from abm_model.baseclass import BaseAgent
import numpy as np


class BaseBank(BaseAgent):
    deposit_systemic_shock = None
    h_theta = None

    @classmethod
    def change_value_deposit_systemic(cls, new_value):
        cls.deposit_systemic_shock = new_value

    @classmethod
    def change_h_theta(cls, new_value):
        cls.h_theta = new_value


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
        self.max_credit = None
        self.assets = {'loans': [], 'cds': []}
        self.liabilities = {'loans': [], 'cds': []}

    def update_max_credit(self):
        self.max_credit = self.deposits / self.capital_requirement

    def asses_loan_requests(self, loans: list[Loan]):
        loan_offers = []
        for loan in loans:
            if loan.notional_amount > self.max_credit:
                continue
            if loan.borrower in self.firm_ids:
                loan.update_interest_rate(self.policy_rate * (1 + np.random.uniform(0, self.h_theta) *
                                                              np.tanh((1 + np.random.uniform(0.9, 1.1) *
                                                                       loan.prob_default_borrower) *
                                                                      loan.financial_fragility_borrower)))
                loan_offers.append(loan)
            else:  # we have an interbank loan
                loan.update_interest_rate(self.policy_rate * (1 + np.random.uniform(0, self.h_theta) *
                                                              np.tanh((1 + np.random.uniform(0.9, 1.1) *
                                                                       loan.prob_default_borrower) *
                                                                      loan.financial_fragility_borrower)))
        return loan_offers

    def check_loan(self, loan):
        if (loan.notional_amount + sum([x.notional_amount for x in self.assets['loans']]) +
                sum([x.spread * x.notional_amount for x in self.assets['cds']]) > self.max_credit):
            return False
        return True

