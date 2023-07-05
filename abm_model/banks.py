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
                 naked_cds_prob
                 ):
        """
        | Constructor method that initializes the bank object with the specific parameters.

        :param str idx: A unique identifier for the bank.
        :param float equity: The equity value of the bank.
        :param float deposits: The current deposit amount of the bank.
        :param float capital_requirement: The capital requirement of the bank.
        :param float covered_cds_prob: The probability of a covered credit default swap (CDS) being used by the bank.
        :param float naked_cds_prob: The probability of a naked CDS being used by the bank.
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

    def check_loan(self,
                   loan: Loan):
        """
        | Checks if a loan can be granted by the bank based on the maximum credit limit and other loan and
        asset amounts.

        :param loan: The loan in question.
        :return: It returns False if it cannot be granted. Otherwise, it returns the difference between the
        available funds and the notional of the loan.
        """
        if loan.notional_amount + sum([x.notional_amount for x in self.assets['loans']]) > self.max_credit:
            return False
        return (self.deposits + sum([x.notional_amount for x in self.liabilities['loans']]) -
                (loan.notional_amount + sum([x.notional_amount for x in self.assets['loans']])))

    def check_cds(self,
                  premium: float):
        #  TODO: this is not correctly implemented
        """
        | Checks if the CDS can be granted based on the maximum credit limit and other loan and asset amounts.

        :param premium: The CDS premium.
        :return:
        """
        return (self.deposits + sum([x.notional_amount for x in self.liabilities['loans']]) + self.equity -
                (sum([x.notional_amount for x in self.assets['loans']]) +
                 sum([x.spread * x.notional_amount for x in self.assets['cds']])) >= premium)

    def get_potential_interbank_loans(self,
                                      credit_needed: float,
                                      notional_amount: float) -> list[Loan]:
        """
        | Generates potential interbank loan offers from the bank to other banks.

        :param credit_needed: The needed credit to extend the firm loan
        :param notional_amount: The notional amount of the underlying Loan
        :return: list of potential interbank Loans.
        """
        financial_fragility = (notional_amount + sum([x.notional_amount for x in self.assets['loans']])) / self.deposits
        return [Loan(lender=x, borrower=self.idx,
                     notional_amount=credit_needed,
                     financial_fragility_borrower=financial_fragility)
                for x in random.choices([x for x in self.bank_ids if x != self.idx], k=self.max_interbank_loan)
                ]

    def decide_cds(self,
                   covered: bool = True) -> int:
        """
        | Decides whether to use a covered or naked credit default swap (CDS) based on the specified probabilities.

        :param covered: indicates whether a covered CDS should be considered.
        :return: 1 if a CDS is desired and 0 otherwise.
        """
        if covered:
            return np.random.binomial(1, self.covered_cds_prob)
        else:
            return np.random.binomial(1, self.naked_cds_prob)

    def provide_cds_spread(self,
                           loan: Loan) -> float:
        """
        | Function calculates and provides the spread value for a credit default swap (CDS) based on the Hull CDS
        valuation model for a one-period model.

        :param loan: Underlying Loan object on which the CDS is written.
        :return: CDS spread value.
        """
        R = 0.3
        q = loan.prob_default_borrower + max(np.random.normal(0, 0.01), 10 ** (-2) - loan.prob_default_borrower)
        u = 1 / (1 + self.policy_rate)
        v = 1 / (1 + self.policy_rate)
        e = 1 / (1 + self.policy_rate)
        A = loan.interest_rate
        pi = 1 - q
        return (1 - R - A * R) * q * v / (q * (u + e) + pi * u)

    def reset_variables(self):
        """
        | Resets the certain variables of the Bank object to make it ready to be used for the next period.
        """
        self.max_credit = None
        self.assets = {'loans': [], 'cds': []}
        self.liabilities = {'loans': [], 'cds': []}
        self.money_from_firm_loans = 0
        self.deposit_change = None
        self.current_deposits = None
        self.earnings = None
