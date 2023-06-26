def update_history(historic_bank_equity, banks, t):

    #update return dict

    updated_history = historic_bank_equity
    updated_history.update({t: {}})

    for bank_id in banks:
        updated_history[t].update({bank_id : banks[bank_id].equity})

    return updated_history