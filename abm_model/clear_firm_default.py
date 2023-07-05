from abm_model.markov_model import MarkovModel


def clear_firm_default(firms: dict,
                       banks: dict,
                       economy_state: MarkovModel,
                       good_consumption: list,
                       good_consumption_std: list,
                       min_consumption: float,
                       max_consumption: float):
    """
    |Clear the good markets and see what firms default. Additionally, for each CDS compute the recovery rate.

    :param firms: Dictionary with all firms.
    :param banks: Dictionary with all banks.
    :param economy_state: The economy state modelled as a Markov Model.
    :param good_consumption: Average good consumption for the different economy states.
    :param good_consumption_std: Standard deviation for the good consumption for the different economy states.
    :param min_consumption: Minimum consumption of goods.
    :param max_consumption: Maximum consumption of goods.
    :return: A tuple containing the updated firms dictionary, banks dictionary, and a list of defaulted firms.
    """

    # adjust production based on Credit Market & do the good consumption market
    overall_consumption = good_consumption[economy_state.current_state]
    consumption_std = good_consumption_std[economy_state.current_state]
    for firm_id in firms.keys():
        firms[firm_id].adjust_production()
        firms[firm_id].produce_supply_consumption(min_consumption,
                                                  max_consumption,
                                                  overall_consumption,
                                                  consumption_std)

    # see which firms remain solvent
    defaulted_firms = [firms[firm_id].idx for firm_id in firms.keys() if firms[firm_id].check_default()]
    # clear firm loan payments and update cds with recovery rate
    for firm_id in firms.keys():
        loans = firms[firm_id].loans
        total_loans = sum([(1 + loan.interest_rate) * loan.notional_amount for loan in loans])
        adjustment_factor = total_loans if firm_id not in defaulted_firms else firms[firm_id].equity
        for loan in loans:
            # payback
            banks[loan.lender].money_from_firm_loans += ((1 + loan.interest_rate) * loan.notional_amount
                                                         * adjustment_factor / total_loans)

        firms[firm_id].equity -= adjustment_factor
        # now compute recovery rate for any cds written on the current firm, given firm does have a loan
        # recovery rate not needed otherwise
        if len(loans) > 0:
            firms[firm_id].recovery_rate = adjustment_factor / total_loans

    return firms, banks, defaulted_firms
