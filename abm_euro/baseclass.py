

class BaseAgent:
    """
    | Base agent that stores simulation variables.
    """
    policy_rate = None
    firm_ids = None
    bank_ids = None
    max_interbank_loan = None
    max_bank_loan = None
    max_cds_requests = None

    @classmethod
    def change_policy_rate(cls, new_value):
        """
        | Change the policy rate.

        :param new_value: New policy rate.
        """
        cls.policy_rate = new_value

    @classmethod
    def change_firm_ids(cls, new_value):
        """
        | Change the list of firm ids.

        :param new_value: New list of firm ids.
        """
        cls.firm_ids = new_value

    @classmethod
    def change_bank_ids(cls, new_value):
        """
        | Change the list of bank ids.

        :param new_value: New list of bank ids.
        """
        cls.bank_ids = new_value

    @classmethod
    def change_max_interbank_loan(cls, new_value):
        """
        | Change maximum number of banks a bank can go for an interbank loan.

        :param new_value: Maximum number of interbank loan applications.
        """
        cls.max_interbank_loan = new_value

    @classmethod
    def change_max_bank_loan(cls, new_value):
        """
        | Change maximum number of banks a firm can go for a loan.

        :param new_value: Maximum number of firm-bank loan applications.
        """
        cls.max_bank_loan = new_value

    @classmethod
    def change_max_cds_requests(cls, new_value):
        """
        | Change maximum number of banks a bank can go for a CDS.

        :param new_value: Maximum number of CDS applications.
        """
        cls.max_cds_requests = new_value
