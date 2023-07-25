import numpy as np
import mgarch
import pandas as pd

def calculate_SRISK(equity_by_time, equity_by_bank, debt_by_bank):

    c = 0.15
    k = 0.08

    srisk_by_time = {}
    srisk_by_bank = {}
    market_returns = np.zeros(len(equity_by_time))
    bank_equity = pd.DataFrame(index=list((equity_by_time.keys())))
    bank_debt = pd.DataFrame(index=list((equity_by_time.keys())))

    for t in range(len(equity_by_time)):
        market_returns[t] = np.sum([equity for equity in equity_by_time[t].values()])
    temp = np.roll(market_returns,1)
    temp[0] = np.nan
    market_returns = np.log(market_returns/temp)
    market_returns = pd.DataFrame(market_returns,index=list((equity_by_time.keys())),columns=['market_return'])

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

    #remove model calibration period
    market_returns = market_returns[market_returns.index >= 99]
    bank_equity = bank_equity[bank_equity.index >= 99]
    bank_debt = bank_debt[bank_debt.index >= 99]


    #market_returns = [ sum()returns_by_time





    rt = np.array(np.random.multivariate_normal([1,0],[[2**2,0.5**2],[0.5**2,1**2]],100))

    vol = mgarch.mgarch()
    vol.fit(rt)
    ndays = 1 # volatility of nth day
    cov_nextday = vol.predict(ndays)

    return srisk_by_time, srisk_by_bank

