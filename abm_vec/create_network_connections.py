import random

import numpy as np
from numpy import ndarray

from abm_vec.banks import asses_interbank_loans, check_cds, provide_cds_spread


def create_network_connections(
    loans_by_firm: dict,
    calibration_variables: dict,
    num_firms: int,
    num_banks: int,
    firm_credit_demand: ndarray,
    bank_max_credit: ndarray,
    bank_deposits: ndarray,
    bank_current_deposit: ndarray,
    firm_equity: ndarray,
    firm_pd: ndarray,
    bank_equity: ndarray,
) -> tuple:
    """
    | Create the Bank-to-Firm Loans, Bank-to-Bank Loans and the Bank-to-Bank CDS contracts.

    | The function covers the following steps:

    #. It iterates through each firm, sorting the available loans and attempting to secure one based on credit
    demand and the lending bank’s capacity.

    #. If a bank does not have enough credit or deposit to issue a loan, it seeks an interbank loan.
    The conditions for these loans depend on several factors like financial fragility, policy rate, and calibration
    variables.

    #. The function also handles the creation of CDS contracts, both covered and naked, based on certain probabilities.
    These contracts are established between different banks for each firm, depending on various factors including the
    default probability of the firm and the financial condition of the banks.

    :param loans_by_firm: Dictionary of possible loans for every firm
    :param calibration_variables: Calibration variables
    :param num_firms: Number of firms
    :param num_banks: Number of banks
    :param firm_credit_demand: The loan amount needed by every firm
    :param bank_max_credit: Maximum credit each bank is allowed to loan
    :param bank_deposits: Deposits of each bank
    :param bank_current_deposit: Current bank deposit
    :param firm_equity: Equity of each firm
    :param firm_pd: Probability default of firm
    :param bank_equity: Equity of the banks
    :return:
    """

    # define the needed variables for return
    loan_firms_interest = np.zeros((num_firms, num_banks))
    loan_firms_amount = np.zeros((num_firms, num_banks))
    loan_banks_interest = np.zeros((num_banks, num_banks))
    loan_banks_amount = np.zeros((num_banks, num_banks))
    bank_loan_asset = np.zeros((1, num_banks))[0]
    bank_loan_liability = np.zeros((1, num_banks))[0]
    cds_amount = np.zeros((num_firms, num_banks, num_banks))
    cds_spread = np.zeros((num_firms, num_banks, num_banks))
    cds_asset = np.zeros((1, num_banks))[0]
    cds_spread_amount = np.zeros((num_banks, num_banks))
    cds_dict = {}

    for firm_id in range(num_firms):
        loans_firm = sorted(loans_by_firm[firm_id], key=lambda x: x[1])
        credit = firm_credit_demand[firm_id]
        loan_extended = False
        # loop over available loans and try to secure one
        for loan in loans_firm:
            bank_id = loan[0]
            # check if bank has enough credit left to issue the loan
            if credit + bank_loan_asset[bank_id] > bank_max_credit[bank_id]:
                # loan breaks above max credit and cannot be issued
                continue
            else:
                # not above max credit so could potentially issue the loan
                bank_condition = (
                    bank_deposits[bank_id]
                    + bank_loan_liability[bank_id]
                    - (credit + bank_loan_asset[bank_id])
                )
                if bank_condition > 0:
                    # still have money on balance sheet so can directly issue the loan
                    loan_extended = True
                else:
                    # bank needs to get an interbank loan
                    credit_interbank = -bank_condition
                    financial_fragility = (
                        credit_interbank + bank_loan_asset[bank_id]
                    ) / bank_deposits[bank_id]
                    # get potential interbank loans
                    ib_seller = np.array(
                        random.choices(
                            [x for x in range(num_banks) if x != bank_id],
                            k=calibration_variables["max_interbank_loan"],
                        )
                    )
                    ib_ir = asses_interbank_loans(
                        financial_fragility,
                        calibration_variables["policy_rate"],
                        calibration_variables["max_interbank_loan"],
                        calibration_variables["h_theta"],
                    )
                    # sort offers in ascending order of the interest rate
                    sorted_indices = np.argsort(ib_ir)
                    ib_ir = ib_ir[sorted_indices]
                    ib_seller = ib_seller[sorted_indices]
                    # now see which one you can accept
                    for j in range(calibration_variables["max_interbank_loan"]):
                        # here we also need to check max_credit, not only if the lending bank has enough liquidity
                        if (
                            bank_deposits[ib_seller[j]]
                            + bank_loan_liability[ib_seller[j]]
                            - (credit_interbank + bank_loan_asset[ib_seller[j]])
                            > 0
                        ) and (
                            (credit_interbank + bank_loan_asset[ib_seller[j]])
                            > bank_max_credit[ib_seller[j]]
                        ):
                            # can issue the interbank loan
                            loan_banks_interest[bank_id, ib_seller[j]] = ib_ir[j]
                            loan_banks_amount[bank_id, ib_seller[j]] = credit_interbank
                            bank_loan_asset[ib_seller[j]] += credit_interbank
                            bank_loan_liability[bank_id] += credit_interbank
                            bank_current_deposit[ib_seller[j]] -= credit
                            loan_extended = True
            if loan_extended:
                # issue the firm loan
                loan_interest_rate = loan[1]
                loan_firms_interest[firm_id, bank_id] = loan_interest_rate
                loan_firms_amount[firm_id, bank_id] = credit
                # now take care of the actual variables
                bank_loan_asset[bank_id] += credit
                bank_current_deposit[bank_id] -= credit
                firm_equity[firm_id] += credit
                # now can create CDS connections
                if (
                    calibration_variables["covered_cds_prob"] > 0
                    or calibration_variables["naked_cds_prob"] > 0
                ):
                    # create cds connections
                    covered_buyer = (
                        [bank_id]
                        if np.random.binomial(
                            1, calibration_variables["covered_cds_prob"]
                        )
                        else []
                    )
                    naked_buyer = [
                        buyer
                        for buyer in range(num_banks)
                        if np.random.binomial(
                            1, calibration_variables["naked_cds_prob"]
                        )
                        and buyer != bank_id
                    ]
                    cds_buyers = covered_buyer + naked_buyer
                    if len(cds_buyers) > 0:
                        cds_sellers = [
                            seller
                            for seller in range(num_banks)
                            if seller not in cds_buyers and seller != bank_id
                        ]
                        # now choose potential connections
                        cds_offers = {
                            buyer: np.random.choice(
                                cds_sellers,
                                calibration_variables["max_cds_requests"],
                                replace=False,
                            )
                            for buyer in cds_buyers
                        }
                        cds_offers = {
                            buyer: [
                                (
                                    seller,
                                    provide_cds_spread(
                                        firm_pd[firm_id],
                                        calibration_variables["policy_rate"],
                                        loan_interest_rate,
                                    ),
                                )
                                for seller in cds_offers[buyer]
                            ]
                            for buyer in cds_buyers
                        }
                        cds_offers = {
                            buyer: sorted(cds_offers[buyer], key=lambda x: x[1])
                            for buyer in cds_offers
                        }
                        # see if it is affordable for the seller
                        cds_offers = {
                            buyer: [
                                seller
                                for seller in cds_offers[buyer]
                                if check_cds(
                                    bank_deposits[seller[0]],
                                    bank_loan_liability[seller[0]],
                                    bank_loan_asset[seller[0]],
                                    bank_equity[seller[0]],
                                    cds_asset[seller[0]],
                                    seller[1] * credit,  # the premium
                                )
                            ]
                            for buyer in cds_offers
                        }
                        # select only entries where there are offers
                        cds_offers = {
                            key: value for key, value in cds_offers.items() if value
                        }
                        cds_offers = {
                            buyer: cds_offers[buyer][0] for buyer in cds_offers
                        }
                        # enter transactions
                        transaction_buyer = []
                        transaction_seller = []
                        for buyer in cds_offers:
                            seller = cds_offers[buyer][0]
                            spread = cds_offers[buyer][1]
                            total = credit * spread
                            cds_asset[buyer] += total
                            cds_amount[firm_id, buyer, seller] = credit
                            cds_spread[firm_id, buyer, seller] = spread
                            cds_spread_amount[buyer, seller] += total
                            transaction_buyer.append(buyer)
                            transaction_seller.append(seller)
                        cds_dict[firm_id] = [
                            credit,
                            transaction_buyer,
                            transaction_seller,
                        ]
                break
    return (
        loan_firms_interest,
        loan_firms_amount,
        loan_banks_interest,
        loan_banks_amount,
        cds_amount,
        cds_spread,
        cds_spread_amount,
        bank_current_deposit,
        firm_equity,
        cds_dict,
        bank_loan_asset,
    )
