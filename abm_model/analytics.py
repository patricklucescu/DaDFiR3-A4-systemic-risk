import matplotlib.pyplot as plt
import numpy as np
from abm_model.markov_model import MarkovModel
from abm_model.firms import BaseFirm
from abm_model.baseclass import BaseAgent
from abm_model.loan import Loan
from abm_model.credit_default_swap import CDS


def analytics(historic_data: dict,
              banks: dict,
              t: float,
              T: float,
              economy_state: MarkovModel,
              defaulted_banks: list,
              base_firm: BaseFirm,
              base_agent: BaseAgent,
              defaulted_firms: list,
              firms: dict,
              period_t_transactions: list) -> dict:
    """
    | Perform analytics and update historic data during the simulation.

    :param historic_data: A dictionary containing the historic data.
    :param banks: A dictionary containing all banks.
    :param t: The current time step.
    :param T: The total number of time steps in the simulation.
    :param economy_state: The economy state modeled as a Markov Model.
    :param defaulted_banks: A list of defaulted bank IDs.
    :param base_firm: An instance of the BaseFirm class.
    :param base_agent: An instance of the BaseAgent class.
    :param defaulted_firms: A list of defaulted firm IDs.
    :param firms: A dictionary containing all firms.
    :param period_t_transactions: A list containing all transactions of period t
    :return: The updated historic data dictionary.
    """
    # initialize dictionary
    if len(historic_data) == 0:
        historic_data['banks_equity'] = {}
        historic_data['market_price'] = []
        historic_data['average_wage'] = []
        historic_data['bank_defaults'] = []
        historic_data['firm_defaults'] = []
        historic_data['average_firmloan_ir'] = []
        historic_data['average_bankloan_ir'] = []
        historic_data['average_cds_spread'] = []
        historic_data['total_firmloan'] = []
        historic_data['total_bankloan'] = []
        historic_data['total_cds_notional'] = []
        historic_data['bank_equity'] = []
        historic_data['bank_deposits'] = []
        historic_data['firm_equity'] = []
        historic_data['firm_market_power'] = []


    #end-of-period reporting
    historic_data['banks_equity'] = update_bank_equity(historic_data['banks_equity'], banks, t)
    historic_data['market_price'] = update_market_prices(historic_data['market_price'],base_firm)
    historic_data['average_wage'] = udpate_average_wage(historic_data['average_wage'],firms)
    historic_data['bank_defaults'],historic_data['firm_defaults'] \
        = update_nr_of_defaults(historic_data['bank_defaults']
                                ,historic_data['firm_defaults']
                                ,defaulted_firms,defaulted_banks)
    historic_data['average_firmloan_ir'],historic_data['average_bankloan_ir'],historic_data['average_cds_spread'], \
        historic_data['total_firmloan'], historic_data['total_bankloan'], historic_data['total_cds_notional'] \
                = update_transaction_metrics(historic_data['average_firmloan_ir']
                                             ,historic_data['average_bankloan_ir']
                                             ,historic_data['average_cds_spread']
                                             ,historic_data['total_firmloan']
                                             ,historic_data['total_bankloan']
                                             ,historic_data['total_cds_notional']
                                             ,period_t_transactions
                                             ,base_agent)
    historic_data['bank_equity'],historic_data['bank_deposits'] = udpate_deposits_equity_bank(historic_data['bank_equity'],historic_data['bank_deposits'],banks)
    historic_data['firm_equity'],historic_data['firm_market_power'] = udpate_deposits_equity_firm(historic_data['firm_equity'],historic_data['firm_market_power'],firms)

    #end-of-simulation reporting
    if t==(T-1):
        fig, ax = plt.subplots(2, 3)
        fig.set_size_inches(25, 12)

        color1='blue'
        color2='orange'
        color3='green'
        color4='black'

        ax[0,0].plot(historic_data['market_price'], color=color1)
        ax[0,0].set_ylabel('Market Price',color=color1)
        ax[0,0].tick_params(axis='y', labelcolor=color1)
        rightAx=ax[0,0].twinx()
        rightAx.plot(historic_data['average_wage'],color=color2)
        rightAx.set_ylabel('Average Wage', color=color2)
        rightAx.tick_params(axis='y', labelcolor=color2)
        ax[0,0].set_title("Market Price and Wage")

        ax[0,1].plot(historic_data['bank_defaults'], color=color1)
        ax[0,1].set_ylabel('Bank Defaults',color=color1)
        ax[0,1].tick_params(axis='y', labelcolor=color1)
        rightAx=ax[0,1].twinx()
        rightAx.plot(historic_data['firm_defaults'],color=color2)
        rightAx.set_ylabel('Firm Defaults', color=color2)
        rightAx.tick_params(axis='y', labelcolor=color2)
        ax[0,1].set_title("Bank and Firm Defaults")

        ax[1,0].plot(historic_data['average_firmloan_ir'], color=color1)
        ax[1,0].plot(historic_data['average_bankloan_ir'], color=color3)
        ax[1,0].legend(['Firm Loan IR', 'Interbank Loan IR'])
        ax[1,0].set_ylabel('Interest Rates', color=color4)
        ax[1,0].tick_params(axis='y', labelcolor=color4)
        rightAx = ax[1,0].twinx()
        rightAx.plot(historic_data['average_cds_spread'], color=color2)
        rightAx.set_ylabel('Spreads', color=color2)
        rightAx.tick_params(axis='y', labelcolor=color2)
        ax[1,0].set_title("Interest Rates and Spreads")

        ax[1,1].plot(historic_data['total_firmloan'], color=color1)
        ax[1,1].plot(historic_data['total_bankloan'], color=color3)
        ax[1,1].legend(['Firm Loans Total Notional', 'Interbank Loans Total Notional'])
        ax[1,1].set_ylabel('Loans Total', color=color4)
        ax[1,1].tick_params(axis='y', labelcolor=color4)
        rightAx = ax[1,1].twinx()
        rightAx.plot(historic_data['total_cds_notional'], color=color2)
        rightAx.set_ylabel('CDS Notional', color=color2)
        rightAx.tick_params(axis='y', labelcolor=color2)
        ax[1,1].set_title("Notional Loans and CDS")

        ax[0,2].plot(historic_data['bank_equity'], color=color1)
        ax[0,2].set_ylabel('Bank Equity',color=color1)
        ax[0,2].tick_params(axis='y', labelcolor=color1)
        rightAx=ax[0,2].twinx()
        rightAx.plot(historic_data['bank_deposits'],color=color2)
        rightAx.set_ylabel('Bank Deposits', color=color2)
        rightAx.tick_params(axis='y', labelcolor=color2)
        ax[0,2].set_title("Bank Equity and Deposits")

        ax[1,2].plot(historic_data['firm_equity'], color=color1)
        ax[1,2].set_ylabel('Firm Equity',color=color1)
        ax[1,2].tick_params(axis='y', labelcolor=color1)
        rightAx=ax[1,2].twinx()
        rightAx.plot(historic_data['firm_market_power'],color=color2)
        rightAx.set_ylabel('Fraction Largest Firm', color=color2)
        rightAx.tick_params(axis='y', labelcolor=color2)
        ax[1,2].set_title("Firm Equity and Market Power")
        plt.show()

        print(f'Last bank: {base_agent.bank_ids[len(base_agent.bank_ids)-1]}')
        print(f'Last bank: {base_agent.firm_ids[len(base_agent.firm_ids)-1]}')


    # print(f'time: {t} out of {T-1}')
    # print(f'economy state: {economy_state.current_state}')
    # print(f'defaulted banks: {defaulted_banks}')
    # print(f'market price: {base_firm.market_price}')
    return historic_data


