def update_history(historic_bank_equity: dict,
                   banks: dict,
                   t: float) -> dict:
    """
    | Updates the historic bank equity dictionary with the current time period

    :param historic_bank_equity: Historic bank equity dictionary
    :param banks: Current period banks
    :param t: Current period
    :return: Updated Historic bank equity dictionary
    """
    updated_history = historic_bank_equity
    updated_history.update({t: {}})
    for bank_id in banks:
        updated_history[t].update({bank_id : banks[bank_id].equity})
    return updated_history
