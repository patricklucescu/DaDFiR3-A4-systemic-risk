import numpy as np
import mgarch
import pandas as pd
import random
import math

def calculate_SRISK(equity_by_time, equity_by_bank, debt_by_bank):

    #%% Variable initialization
    #conditional market shortfall
    c = -0.10
    #prudential capital fraction
    k = 0.08
    #h-period LRMES
    h = 10
    #number of Monte-Carlo simulations
    S = 1000

    srisk_calculation_start = 280
    nperiods_rolling_window = 30
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


    #%% construction of standardized innovations
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

    srisk_bank_ids = [bank_key for bank_key in lrmes_innovations.keys()
                      if '_vola_adjusted' not in bank_key and 'market_return' not in bank_key]

    counter = 1

    for bank_id in srisk_bank_ids:

        print(f'bank {counter} out of {len(srisk_bank_ids)}')
        counter += 1

        for period in range(srisk_calculation_start, len(equity_by_time)):

            #last period reached
            if not type(dcc_garch_params.loc[period][bank_id]) == dict:
                break

            current_innovation_sequence_and_adjusted_returns = lrmes_innovations.loc[period - nperiods_rolling_window:period][['market_return', bank_id, bank_id+'_vola_adjusted']]
            current_innovation_sequence_and_adjusted_returns = current_innovation_sequence_and_adjusted_returns.dropna(axis=0, how='any')
            current_innovation_sequence_and_adjusted_returns = current_innovation_sequence_and_adjusted_returns.astype(float)

            current_innovation_sequence = current_innovation_sequence_and_adjusted_returns[['market_return', bank_id]]
            current_adjusted_returns = current_innovation_sequence_and_adjusted_returns[['market_return', bank_id+'_vola_adjusted']]

            #if we have valid (i.e. long enough) sequence, calculate LRMES for that sequence
            if len(current_innovation_sequence[:][bank_id]) >= nperiods_rolling_window:

                full_period_return_sampleS = pd.DataFrame(columns=current_innovation_sequence.keys())

                for sample in range(S):

                    innovations_s = pd.DataFrame(current_innovation_sequence.loc[random.choices(list(current_innovation_sequence.index), k=h)].values,
                                                 index=range(h),columns=current_innovation_sequence.keys())
                    returns_sampleS = pd.DataFrame(index=range(h), columns=innovations_s.keys())

                    Q_t = np.array([])
                    var_market_t = 0
                    var_bank_t = 0

                    for sample_s_period_h in range(h):

                        innov_market = innovations_s.loc[sample_s_period_h]['market_return']
                        innov_bank = innovations_s.loc[sample_s_period_h][bank_id]

                        S_i = current_adjusted_returns[[bank_id+'_vola_adjusted', 'market_return']].cov()

                        if sample_s_period_h == 0:

                            corr = dcc_garch_params.loc[period][bank_id]['correlation_period_ahead']
                            sigma_market = dcc_garch_params.loc[period][bank_id]['vola_market_period_ahead']
                            sigma_bank = dcc_garch_params.loc[period][bank_id]['vola_bank_period_ahead']

                            #DCC
                            #Q_zero
                            Q_t_m1 = np.array([[1, corr],[corr, 1]])

                            epsilon_t_m1_market = innov_market
                            epsilon_t_m1_bank = ((1-corr**2)**0.5)*innov_bank + corr*innov_market

                            Q_t = (1 - dcc_garch_params.loc[period][bank_id]['alpha'] -
                                   dcc_garch_params.loc[period][bank_id]['beta']) * S_i \
                                  + dcc_garch_params.loc[period][bank_id]['alpha'] * np.matmul(
                                np.matrix([epsilon_t_m1_bank, epsilon_t_m1_market]).T, np.matrix([epsilon_t_m1_bank, epsilon_t_m1_market])) \
                                  + dcc_garch_params.loc[period][bank_id]['beta'] * Q_t_m1


                            #GARCH
                            #sigma_square_zero
                            var_market_t_m1 = sigma_market**2
                            var_bank_t_m1 = sigma_bank**2

                            var_market_t = dcc_garch_params.loc[period][bank_id]['market_omega'] + \
                                           dcc_garch_params.loc[period][bank_id]['market_beta'] * var_market_t_m1 + \
                                           dcc_garch_params.loc[period][bank_id]['market_alpha'] * (epsilon_t_m1_market * sigma_market) ** 2

                            var_bank_t = dcc_garch_params.loc[period][bank_id]['bank_omega'] + \
                                           dcc_garch_params.loc[period][bank_id]['bank_beta'] * var_bank_t_m1 + \
                                           dcc_garch_params.loc[period][bank_id]['bank_alpha'] * (epsilon_t_m1_bank * sigma_bank) ** 2

                        else:

                            # DCC
                            Q_t_m1 = np.array(Q_t)

                            corr = Q_t_m1[0][1]/(Q_t_m1[0][0]*Q_t_m1[1][1])

                            epsilon_t_m1_market = innov_market
                            epsilon_t_m1_bank = ((1-corr**2)**0.5)*innov_bank + Q_t_m1[0][1]*innov_market

                            Q_t = (1 - dcc_garch_params.loc[period][bank_id]['alpha'] -
                                   dcc_garch_params.loc[period][bank_id]['beta']) * S_i \
                                  + dcc_garch_params.loc[period][bank_id]['alpha'] * np.matmul(
                                np.matrix([epsilon_t_m1_bank, epsilon_t_m1_market]).T,
                                np.matrix([epsilon_t_m1_bank, epsilon_t_m1_market])) \
                                  + dcc_garch_params.loc[period][bank_id]['beta'] * Q_t_m1

                            # GARCH
                            var_market_t_m1 = var_market_t
                            var_bank_t_m1 = var_bank_t

                            sigma_market = var_market_t**0.5
                            sigma_bank = var_bank_t**0.5

                            var_market_t = dcc_garch_params.loc[period][bank_id]['market_omega'] + \
                                           dcc_garch_params.loc[period][bank_id]['market_beta'] * var_market_t_m1 + \
                                           dcc_garch_params.loc[period][bank_id]['market_alpha'] * (epsilon_t_m1_market * sigma_market) ** 2

                            var_bank_t = dcc_garch_params.loc[period][bank_id]['bank_omega'] + \
                                         dcc_garch_params.loc[period][bank_id]['bank_beta'] * var_bank_t_m1 + \
                                         dcc_garch_params.loc[period][bank_id]['bank_alpha'] * (epsilon_t_m1_bank * sigma_bank) ** 2

                        returns_sampleS.loc[sample_s_period_h]['market_return'] = epsilon_t_m1_market * sigma_market
                        returns_sampleS.loc[sample_s_period_h][bank_id] = epsilon_t_m1_bank * sigma_bank

                    #add mean and reapply factor
                    returns_sampleS[:]['market_return'] += dcc_garch_params.loc[period][bank_id]['mean_market']
                    returns_sampleS[:][bank_id] += dcc_garch_params.loc[period][bank_id]['mean_bank']

                    full_period_return_sampleS.loc[sample] = [np.exp(sum([market_ret for market_ret in returns_sampleS[:]['market_return']]))-1,
                                                              np.exp(sum([bank_ret for bank_ret in returns_sampleS[:][bank_id]]))-1]

                if len([bank_return for market_return, bank_return in np.array(full_period_return_sampleS) if market_return <= c ]) == 0:
                    lrmes.loc[period][bank_id] = 0
                else:
                    lrmes.loc[period][bank_id] = -np.mean([bank_return for market_return, bank_return in np.array(full_period_return_sampleS) if market_return <= c ])



    #%% calculation of SRISK from equity, debt and LRMES
    for bank_id in srisk_bank_ids:

        for period in range(srisk_calculation_start, len(equity_by_time)):

            srisk.loc[period][bank_id] = k*bank_debt.loc[period][bank_id]-(1-k)*bank_equity.loc[period][bank_id]*(1-lrmes.loc[period][bank_id])

    return srisk