def update_bank_equity(historic_bank_equity: dict,
                       banks: dict,
                       t: float) -> dict:
    """
    | Update the historic bank equity data with the current bank equity values.

    :param historic_bank_equity: A dictionary containing the historic bank equity data.
    :param banks: A dictionary containing all banks.
    :param t: The current time step.
    :return: The updated historic bank equity data.
    """
    updated_bank_equity = historic_bank_equity
    updated_bank_equity.update({t: {}})
    for bank_id in banks:
        updated_bank_equity[t].update({bank_id: banks[bank_id].equity})
    return updated_bank_equity


def update_market_prices(historic_market_price: list,
                         base_firm: BaseFirm) -> list:
    """
    | Update the historic market price data with the current market price data.

    :param historic_market_price: A dictionary containing the historic market price data.
    :param base_firm: The BaseFirm agent.
    :return: THe updated historic market price data.
    """
    historic_market_price.append(base_firm.market_price)

    return historic_market_price


def update_nr_of_defaults(historic_bank_defaults: list,
                          historic_firm_defaults: list,
                          defaulted_firms: list,
                          defaulted_banks: list) -> tuple:
    """
    | Update historic number of defaulted Banks and Firms.

    :param historic_bank_defaults: Historic number of Banks default list.
    :param historic_firm_defaults: Historic number of Firms default list.
    :param defaulted_firms: Current period defaulted Firms.
    :param defaulted_banks: Current period defaulted Banks.
    :return: The updated historic number of defaulted Banks and Firms.
    """
    historic_bank_defaults.append(len(defaulted_banks))
    historic_firm_defaults.append(len(defaulted_firms))

    return historic_bank_defaults, historic_firm_defaults


