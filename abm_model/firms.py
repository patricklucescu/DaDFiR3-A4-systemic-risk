from abm_model.loan import Loan
from abm_model.baseclass import BaseAgent
import numpy as np
import random
from abm_model.essentials import *


class BaseFirm(BaseAgent):
    market_price = None
    min_wage = None

    @classmethod
    def change_market_price(cls, new_value):
        cls.market_price = new_value

    @classmethod
    def change_min_wage(cls, new_value):
        cls.min_wage = new_value


class Firm(BaseFirm):
    def __init__(self,
                 idx,
                 supply,
                 excess_supply,
                 price,
                 wage,
                 equity,
                 productivity,
                 default_probability):
        super().__init__()
        self.idx = idx
        self.supply = supply
        self.excess_supply = excess_supply
        self.price = price
        self.wage = wage
        self.equity = equity
        self.productivity = productivity
        self.default_probability = default_probability
        # initialize other class variables
        self.loans = []
        self.total_wages = None
        self.credit_demand = None
        self.financial_fragility = None
        self.potential_lenders = None
        self.recovery_rate = None

    def compute_expected_supply_and_prices(self):
        """
        update the price and supply for the firm
        """
        self.wage = max([self.min_wage, self.wage * (1 + wages_adj()[0])])
        self.price, self.supply = compute_expected_supply_price(self.excess_supply,
                                                                self.supply,
                                                                self.price,
                                                                self.market_price,
                                                                self.wage,
                                                                self.productivity)
        self.total_wages = self.wage * self.supply / self.productivity

    def check_loan_desire_and_choose_loans(self):
        # check if there is loan desire
        self.credit_demand = max([self.total_wages - self.equity, 0])
        self.financial_fragility = self.credit_demand / self.equity
        if self.credit_demand > 0:
            # pick random banks
            potential_lenders = [Loan(lender=x,
                                      borrower=self.idx,
                                      notional_amount=self.credit_demand,
                                      financial_fragility_borrower=self.financial_fragility,
                                      prob_default_borrower=self.default_probability,
                                      ) for x in random.choices(self.bank_ids, k=self.max_bank_loan)
                                 ]
            self.potential_lenders = potential_lenders
        else:
            self.potential_lenders = []

    def adjust_production(self):
        if self.total_wages != self.equity:  # loan has not been paid, so we do not have money for all wages
            #  we need to reduce supply
            self.supply = self.equity * self.productivity / self.wage

    def produce_supply_consumption(self, min_consumption, max_consumption, overall_consumption, consumption_std):
        self.equity -= self.total_wages
        actual_consumption_percentage = min(max(min_consumption, np.random.normal(overall_consumption,
                                                                                  consumption_std)), max_consumption)
        self.equity += self.price * actual_consumption_percentage * self.supply
        self.excess_supply = (1 - actual_consumption_percentage) * self.supply

    def reset_variables(self):
        self.loans = []
        self.total_wages = None
        self.credit_demand = None
        self.financial_fragility = None
        self.potential_lenders = None
        self.recovery_rate = None

    def check_default(self):
        if self.equity < sum([(1+loan.interest_rate) * loan.notional_amount for loan in self.loans]):
            # we have default of the entity
            return True
        return False
