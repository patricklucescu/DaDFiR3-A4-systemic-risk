from abm_model.loan import Loan
from abm_model.baseclass import BaseAgent
import numpy as np
import random


class BaseBank(BaseAgent):
    """
    | Base Bank agent that stores variables common to all banks.
    """
    deposit_systemic_shock = None
    h_theta = None

    @classmethod
    def change_value_deposit_systemic(cls, new_value):
        """
        | Function to change the value of the deposit systemic shock.

        :param new_value: Value of the deposit systemic shock.
        """
        cls.deposit_systemic_shock = new_value

    @classmethod
    def change_h_theta(cls, new_value):
        """
        | Function to change the value of h_theta which controls the randomness in the interest rate for loans.

        :param new_value: Value of h_theta.
        """
        cls.h_theta = new_value


class Bank(BaseBank):
    """
    | Bank class that inherits from a class called BaseBank.
    It incorporates various decision-making actions needed for a bank.
    """

    def __init__(self,
                 idx,
                 equity,
                 deposits,
                 capital_requirement,
                 covered_cds_prob,
                 naked_cds_prob,
                 tier_1_cap,
                 gross_loans,
                 ):
        """
        | Constructor method that initializes the bank object with the specific parameters.

        :param str idx: A unique identifier for the bank.
        :param float equity: The equity value of the bank.
        :param float deposits: The current deposit amount of the bank.
        :param float capital_requirement: The capital requirement of the bank.
        :param float covered_cds_prob: The probability of a covered credit default swap (CDS) being used by the bank.
        :param float naked_cds_prob: The probability of a naked CDS being used by the bank.
        :param flaot tier_1_cap: The Tier 1 capital ration.
        :param float gross_loans: The total amount of loans.
        """
        super().__init__()
        self.idx = idx
        self.equity = equity
        self.deposits = deposits
        self.capital_requirement = capital_requirement
        self.covered_cds_prob = covered_cds_prob
        self.naked_cds_prob = naked_cds_prob
        self.max_credit = None
        self.assets = {'loans': [], 'cds': []}
        self.liabilities = {'loans': [], 'cds': []}
        self.money_from_firm_loans = 0
        self.deposit_change = None
        self.current_deposits = None
        self.earnings = None
        self.tier_1_cap = tier_1_cap
        self.gross_loans = gross_loans

