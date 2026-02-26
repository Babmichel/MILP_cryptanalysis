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

attack.upper_subkey = key_schedule.upper_subkey
attack.lower_subkey = key_schedule.lower_subkey
attack.upper_key_guess = key_schedule.upper_key_guess
attack.lower_key_guess = key_schedule.lower_key_guess
attack.common_key_guess = key_schedule.common_key_guess


attack.attack()

if attack.optimized:
    attack.display_console()
    attack.get_results()
    key_schedule.display_master_key()
