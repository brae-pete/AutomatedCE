def get_float(msg: str, failed=False):
    """
    :param msg: message to display
    :param failed: flag if user has failed the question requirments
    :return : float number
    """
    if failed:
        print("Please enter a number")
    resp = input(msg + " ")
    if resp.replace('.', '').isnumeric():
        return float(resp)
    else:
        return get_float(msg, failed=True)


def get_int(msg: str, failed=False):
    """
    :param msg: message to display
    :param failed: flag if user has failed the question requirments
    :return : float number
    """
    if failed:
        print("Please enter a number")
    resp = input(msg + " ")
    if resp.isnumeric():
        return int(resp)
    else:
        return get_float(msg, failed=True)


def get_yes_no(msg: str, failed=False):
    """
    Asks user for Y/N response
    :return : True for Yes, False for No
    """
    if failed:
        print("Please enter y or n as you answer")
    resp = input(msg + " ")
    if resp.lower() == 'n':
        return False
    elif resp.lower() == 'y':
        return True
    else:
        return get_yes_no(msg, failed=True)


def get_value(msg: str, values: list, failed=False):
    if failed:
        print(f"Please select one of the following wells:")
        [print(x)]
    resp = input(msg)
    if resp not in values:
        return get_value(msg, values, True)
    else:
        return resp