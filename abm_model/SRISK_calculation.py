import numpy as np
import mgarch

def calculate_SRISK(returns_by_time, returns_by_bank, debt_by_time, debt_by_bank):

    c = 0.15
    k = 0.08

    srisk_by_time = {}
    srisk_by_bank = {}
    market_returns = np.zeros(len(returns_by_time))

    for t in range(len(returns_by_time)):
        market_returns[t] = np.sum([equity for equity in returns_by_time[t].values()])
    temp = np.roll(market_returns,1)
    temp[0] = np.nan
    market_returns = np.log(market_returns/temp)


    #market_returns = [ sum()returns_by_time





    rt = np.array(np.random.multivariate_normal([1,0],[[2**2,0.5**2],[0.5**2,1**2]],100))

    vol = mgarch.mgarch()
    vol.fit(rt)
    ndays = 1 # volatility of nth day
    cov_nextday = vol.predict(ndays)

    return srisk_by_time, srisk_by_bank

