from Model import differential_MITM_fix_distinguisher, model_MILP_attack
from Cipher import SKINNY_parameters as cipher
from licence_parameters import *
from attack_parameters  import *

attack = differential_MITM_fix_distinguisher.Differential_MITM_fix_distinguisher(cipher.cipher_parameters, licence_parameters, attack_parameters)
attack.getdetails()
attack.part_initalisation()
attack.upper_part_value_propagation()
attack.lower_part_value_propagation()
attack.objective_function()
attack.optimize()
attack.getresults()
attack.affichage_console()
print(attack.mix_columns_inverse)