def udpate_average_wage(historic_average_wage: list,
                        firms: dict) -> list:
    """
    | Update the historic average wage of the firms.

    :param historic_average_wage: Historic average wage of the firms.
    :param firms: Current period firms.
    :return: The updated historic average wage.
    """
    historic_average_wage.append(np.mean([firms[firm_id].wage for firm_id in firms]))

    return historic_average_wage



def update_transaction_metrics(historic_average_firmloan_ir
                               ,historic_average_bankloan_ir
                               ,historic_data_average_cds_spread
                               ,historic_data_total_firmloan
                               ,historic_data_total_bankloan
                               ,historic_data_total_cds_notional
                               ,period_t_transactions, base_agent):

    notional_amount_weighted_ir_bankloan = 0; total_bankloan = 0
    notional_amount_weighted_ir_firmloan = 0; total_firmloan = 0
    notional_amount_weighted_cds_spread = 0; total_cds_notional = 0

    for transaction_id in range(len(period_t_transactions)):

        if type(period_t_transactions[transaction_id].data) == Loan:

            if period_t_transactions[transaction_id].data.borrower in base_agent.firm_ids:
                notional_amount_weighted_ir_firmloan += period_t_transactions[transaction_id].data.notional_amount * \
                                                        period_t_transactions[transaction_id].data.interest_rate
                total_firmloan += period_t_transactions[transaction_id].data.notional_amount
            else:
                notional_amount_weighted_ir_bankloan += period_t_transactions[transaction_id].data.notional_amount * \
                                                        period_t_transactions[transaction_id].data.interest_rate
                total_bankloan += period_t_transactions[transaction_id].data.notional_amount

        elif type(period_t_transactions[transaction_id].data) == CDS:

            notional_amount_weighted_cds_spread += period_t_transactions[transaction_id].data.notional_amount * \
                                                        period_t_transactions[transaction_id].data.spread
            total_cds_notional += period_t_transactions[transaction_id].data.notional_amount

    if total_firmloan == 0:
        historic_average_firmloan_ir.append(0)
    else:
        historic_average_firmloan_ir.append(notional_amount_weighted_ir_firmloan/total_firmloan)
    if total_bankloan == 0:
        historic_average_bankloan_ir.append(0)
    else:
        historic_average_bankloan_ir.append(notional_amount_weighted_ir_bankloan / total_bankloan)
    if total_cds_notional == 0:
        historic_data_average_cds_spread.append(0)
    else:
        historic_data_average_cds_spread.append(notional_amount_weighted_cds_spread / total_cds_notional)
    historic_data_total_firmloan.append(total_firmloan)
    historic_data_total_bankloan.append(total_bankloan)
    historic_data_total_cds_notional.append(total_cds_notional)


    return historic_average_firmloan_ir,historic_average_bankloan_ir,historic_data_average_cds_spread, \
        historic_data_total_firmloan,historic_data_total_bankloan,historic_data_total_cds_notional



def udpate_deposits_equity_bank(historic_bank_equity,historic_bank_deposits,banks):

    historic_bank_equity.append(sum([banks[bank_id].equity for bank_id in banks]))
    historic_bank_deposits.append(sum([banks[bank_id].deposits for bank_id in banks]))

    return historic_bank_equity, historic_bank_deposits



def udpate_deposits_equity_firm(historic_data_firm_equity,historic_data_firm_market_power,firms):

    total_equity = sum([firms[firm_id].equity for firm_id in firms])
    historic_data_firm_equity.append(total_equity)
    historic_data_firm_market_power.append(max([firms[firm_id].equity for firm_id in firms])/total_equity)

    return historic_data_firm_equity,historic_data_firm_market_power




