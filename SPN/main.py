from Cipher import SKINNY_parameters as cipher
from Key_schedule import SKINNY_key_schedule
from Model import MITM
import licence_parameters 
import attack_parameters


attack = MITM.MITM(cipher.cipher_parameters, 
                   licence_parameters.licence_parameters, 
                   attack_parameters.attack_parameters)

key_schedule = SKINNY_key_schedule.Model_MILP_SKINNY_key_schedule(cipher.cipher_parameters, 
                                                                 attack.total_rounds,
                                                                 attack.model)
attack.getdetails()
key_schedule.keyschedule()
attack.attack()
if attack.everything_all_right:
    attack.optimize()
    attack.display_console()
