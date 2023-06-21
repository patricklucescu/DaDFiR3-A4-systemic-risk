

class BaseAgent:
    policy_rate = None
    firm_ids = None
    bank_ids = None
    max_interbank_loan = None
    max_bank_loan = None
    max_cds_requests = None

    @classmethod
    def change_policy_rate(cls, new_value):
        cls.policy_rate = new_value

    @classmethod
    def change_firm_ids(cls, new_value):
        cls.firm_ids = new_value

    @classmethod
    def change_bank_ids(cls, new_value):
        cls.bank_ids = new_value

    @classmethod
    def change_max_interbank_loan(cls, new_value):
        cls.max_interbank_loan = new_value

    @classmethod
    def change_max_bank_loan(cls, new_value):
        cls.max_bank_loan = new_value

    @classmethod
    def change_max_cds_requests(cls, new_value):
        cls.max_cds_requests = new_value
