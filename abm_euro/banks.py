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

    def update_current_deposits(self):
        """
        | Updates the current_deposits attribute of the bank object to the deposits of the bank.
        """
        self.current_deposits = self.deposits

    def update_max_credit(self):
        """
        | Updates the max_credit attribute of the bank object based on the ratio of deposits to the capital requirement.
        """
        self.max_credit = self.deposits / self.capital_requirement

    def asses_loan_requests(self,
                            loans: list[Loan]) -> list:
        """
        | Asses loan requests received by the bank and returns a list of loan offers made by the bank.
        It iterates over the loan requests, considering factors such as the borrower type and financial
        fragility to update the interest rate of the loan offers.

        :param loans: list of Loan objects.
        :return: List of Loans that could be granted.
        """
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
                # TODO: might be advisable to change how interbank interest rates are computed
                loan.update_interest_rate(self.policy_rate * (1 + np.random.uniform(0, self.h_theta) *
                                                              np.tanh(loan.financial_fragility_borrower)))
                loan_offers.append(loan)
        return loan_offers

