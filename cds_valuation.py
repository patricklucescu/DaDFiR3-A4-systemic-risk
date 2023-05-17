import numpy as np

def cds_valuation_continous(q, r, bond_ir, payment_dates, R, T, num_times):
    t_space = np.linspace(0.001,T, num_times)
    delta_t = t_space[1] - t_space[0]
    t_star_idx = [max(list(filter(lambda i: i < t, payment_dates))) for t in t_space]
    q_density = [q[t_idx] for t_idx in t_star_idx]
    interp_ir = [np.interp(t, payment_dates, r) for t in t_space]
    u = [np.sum(1 /(1 + r[:t_idx+1])) for t_idx in t_star_idx]
    e = [(t-payment_dates[t_idx]) / (1+ir_t) for t, t_idx, ir_t in zip(t_space, t_star_idx, interp_ir)]
    v = [1 / (1 +ir_t) for ir_t in interp_ir]
    A = [bond_ir * (t-t_idx) for t,t_idx in zip(t_space,t_star_idx)]
    
    pi = 1 - delta_t * sum(q_density)
    expected_pres_val_payments = delta_t * sum([q_density[i] * (u[i] + e[i]) for i in range(len(t_space))]) + pi * u[-1]
    expected_payoff = delta_t * sum([(1 - R - R * A[i]) * q_density[i] * v[i] for i in range(len(t_space))])

    return  expected_payoff / expected_pres_val_payments