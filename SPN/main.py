import sys
import importlib
cipher_name = sys.argv[1]  
file_number = sys.argv[2]
from sage.all import *

parameters = importlib.import_module(f"Attack_parameters.{cipher_name}_{file_number}")
cipher = importlib.import_module(f"Cipher.{parameters.attack_parameters.get('Cipher')}_parameters")
key_schedule = importlib.import_module(f"Key_schedule.{parameters.attack_parameters.get('Key_schedule')}_key_schedule")
attack_type = parameters.attack_parameters.get('attack_type')
attack_model = importlib.import_module(f"Model.{attack_type}")

import licence_parameters 
import gurobipy as gp


attack = attack_model.attack_model(cipher.cipher_parameters, 
                   licence_parameters.licence_parameters, 
                   parameters.attack_parameters, None)

key_schedule = key_schedule.Model_MILP_key_schedule(cipher.cipher_parameters, 
                                                                 attack.total_rounds,
                                                                 attack.model)

key_schedule.keyschedule()

if parameters.attack_parameters.get('specific_key_filtering'):
    attack.specific_key_filtering_quantity = key_schedule.key_filter

attack.upper_subkey = key_schedule.upper_subkey
attack.lower_subkey = key_schedule.lower_subkey
attack.upper_key_guess = key_schedule.upper_key_guess
attack.lower_key_guess = key_schedule.lower_key_guess
attack.common_key_guess = key_schedule.common_key_guess


""" key_schedule.model.addConstr(key_schedule.upper_subkey[4, 0, 1] == 0)
key_schedule.model.addConstr(key_schedule.upper_subkey[4, 0, 3] == 0)
key_schedule.model.addConstrs((key_schedule.upper_subkey[4, 1, c] == 0 for c in range(4)))
key_schedule.model.addConstrs((key_schedule.upper_subkey[5, r, c] == 0 for r in range(2) for c in range(4)))
key_schedule.model.addConstrs((key_schedule.upper_subkey[round_index, r, c] == 0 for round_index in range(5, attack.total_rounds) for r in range(2) for c in range(4)))

 """
attack.attack()

if attack.optimized:
    key_schedule.display_master_key()
    attack.display_console()
    attack.get_results()
    
