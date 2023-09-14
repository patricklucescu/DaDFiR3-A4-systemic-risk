import numpy as np
import mgarch
import pandas as pd
import random
import math
import time
# import cupy as cp
import matplotlib.pyplot as plt
import copy

def calculate_SRISK(equity_by_time, equity_by_bank, debt_by_bank):

    start = time.time()

    #%% Variable initialization
    #conditional market shortfall
    c = -0.10
    #prudential capital fraction
    k = 0.08
    #h-period LRMES
    h = 15
    #number of Monte-Carlo simulations
    S = 50000

    monte_carlo_srisk = False

    srisk_calculation_start = 250
    nperiods_rolling_window = 150
    dcc_garch_calibration = 30

    lrmes = pd.DataFrame(index=list((equity_by_time.keys())), columns=equity_by_bank.keys())
    srisk = pd.DataFrame(index=list((equity_by_time.keys())),columns=equity_by_bank.keys())

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
    for bank_id in list(equity_by_bank.keys()):
        cols.append(bank_id+'_vola_adjusted')
    cols.append('market_return')
    cols.append('market_return_window')
    market_returns_standardized_innovations = pd.DataFrame(index=list(equity_by_time.keys()),
                                                           columns=cols)
    dcc_garch_params = pd.DataFrame(index=list((equity_by_time.keys())),
                                                           columns=equity_by_bank.keys())

    # %% construction of market and bank returns
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

    debt_equity_leverage = (bank_debt)/bank_equity
    quasi_leverage = (bank_debt + bank_equity) / bank_equity

    # %% construction of standardized innovations
    if monte_carlo_srisk:

        for bank_id in equity_by_bank:

            print(f'{bank_id} in innovation sequences')

            dcc_garch_starting_period = srisk_calculation_start - nperiods_rolling_window - dcc_garch_calibration

            # if the return history in the relevant period (start SRISK calculation - calibration time : end) is
            # too short ( <= size rolling window + initial DCC-GARCH clibration) then do not consider that bank
            period_of_interest = market_returns.loc[dcc_garch_starting_period: len(equity_by_time)][bank_id]
            period_of_interest = period_of_interest.dropna()
            if len(period_of_interest) <= (nperiods_rolling_window + dcc_garch_calibration):
                continue

            for dcc_garch_period in range(srisk_calculation_start - nperiods_rolling_window, len(equity_by_time) - 1):

                if dcc_garch_period - dcc_garch_starting_period < nperiods_rolling_window:
                    dcc_garch_returns = market_returns.loc[dcc_garch_starting_period : dcc_garch_period + 1][['market_return', bank_id]]
                else:
                    dcc_garch_returns = market_returns.loc[dcc_garch_period - nperiods_rolling_window: dcc_garch_period + 1][['market_return', bank_id]]

                 #demean
                mean_market = np.mean(dcc_garch_returns[:-1][:]['market_return'])
                mean_bank = np.mean(dcc_garch_returns[:-1][:][bank_id])
                dcc_garch_returns['market_return'] = dcc_garch_returns['market_return'] - mean_market
                dcc_garch_returns[bank_id] = dcc_garch_returns[bank_id] - mean_bank

                #if data is available for full period (t-rolling window : t), calculate SRISK for t+1
                if not dcc_garch_returns.isnull().any().any():

                    vol = mgarch.mgarch()
                    vol.fit(dcc_garch_returns[:-1][:])
                    cov_nextday = vol.predict(1)
                    current_dcc_garch_params = {'vola_market_period_ahead' : cov_nextday['cov'][0][0]**0.5, 'vola_bank_period_ahead' : cov_nextday['cov'][1][1]**0.5,
                                  'correlation_period_ahead' : cov_nextday['cov'][0][1]/(cov_nextday['cov'][0][0]**0.5*cov_nextday['cov'][1][1]**0.5),
                                  'mean_market' : mean_market, 'mean_bank' : mean_bank, 'alpha': vol.a, 'beta': vol.b, 'market_omega': vol.garch_params[0]['omega'],
                                                'market_alpha': vol.garch_params[0]['alpha'], 'market_beta': vol.garch_params[0]['beta'],'bank_omega': vol.garch_params[1]['omega'],
                                                'bank_alpha': vol.garch_params[1]['alpha'], 'bank_beta': vol.garch_params[1]['beta']}
                    market_returns_standardized_innovations.loc[dcc_garch_period + 1][bank_id] = (dcc_garch_returns.loc[dcc_garch_period + 1][bank_id]/current_dcc_garch_params['vola_bank_period_ahead'] -
                                                                                              current_dcc_garch_params['correlation_period_ahead']*dcc_garch_returns.loc[dcc_garch_period + 1]['market_return']/current_dcc_garch_params['vola_market_period_ahead']) \
                                                                                             /(1-current_dcc_garch_params['correlation_period_ahead']**2)**0.5
                    market_returns_standardized_innovations.loc[dcc_garch_period + 1][bank_id+'_vola_adjusted'] = dcc_garch_returns.loc[dcc_garch_period + 1][bank_id]/current_dcc_garch_params['vola_bank_period_ahead']
                    #gets written multiple times, take value with longest co-movement with any bank return
                    if (math.isnan(market_returns_standardized_innovations.loc[dcc_garch_period + 1]['market_return_window']) or market_returns_standardized_innovations.loc[dcc_garch_period + 1]['market_return_window'] <= len(dcc_garch_returns[:]['market_return'])):
                        market_returns_standardized_innovations.loc[dcc_garch_period + 1]['market_return'] = (dcc_garch_returns.loc[dcc_garch_period + 1]['market_return']
                                                                                            / current_dcc_garch_params['vola_market_period_ahead'])
                        market_returns_standardized_innovations.loc[dcc_garch_period + 1]['market_return_window'] = len(dcc_garch_returns[:]['market_return'])
                    dcc_garch_params.loc[dcc_garch_period][bank_id] = current_dcc_garch_params



        #%% calculation of LRMES via Monte Carlo
        lrmes_innovations = market_returns_standardized_innovations.dropna(axis=1, how='all')
        lrmes_innovations = lrmes_innovations.dropna(axis=0, how='all')

        bank_ids = [bank_key for bank_key in lrmes_innovations.keys()
                          if '_vola_adjusted' not in bank_key and 'market_return' not in bank_key]
        adjusted_return_columns = [bank_key for bank_key in lrmes_innovations.keys()
                          if '_vola_adjusted' in bank_key or 'market_return' in bank_key]
        innovation_return_columns = [bank_key for bank_key in lrmes_innovations.keys()
                                   if '_vola_adjusted' not in bank_key and 'window' not in bank_key]




        for period in range(srisk_calculation_start, len(equity_by_time)-2):

            #get one more, as last period still has an innovation but no garch parameters. Bank gets
            # dropped if last innovation is nan, i.e. when there are no garch parameters for that period.
            # drop extra period after removing nans to ensure we only use the innovation sequence up to time t
            current_innovation_sequence_and_adjusted_returns = \
                lrmes_innovations.loc[period - nperiods_rolling_window:period+1][:].astype(float)

            current_innovation_sequence = current_innovation_sequence_and_adjusted_returns[innovation_return_columns].dropna(axis=1, how='any')
            current_adjusted_returns = current_innovation_sequence_and_adjusted_returns[adjusted_return_columns].dropna(axis=1, how='any')

            #drop extra period here
            current_innovation_sequence = current_innovation_sequence[:-1][:]
            current_adjusted_returns = current_adjusted_returns[:-1][:]

            # all dcc garch parameters stored in each bank are the same for the market. Just chose first one
            dcc_garch_market = current_innovation_sequence.keys()[0]

            shortfall_samples = []

            full_sample_innovations = [random.choices(list(current_innovation_sequence.index), k=h) for sample in range(S)]

            #first only get market returns. Only calculate bank returns for those market movements that fulfill the capital shortfall condition
            for sample in range(S):

                innovations_s = current_innovation_sequence.loc[full_sample_innovations[sample]]
                innovations_s.index = ([x for x in range(h)])
                returns_sampleS = pd.DataFrame(index=range(h), columns=['market_return'])

                var_market_t = 0
                for sample_s_period_h in range(h):

                    epsilon_t_m1_market = innovations_s.loc[sample_s_period_h]['market_return']

                    if sample_s_period_h == 0:

                        sigma_market = dcc_garch_params.loc[period][dcc_garch_market]['vola_market_period_ahead']

                        # sigma_square_zero
                        var_market_t_m1 = sigma_market ** 2

                        var_market_t = dcc_garch_params.loc[period][dcc_garch_market]['market_omega'] + \
                                       dcc_garch_params.loc[period][dcc_garch_market]['market_beta'] * var_market_t_m1 + \
                                       dcc_garch_params.loc[period][dcc_garch_market]['market_alpha'] * (
                                                   epsilon_t_m1_market * sigma_market) ** 2

                    else:

                        var_market_t_m1 = var_market_t

                        sigma_market = var_market_t ** 0.5

                        var_market_t = dcc_garch_params.loc[period][dcc_garch_market]['market_omega'] + \
                                       dcc_garch_params.loc[period][dcc_garch_market]['market_beta'] * var_market_t_m1 + \
                                       dcc_garch_params.loc[period][dcc_garch_market]['market_alpha'] * (
                                                   epsilon_t_m1_market * sigma_market) ** 2

                    returns_sampleS.loc[sample_s_period_h]['market_return'] = epsilon_t_m1_market * sigma_market

                returns_sampleS[:]['market_return'] += dcc_garch_params.loc[period][dcc_garch_market]['mean_market']

                if np.exp(sum([market_ret for market_ret in returns_sampleS[:]['market_return']])) - 1 < c:
                    shortfall_samples.append(sample)

            srisk_bank_ids = [bank_id for bank_id in current_innovation_sequence if 'market' not in bank_id]
            full_period_return_sampleS = pd.DataFrame(index=shortfall_samples, columns=srisk_bank_ids)


            #Todo: make an error catch for the case where we do not have any shortfall samles
            if len(shortfall_samples) == 0:

                pass

            else:

                pass

            #sample = sample position in (1,S).
            #sample_counter = place of sample in shortfall_samples-array
            sample_counter = 0
            for sample in shortfall_samples:

                sample_shortfall_innovations = current_innovation_sequence.loc[full_sample_innovations[shortfall_samples[sample_counter]]]
                sample_shortfall_innovations.index = ([x for x in range(h)])
                sample_counter += 1

                for bank_id in srisk_bank_ids:

                    innovations_s = sample_shortfall_innovations[['market_return', bank_id]]
                    returns_sampleS = pd.DataFrame(index=range(h), columns=[bank_id])

                    Q_t = np.array([])
                    var_market_t = 0
                    var_bank_t = 0

                    for sample_s_period_h in range(h):

                        innov_market = innovations_s.loc[sample_s_period_h]['market_return']
                        innov_bank = innovations_s.loc[sample_s_period_h][bank_id]

                        S_i = current_adjusted_returns[[bank_id + '_vola_adjusted', 'market_return']].cov()

                        if sample_s_period_h == 0:

                            corr = dcc_garch_params.loc[period][bank_id]['correlation_period_ahead']
                            sigma_market = dcc_garch_params.loc[period][bank_id]['vola_market_period_ahead']
                            sigma_bank = dcc_garch_params.loc[period][bank_id]['vola_bank_period_ahead']

                            # DCC
                            # Q_zero
                            Q_t_m1 = np.array([[1, corr], [corr, 1]])

                            epsilon_t_m1_market = innov_market
                            epsilon_t_m1_bank = ((1 - corr ** 2) ** 0.5) * innov_bank + corr * innov_market

                            Q_t = (1 - dcc_garch_params.loc[period][bank_id]['alpha'] -
                                   dcc_garch_params.loc[period][bank_id]['beta']) * S_i \
                                  + dcc_garch_params.loc[period][bank_id]['alpha'] * np.matmul(
                                np.matrix([epsilon_t_m1_bank, epsilon_t_m1_market]).T,
                                np.matrix([epsilon_t_m1_bank, epsilon_t_m1_market])) \
                                  + dcc_garch_params.loc[period][bank_id]['beta'] * Q_t_m1

                            # GARCH
                            # sigma_square_zero
                            var_market_t_m1 = sigma_market ** 2
                            var_bank_t_m1 = sigma_bank ** 2

                            var_market_t = dcc_garch_params.loc[period][bank_id]['market_omega'] + \
                                           dcc_garch_params.loc[period][bank_id]['market_beta'] * var_market_t_m1 + \
                                           dcc_garch_params.loc[period][bank_id]['market_alpha'] * (
                                                       epsilon_t_m1_market * sigma_market) ** 2

                            var_bank_t = dcc_garch_params.loc[period][bank_id]['bank_omega'] + \
                                         dcc_garch_params.loc[period][bank_id]['bank_beta'] * var_bank_t_m1 + \
                                         dcc_garch_params.loc[period][bank_id]['bank_alpha'] * (
                                                     epsilon_t_m1_bank * sigma_bank) ** 2

                        else:

                            # DCC
                            Q_t_m1 = np.array(Q_t)

                            corr = Q_t_m1[0][1] / (Q_t_m1[0][0] * Q_t_m1[1][1])

                            epsilon_t_m1_market = innov_market
                            epsilon_t_m1_bank = ((1 - corr ** 2) ** 0.5) * innov_bank + Q_t_m1[0][1] * innov_market

                            Q_t = (1 - dcc_garch_params.loc[period][bank_id]['alpha'] -
                                   dcc_garch_params.loc[period][bank_id]['beta']) * S_i \
                                  + dcc_garch_params.loc[period][bank_id]['alpha'] * np.matmul(
                                np.matrix([epsilon_t_m1_bank, epsilon_t_m1_market]).T,
                                np.matrix([epsilon_t_m1_bank, epsilon_t_m1_market])) \
                                  + dcc_garch_params.loc[period][bank_id]['beta'] * Q_t_m1

                            # GARCH
                            var_market_t_m1 = var_market_t
                            var_bank_t_m1 = var_bank_t

                            sigma_market = var_market_t ** 0.5
                            sigma_bank = var_bank_t ** 0.5

                            var_market_t = dcc_garch_params.loc[period][bank_id]['market_omega'] + \
                                           dcc_garch_params.loc[period][bank_id]['market_beta'] * var_market_t_m1 + \
                                           dcc_garch_params.loc[period][bank_id]['market_alpha'] * (
                                                       epsilon_t_m1_market * sigma_market) ** 2

                            var_bank_t = dcc_garch_params.loc[period][bank_id]['bank_omega'] + \
                                         dcc_garch_params.loc[period][bank_id]['bank_beta'] * var_bank_t_m1 + \
                                         dcc_garch_params.loc[period][bank_id]['bank_alpha'] * (
                                                     epsilon_t_m1_bank * sigma_bank) ** 2

                        returns_sampleS.loc[sample_s_period_h][bank_id] = epsilon_t_m1_bank * sigma_bank

                    # add mean and reapply factor
                    returns_sampleS[:][bank_id] += dcc_garch_params.loc[period][bank_id]['mean_bank']

                    full_period_return_sampleS.loc[sample][bank_id] = np.exp(sum([bank_ret for bank_ret in returns_sampleS[:][bank_id]])) - 1

                    if np.exp(sum([bank_ret for bank_ret in returns_sampleS[:][bank_id]])) - 1 > 100 or np.exp(sum([bank_ret for bank_ret in returns_sampleS[:][bank_id]])) - 1 < -0.95:
                        print(np.exp(sum([bank_ret for bank_ret in returns_sampleS[:][bank_id]])) - 1)

            for bank_id in srisk_bank_ids:
                lrmes.loc[period][bank_id] = -np.mean(full_period_return_sampleS[bank_id])


    # simple bootstrap from empirical dist.
    else:

        for period in range(srisk_calculation_start, len(equity_by_time)-2):

            current_returns = market_returns[period-nperiods_rolling_window:period]
            current_returns = current_returns.dropna(axis=1)
            current_market_returns = current_returns['market_return']

            bootstrap_position = pd.DataFrame([random.choices(list(current_returns.index), k=h) for sample in range(S)])
            bootstrap_returns = pd.DataFrame([current_market_returns[row[1]].values.tolist() for row in bootstrap_position.iterrows()])
            bootstrap_returns_cumulated = bootstrap_returns.sum(axis=1)
            bootstrap_returns_cumulated = np.exp(bootstrap_returns_cumulated) - 1
            shortfall_boostrap_position = bootstrap_position[bootstrap_returns_cumulated < c]

            print(len(shortfall_boostrap_position))

            bank_ids = [bank_key for bank_key in current_returns.keys()
                        if 'market_return' not in bank_key]

            for bank_id in bank_ids:
                current_bank_returns = current_returns[bank_id]
                bootstrap_bank_returns = pd.DataFrame(
                    [current_bank_returns[row[1]].values.tolist() for row in shortfall_boostrap_position.iterrows()])
                bootstrap_bank_returns_cumulated = bootstrap_bank_returns.sum(axis=1)
                bootstrap_bank_returns_cumulated = np.exp(bootstrap_bank_returns_cumulated) - 1

                lrmes.loc[period][bank_id] = -np.mean(bootstrap_bank_returns_cumulated)

    end = time.time()
    print(f"SRISK calculation finished in {(end - start) / 60} minutes")

    #%% calculation of SRISK from equity, debt and LRMES
    for bank_id in equity_by_bank.keys():

        for period in range(srisk_calculation_start, len(equity_by_time)):
            if bank_equity.loc[period][bank_id] == 0:
                srisk.loc[period][bank_id] = 0
            else:
                srisk.loc[period][bank_id] = k*bank_debt.loc[period][bank_id]-(1-k)*bank_equity.loc[period][bank_id]*(1-lrmes.loc[period][bank_id])

    srisk_positive = copy.deepcopy(srisk)
    srisk_positive[srisk_positive<0] = 0
    srisk_positive[srisk_positive.isna()] = 0
    srisk_positive_aggregate = srisk_positive.sum(axis=1)
    srisk_positive_aggregate = srisk_positive_aggregate[srisk_positive_aggregate!=0]

    aggregate_assets = (bank_equity + bank_debt).sum(axis=1)
    aggregate_assets = aggregate_assets.loc[srisk_positive_aggregate.keys()]

    plt.plot(srisk_positive_aggregate/aggregate_assets, color='blue')
    plt.ylabel('Systemic risk in % of aggregate assets', color='blue')
    plt.tick_params(axis='y', labelcolor='blue')
    plt.title("Aggregate systemic risk")
    plt.axvline(x=275, color='r', label='shock')
    # plt.savefig(str(round(time.time()*1000))+'.pdf')
    plt.show()

    return srisk, lrmes

