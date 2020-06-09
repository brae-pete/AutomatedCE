import os
from pathlib import Path

# Get the Home Directory Location
HOME = os.getcwd().split("AutomatedCE")[0] + "AutomatedCE"


def get_system_var(*var_names):
    """
    Get a variable from the system config file
    :param var_names: str
    :return:
    """
    # Get the Var file
    var_path = os.path.join(HOME, "config", "system_var.txt")
    with open(var_path) as fin:
        var_lines = fin.readlines()

    var_dict = {}

    for var_str in var_lines:
        var_list = var_str.split(',')
        var_dict[var_list[0]] = eval(var_list[1].replace('\n',''))

    response = []
    for var_name in var_names:
        assert var_name in var_dict.keys(), f"{var_name} is not a var in system_config.txt"
        response.append(var_dict[var_name])

    return response
