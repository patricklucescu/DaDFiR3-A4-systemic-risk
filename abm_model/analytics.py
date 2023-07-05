import matplotlib.pyplot as plt
import numpy as np

def analytics(historic_data, banks, t, T, economy_state,
              defaulted_banks, base_firm,
              base_agent, defaulted_firms, firms):

    #initialize dictionary
    if len(historic_data) == 0:
        historic_data['banks_equity'] = {}
        historic_data['market_price'] = []
        historic_data['average_wage'] = []
        historic_data['bank_defaults'] = []
        historic_data['firm_defaults'] = []


    #end-of-period reporting
    historic_data['banks_equity'] = update_bank_equity(historic_data['banks_equity'], banks, t)
    historic_data['market_price'] = update_market_prices(historic_data['market_price'],base_firm)
    historic_data['average_wage'] = udpate_average_wage(historic_data['average_wage'],firms)
    historic_data['bank_defaults'],historic_data['firm_defaults'] = update_nr_of_defaults(historic_data['bank_defaults']
                                                                                          ,historic_data['firm_defaults']
                                                                                          ,defaulted_firms,defaulted_banks)



    #end-of-simulation reporting
    if t==(T-1):
        plt.plot(historic_data['market_price'])
        plt.plot(historic_data['average_wage'])
        plt.title("Market Price and Wage")
        plt.legend(['Market Price','Average Wage'])
        plt.show()

        print(f'Last bank: {base_agent.bank_ids[len(base_agent.bank_ids)-1]}')
        print(f'Last bank: {base_agent.firm_ids[len(base_agent.firm_ids)-1]}')


    # print(f'time: {t} out of {T-1}')
    # print(f'economy state: {economy_state.current_state}')
    # print(f'defaulted banks: {defaulted_banks}')
    # print(f'market price: {base_firm.market_price}')

    return historic_data






def update_bank_equity(historic_bank_equity, banks, t):

    #update return dict

    updated_bank_equity = historic_bank_equity
    updated_bank_equity.update({t: {}})

    for bank_id in banks:
        updated_bank_equity[t].update({bank_id : banks[bank_id].equity})

    return updated_bank_equity




def update_market_prices(historic_market_price,base_firm):

    historic_market_price.append(base_firm.market_price)

    return historic_market_price



def update_nr_of_defaults(historic_bank_defaults,historic_firm_defaults,defaulted_firms,defaulted_banks):

    historic_bank_defaults.append(len(defaulted_banks))
    historic_firm_defaults.append(len(defaulted_firms))

    return historic_bank_defaults,historic_firm_defaults



def udpate_average_wage(histroic_average_wage, firms):

    histroic_average_wage.append(np.mean([firms[firm_id].wage for firm_id in firms]))

    return histroic_average_wage


