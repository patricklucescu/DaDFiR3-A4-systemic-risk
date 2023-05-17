import numpy
import random
from abm_model.essentials import *


class Bank:
    def __init__(self,
                 idx,
                 equity,
                 capital_req,
                 policy_rate,
                 firm_ids,
                 bank_ids,
                 h_theta,
                 bank_loans=[],
                 firm_loans=[],
                 max_interbank=3
                 ):
        self.idx = idx
        self.firm_ids = firm_ids
        self.bank_ids = bank_ids
        self.equity = equity
        self.capital_req = capital_req
        self.policy_rate = policy_rate
        self.bank_loans = bank_loans
        self.firm_loans = firm_loans
        self.h_theta = h_theta
        self.max_credit = None
        self.max_interbank = max_interbank

    def update_firm_ids(self, firm_ids):
        self.firm_ids = firm_ids

    def update_bank_ids(self, bank_ids):
        self.bank_ids = bank_ids

    def update_max_credit(self):
        self.max_credit = self.equity / self.capital_req

    def asses_loan_requests(self, loans, firms):
        loan_offers = []
        for loan in loans:
            if loan[1] > self.max_credit:  # if loan request is bigger than max credit then we reject the loan
                continue
            provided_ir = self.policy_rate * (1 + np.random.uniform(0, self.h_theta)
                                              * firms[loan[0]].financial_fragility)
            loan_offers += [{loan[0]: (self.idx, provided_ir, loan[1])}]
        return loan_offers

    def select_interbank_lenders(self):
        return
    def asses_bank_loan_request(self, loan, bank):
        if loan > self.max_credit:
            return
        interest_rate = self.policy_rate * (1 + 1)
