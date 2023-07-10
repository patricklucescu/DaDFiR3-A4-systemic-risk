from abm_model.loan import Loan
from abm_model.baseclass import BaseAgent
import random
from abm_model.essentials import *


class BaseFirm(BaseAgent):
    """
    | BaseFirm class represents the base agent for a firm in the ABM model.
    """
    market_price = None
    min_wage = None
    max_leverage = None

    @classmethod
    def change_market_price(cls, new_value: float):
        """
        | Change the market price of the base firm.

        :param new_value: The new market price.
        """
        cls.market_price = new_value

    @classmethod
    def change_min_wage(cls, new_value: float):
        """
        | Change the minimum wage of the base firm.

        :param new_value: The new minimum wage.
        """
        cls.min_wage = new_value

    @classmethod
    def change_max_leverage(cls, new_value: float):
        """
        | Change the maximum leverage of the base firm.

        :param new_value: The new maximum leverage.
        """
        cls.max_leverage = new_value


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
        """
        | Constructor method that initializes the firm object with the specific parameters.

        :param idx: A unique identifier for the Firm.
        :param supply: Supply in the previous period.
        :param excess_supply: Excess supply in the previous period.
        :param price: Firm's good price in the previous period.
        :param wage: The wage the firm pays for the labour.
        :param equity: Equity of the firm.
        :param productivity: Productivity of the firm.
        :param default_probability: Default probability of the firm.
        """
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
        self.prev_equity = None

    def compute_expected_supply_and_prices(self):
        """
        | Compute the expected supply and prices for the firm.
        """
        self.wage = max([self.min_wage, self.wage * (1 + wages_adj())])
        self.price, self.supply = compute_expected_supply_price(self.excess_supply,
                                                                self.supply,
                                                                self.price,
                                                                self.market_price,
                                                                self.wage,
                                                                self.productivity)
        # make sure firm does not go beyond max leverage
        self.supply = min([self.productivity * (self.max_leverage + 1) * self.equity / self.wage, self.supply])
        # compute total wages
        self.total_wages = self.wage * self.supply / self.productivity

    def check_loan_desire_and_choose_loans(self):
        """
        | Check if the firm has a desire for loans and choose potential lenders.
        """
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
        """
        | Adjust the production based on the available funds.
        """
        if self.total_wages != self.equity:
            # loan has not been paid, so we do not have money for all wages
            #  we need to reduce supply
            self.supply = self.equity * self.productivity / self.wage
            self.total_wages = self.equity

    def produce_supply_consumption(self,
                                   min_consumption: float,
                                   max_consumption: float,
                                   overall_consumption: float,
                                   consumption_std: float):
        """
        | Produce the supply and handle consumption based on certain parameters.

        :param min_consumption: The minimum consumption as a percentage between 0 and 1.
        :param max_consumption: The maximum consumption as a percentage between 0 and 1.
        :param overall_consumption: The overall consumption.
        :param consumption_std: The standard deviation of consumption.
        """
        self.prev_equity = self.equity
        self.equity -= self.total_wages
        actual_consumption_percentage = min(max(min_consumption, np.random.normal(overall_consumption,
                                                                                  consumption_std)), max_consumption)
        self.equity += self.price * actual_consumption_percentage * self.supply
        self.excess_supply = (1 - actual_consumption_percentage) * self.supply

    def reset_variables(self):
        """
        | Resets the certain variables of the Firm object to make it ready to be used for the next period.
        """
        self.loans = []
        self.total_wages = None
        self.credit_demand = None
        self.financial_fragility = None
        self.potential_lenders = None
        self.recovery_rate = None

    def check_default(self):
        """
        | Check if the firm has defaulted.

        :return: True if the firm has defaulted, False otherwise.
        """
        if self.equity < sum([(1+loan.interest_rate) * loan.notional_amount for loan in self.loans]):
            # we have default of the entity
            return True
        return False
