from Model import model_MILP_attack
from Cipher import SKINNY_parameters as cipher
from SPN.Model import MITM
from licence_parameters import *
from attack_parameters  import *

attack = MITM.Differential_MITM_fix_distinguisher(cipher.cipher_parameters, licence_parameters, attack_parameters)
attack.getdetails()
attack.part_initalisation()
attack.upper_part_value_propagation()
attack.lower_part_value_propagation()
attack.objective_function()
if attack.everything_all_right:
    attack.optimize()
    attack.getresults()
    attack.display_console()
