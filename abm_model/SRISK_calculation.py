import numpy as np
import mgarch
import pandas as pd

def calculate_SRISK(equity_by_time, equity_by_bank, debt_by_bank):

    c = 0.15
    k = 0.08
    SRISK_calculation_start = 250
    nperiods_rolling_window = 20
    dcc_garch_calibration = 10


    SRISK = pd.DataFrame(index=list((equity_by_time.keys())),columns=equity_by_bank.keys())

    market_returns = np.zeros(len(equity_by_time))
    bank_equity = pd.DataFrame(index=list((equity_by_time.keys())))
    bank_debt = pd.DataFrame(index=list((equity_by_time.keys())))

    for t in range(len(equity_by_time)):
        market_returns[t] = np.sum([equity for equity in equity_by_time[t].values()])
    temp = np.roll(market_returns,1)
    temp[0] = np.nan
    market_returns = np.log(market_returns/temp)
    market_returns = pd.DataFrame(market_returns,index=list((equity_by_time.keys())),columns=['market_return'])
    cols = list(equity_by_bank.keys())
    cols.append('market_return')
    market_returns_standardized_innovations = pd.DataFrame(index=list(equity_by_time.keys()),
                                                           columns=cols)
    cov_cor_mean_hist = pd.DataFrame(index=list((equity_by_time.keys())),
                                                           columns=equity_by_bank.keys())

    #construction of market and bank returns
    for bank_id in equity_by_bank:
        current_returns = list(equity_by_bank[bank_id].values())
        #remove last period, i.e. period t = 300 OR period where equity = 0
        current_returns[-1] = np.nan
        temp = np.roll(current_returns,1)
        temp[0] = np.nan
        bank_return = pd.DataFrame(np.log(current_returns/temp),
                                   index=list((equity_by_bank[bank_id].keys())),columns=[bank_id])
        market_returns = market_returns.join(bank_return)

        equity = pd.DataFrame(list(equity_by_bank[bank_id].values()),
                              index=list((equity_by_bank[bank_id].keys())),columns=[bank_id])
        debt = pd.DataFrame(list(debt_by_bank[bank_id].values()),
                            index=list((debt_by_bank[bank_id].keys())),columns=[bank_id])

        bank_equity = bank_equity.join(equity)
        bank_debt = bank_debt.join(debt)

    # #remove model calibration period
    # market_returns = market_returns[market_returns.index >= 99]
    # bank_equity = bank_equity[bank_equity.index >= 99]
    # bank_debt = bank_debt[bank_debt.index >= 99]

    #construction of standardized innovations
    for bank_id in equity_by_bank:

        for dcc_garch_period in range(SRISK_calculation_start - nperiods_rolling_window, len(equity_by_time) - 1):

            dcc_garch_starting_period = SRISK_calculation_start - nperiods_rolling_window -dcc_garch_calibration

            initial_period = market_returns.loc[dcc_garch_starting_period: SRISK_calculation_start][['market_return', bank_id]] * 100
            if initial_period.isnull().any().any():
                break

            if dcc_garch_period - dcc_garch_starting_period < nperiods_rolling_window:
                dcc_garch_returns = market_returns.loc[dcc_garch_starting_period : dcc_garch_period + 1][['market_return', bank_id]]*100
            else:
                dcc_garch_returns = market_returns.loc[dcc_garch_period - nperiods_rolling_window: dcc_garch_period + 1][['market_return', bank_id]]*100

             #demean
            mean_market = np.mean(dcc_garch_returns['market_return'])
            mean_bank = np.mean(dcc_garch_returns[bank_id])
            dcc_garch_returns['market_return'] = dcc_garch_returns['market_return'] - mean_market
            dcc_garch_returns[bank_id] = dcc_garch_returns[bank_id] - mean_bank

            #if data is available for full period (t-rolling window : t), calculate SRISK for t+1
            if not dcc_garch_returns.isnull().any().any():

                vol = mgarch.mgarch()
                vol.fit(dcc_garch_returns[:-1][:])
                cov_nextday = vol.predict(1)
                cov_cor_mean = {'cov_market' : cov_nextday['cov'][0][0], 'cov_bank' : cov_nextday['cov'][1][1],
                              'correlation' : cov_nextday['cov'][0][1]/(cov_nextday['cov'][0][0]*cov_nextday['cov'][1][1]),
                              'mean_market' : mean_market, 'mean_bank' : mean_bank}
                market_returns_standardized_innovations.loc[dcc_garch_period + 1][bank_id] = (dcc_garch_returns.loc[dcc_garch_period + 1][bank_id]/cov_cor_mean['cov_bank'] -
                                                                                          cov_cor_mean['correlation']*dcc_garch_returns.loc[dcc_garch_period + 1]['market_return']/cov_cor_mean['cov_market']) \
                                                                                         /(1-cov_cor_mean['correlation']**2)**0.5
                #gets written multiple times, i.e. for each bank, but does not matter as it should remain the same
                market_returns_standardized_innovations.loc[dcc_garch_period + 1]['market_return'] = (dcc_garch_returns.loc[dcc_garch_period + 1]['market_return']
                                                                                        / cov_cor_mean['cov_market'])
                cov_cor_mean_hist.loc[dcc_garch_period + 1][bank_id] = cov_cor_mean


    for period in range(SRISK_calculation_start, len(equity_by_time)):

        continue


    return SRISK

