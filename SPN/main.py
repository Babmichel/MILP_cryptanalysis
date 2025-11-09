from Cipher import SKINNY_parameters as cipher
from Key_schedule import SKINNY_key_schedule
from Model import MITM
import licence_parameters 
import attack_parameters
import gurobipy as gp


attack = MITM.MITM(cipher.cipher_parameters, 
                   licence_parameters.licence_parameters, 
                   attack_parameters.attack_parameters, None)
print(attack.model)
key_schedule = SKINNY_key_schedule.Model_MILP_SKINNY_key_schedule(cipher.cipher_parameters, 
                                                                 attack.total_rounds,
                                                                 attack.model)
attack.getdetails()

key_schedule.keyschedule()

attack.upper_subkey = key_schedule.upper_subkey
attack.lower_subkey = key_schedule.lower_subkey
attack.upper_key_guess = key_schedule.upper_key_guess
attack.lower_key_guess = key_schedule.lower_key_guess
attack.common_key_guess = key_schedule.common_key_guess

key_schedule.model.addConstrs((key_schedule.master_key[0, 0, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[0, 1, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[0, 2, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[0, 3, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[1, 0, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[1, 1, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[1, 2, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[1, 3, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[2, 0, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[2, 1, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[2, 2, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[2, 3, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[3, 0, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[3, 1, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[3, 2, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')
key_schedule.model.addConstrs((key_schedule.master_key[3, 3, value] == 1 for value in [1,2]),
                              name='master_key_fixed_values_from_attack')

attack.attack()

if attack.optimized:
    attack.display_console()
    attack.get_results()
    key_schedule.display_master_key()