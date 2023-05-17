import numpy as np
import random
from abm_model.essentials import *


class Firm:

    def __init__(self,
                 idx,
                 market_price,
                 supply,
                 price,
                 wage,
                 min_wage,
                 equity_level,
                 productivity,
                 firm_ids,
                 bank_ids,
                 policy_rate,
                 loans: list = [],
                 num_firms: int = 100,
                 num_banks: int = 10,
                 max_banks_loan=3):

        if loans is None:
            loans = []
        self.idx = idx
        self.num_banks = num_banks
        self.num_firms = num_firms
        self.max_banks_loan = max_banks_loan
        self.market_price = market_price
        self.price = price
        self.supply = supply
        self.equity_level = equity_level
        self.wage = wage
        self.productivity = productivity
        self.labour = None
        self.min_wage = min_wage
        self.total_wage = self.wage * self.supply / self.productivity
        self.firm_ids = firm_ids
        self.bank_ids = bank_ids
        self.policy_rate = policy_rate
        # create list containing all the loans the firm has. Each loan should be of the form (idx, T, B, r), where
        # idx is the unique id of the bank, T is the expiry, B is the face value of the loan, r is the interest rate
        self.loans = loans
        self.total_wages = None
        self.credit_demand = None
        self.financial_fragility = None
        self.potential_lenders = None
        self.created_supply = None
        self.default_prob = None

    def update_min_wage(self, min_wage):
        self.min_wage = min_wage

    def update_market_price(self, market_price):
        self.market_price = market_price

    def update_firm_ids(self, firm_ids):
        self.firm_ids = firm_ids

    def update_bank_ids(self, bank_ids):
        self.bank_ids = bank_ids

    def compute_expected_supply_and_prices(self):
        """
        update the price and supply for the firm
        """
        self.wage = max([self.min_wage, self.wage * (1 + wages_adj()[0])])
        statement_1 = (self.supply > 0 and self.price >= self.market_price)
        statement_2 = (self.supply == 0 and self.price < self.market_price)
        statement_3 = (self.supply > 0 and self.price < self.market_price)
        statement_4 = (self.supply == 0 and self.price >= self.market_price)
        if statement_1 or statement_2:
            # supply remains constant
            self.total_wages = self.wage * self.supply / self.productivity
            min_price = (self.total_wages + sum([x[2] * x[3] for x in self.loans])) / self.supply
            if statement_1:
                self.price = np.max([min_price, self.price * (1 - price_adj()[0])])
            else:
                self.price = np.max([min_price, self.price * (1 + price_adj()[0])])
        elif statement_3 or statement_4:
            # price remains the same
            if statement_3:
                self.supply = self.supply * (1 - supply_adj()[0])
            else:
                self.supply = self.supply * (1 + supply_adj()[0])
            self.total_wages = self.wage * self.supply / self.productivity

    def check_loan_desire_and_choose_loans(self):
        # check if there is loan desire
        self.credit_demand = max([self.total_wages - self.equity_level, 0])
        self.financial_fragility = self.credit_demand / self.equity_level
        if self.credit_demand > 0:
            # pick random banks
            potential_lenders = random.choices(self.bank_ids, k=self.max_banks_loan)
            self.potential_lenders = dict([(bank_id, (self.idx, self.credit_demand)) for bank_id in potential_lenders])

    def adjust_production(self):
        if self.total_wages != self.equity_level:  # loan has not been paid so we do not have money for all wages
            #  we need to reduce supply
            self.supply = self.equity_level * self.productivity / self.wage

    def produce_supply(self):
        self.created_supply = self.supply
        self.equity_level -= self.total_wages
        return self.total_wages, int(self.created_supply / self.productivity), self.wage

    def compute_default_prob(self):
        if self.loans:
            credit_requested = self.loans[0][3]
            interest_rate_loan = self.loans[0][2]
            self.default_prob = 0.02

