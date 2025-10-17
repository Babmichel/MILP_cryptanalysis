from differential_MITM import *
from SKINNY_parameters import *
from licence_parameters import *
from attack_parameters  import *

attack = Model_MILP_Differential_MITM(cipher_parameters, attack_parameters, licence_parameters)
attack.getdetails()
attack.part_initalisation()
attack.upper_part_value_propagation()
attack.objective_function()
attack.optimize()
attack.getresults()