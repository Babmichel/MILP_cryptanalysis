#This file contains the MILP model to find Differential Meet in the middle attacks on SIMON like cipher
import numpy as np
import gurobipy as gp
from gurobipy import GRB
from itertools import product
import math
import csv

def differential_Meet_in_the_middle(user_parameters, licence):
        """Generate and solve the MILP model of the key recovery of Differential MITM attacks on SIMON like cipher
        for a given differential distinguisher. 
        Parameters
        ----------
        user_parameters : file.
                The file that contains the parameters of your attack

        licence : file.
                The file that contains the information of your gurobi licence

        Return
        ------
        feasibility : boolean
                1 if the  model is feasible, 0 if not
        If the mode is feasible : generate a 'solution.csv' file with all the variables of the model and their values
        If the model is not feasible : generate a 'model_infeasible.ilp' file with the constraints generating the infeasibility
        """

        options = {
                "WLSACCESSID" : licence["WLSACCESSID"],
                "WLSSECRET" : licence["WLSSECRET"],
                "LICENSEID" : licence["LICENSEID"]}

        with gp.Env(params=options) as env, gp.Model(env=env) as model:
                #---------------------------------------------------------------------------------------------------------------------------------------
                #Model Global Parameters
                #---------------------------------------------------------------------------------------------------------------------------------------

                #User parameters :
                block_size, key_size = user_parameters['block_size'], user_parameters['key_size']

                distinguisher_size, distinguisher_proba = user_parameters['distinguisher_size'], user_parameters['distinguisher_probability']

                active_input = user_parameters['distinguisher_active_input_bits']

                left_active_input, right_active_input =[], []

                for active_bit in active_input :
                        if active_bit < int(block_size/2):
                                left_active_input.append(active_bit)
                        else :
                                right_active_input.append(active_bit-int(block_size/2))

                active_output = user_parameters['distinguisher_active_output_bits']
                left_active_output, right_active_output = [], []

                for active_bit in active_output :
                        if active_bit < int(block_size/2):
                                left_active_output.append(active_bit)
                        else :
                                right_active_output.append(active_bit-int(block_size/2))

                structure_size, MITM_up_size, MITM_down_size = user_parameters['structure_size'], user_parameters['upper_part_size'], user_parameters['lower_part_size']

                dec_up, dec_mid, dec_down  = user_parameters['first_branch_shift'], user_parameters['second_branch_shift'], user_parameters['third_branch_shift']

                key_schedule_linearity = user_parameters['key_schedule_linearity']
                state_test, proba_key_rec = user_parameters['state_test'], user_parameters['state_test']

                # Parameters of the Gurobi model
                model.params.FeasibilityTol = 1e-9
                model.params.OptimalityTol = 1e-9
                model.setParam("OutputFlag", 1) 
                model.setParam("LogToConsole", 1)

                # Parameters for the model
                state_size = int(block_size/2)
                subkey_size = state_size
                distinguisher_probability = math.ceil(distinguisher_proba)
                total_round = structure_size + MITM_up_size + distinguisher_size + MITM_down_size

                #---------------------------------------------------------------------------------------------------------------------------------------
                ### Variable Creation ###
                #---------------------------------------------------------------------------------------------------------------------------------------

                #Key
                key = np.zeros([total_round, subkey_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know]
                key_structure = np.zeros([structure_size, subkey_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = lower part, 2=upper part]

                #structure
                structure_right1 = np.zeros([structure_size, state_size, 2, 3, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:lower part/upper part/both part, 0:know/1:unknow]
                structure_left1 = np.zeros([structure_size, state_size, 2, 3, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:lower part/upper part/both part, 0:know/1:unknow]
                structure_AND = np.zeros([structure_size, state_size, 2, 2, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:lower part/upper part, 0:know/1:unknow]
                structure_right2 = np.zeros([structure_size, state_size, 2, 2, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:lower part/upper part, 0:know/1:unknow]
                structure_left2 = np.zeros([structure_size, state_size, 2, 2, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:lower part/, 0:know/1:unknow]
                filtered_difference = np.zeros([state_size, 2], dtype = object)#[bit index, 0:left state/1:right state]
                fix_state = np.zeros([state_size, 2], dtype = object)#[bit index, 0:not filtered/1:filtered]

                #up_state
                up_left_state = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
                up_right_state = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know]
                up_left_state_mid = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
                up_left_state_up = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
                up_left_state_down = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
                up_state_test_or = np.zeros([MITM_up_size, state_size, 2], dtype = object)

                #up_differences
                up_left_difference = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
                up_right_difference = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
                up_left_difference_AND = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no differences, 1 = unknow differences, 2 = probabilistic annulation]
                up_left_difference_XOR = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
                up_right_difference_XOR = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
                up_var_for_right_XOR_1 = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value: 1 if 1+1]
                up_var_for_right_XOR_0 = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value: 0 if 0+0]

                #down_state
                down_left_state = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
                down_right_state = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know]
                down_left_state_mid = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
                down_left_state_up = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
                down_left_state_down = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
                down_state_test_or = np.zeros([MITM_down_size, state_size, 2], dtype = object)

                #down_differences
                down_left_difference = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
                down_right_difference = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
                down_left_difference_AND = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no differences, 1 = unknow differences, 2 = probabilistic annulation]
                down_left_difference_XOR = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
                down_right_difference_XOR = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
                down_var_for_right_XOR_1 = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value: 1 if 1+1]
                down_var_for_right_XOR_0 = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value: 0 if 0+0]

                #propagation of the pseudo-linear and non linear equations in the upper part
                up_left_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                up_right_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                up_AND_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                up_right2_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                up_AND1_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                up_AND2_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                up_AND1_statetest_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                up_AND2_statetest_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]

                down_left_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                down_right_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                down_AND_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                down_right2_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                down_AND_up_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                down_AND_mid_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                down_AND1_statetest_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
                down_AND2_statetest_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]

                #---------------------------------------------------------------------------------------------------------------------------------------
                ### MILP Variable initialisation ###
                #---------------------------------------------------------------------------------------------------------------------------------------

                #Variables needed to represent the key in the attack
                for round, bit, value in product(range(total_round), range(subkey_size), range(2)):
                        key[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'key_{round}_{bit}_{value}')

                #Variables needed to represent the filter state and diferences in the structure
                for  bit, value in product(range(state_size), range(2)):
                        filtered_difference[bit, value] = model.addVar(vtype = GRB.BINARY, name = f'filtered_difference_{bit}_{value}')
                        fix_state[bit, value] = model.addVar(vtype = GRB.BINARY, name = f'filtered_state_{bit}_{value}')

                #Variables needed to represent the key in the structure
                for round, bit, value in product(range(structure_size), range(subkey_size), range(3)):
                        key_structure[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'key_structure_{round}_{bit}_{value}')

                #Variables needed to represent the structure
                for round, bit, state_type, activity in  product(range(structure_size), range(state_size), range(2), range(2)):
                        for color in range(3):
                                structure_right1[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_right1_{round}_{bit}_{state_type}_{color}_{activity}')
                                structure_left1[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_left1_{round}_{bit}_{state_type}_{color}_{activity}')
                        for color in range(2):
                                structure_AND[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_AND_{round}_{bit}_{state_type}_{color}_{activity}')
                                structure_right2[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_right2_{round}_{bit}_{state_type}_{color}_{activity}')
                                structure_left2[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_left2_{round}_{bit}_{state_type}_{color}_{activity}')

                #Variables needed to represent the lower part of the attack
                for round, bit in product(range(MITM_down_size), range(state_size)): 
                        for value in range(3):
                                down_left_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_equation_{round}_{bit}_{value}')
                                down_right_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_right_equation_{round}_{bit}_{value}')
                                down_AND_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND_equation_{round}_{bit}_{value}')
                                down_right2_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_right2_equation_{round}_{bit}_{value}')
                                down_AND_up_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND_up_equation_{round}_{bit}_{value}')
                                down_AND_mid_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND_mid_equation_{round}_{bit}_{value}')
                                down_AND1_statetest_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND1_statetest_equation_{round}_{bit}_{value}')
                                down_AND2_statetest_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND2_statetest_equation_{round}_{bit}_{value}')
                                
                                down_right_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_right_difference_{round}_{bit}_{value}')
                                down_left_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_difference_{round}_{bit}_{value}')
                                down_left_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_difference_XOR_{round}_{bit}_{value}')
                                down_right_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_right_difference_XOR_{round}_{bit}_{value}')

                                down_left_difference_AND[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_difference_AND_{round}_{bit}_{value}')

                                down_left_state_up[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_up_{round}_{bit}_{value}')
                                down_left_state_mid[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_mid_{round}_{bit}_{value}')
                        
                        for value in range(2):
                                down_state_test_or[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_state_test_or_{round}_{bit}_{value}')
                                down_right_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_right_state_{round}_{bit}_{value}')
                                down_left_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_{round}_{bit}_{value}')
                                down_left_state_down[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_down_{round}_{bit}_{value}')
                                down_var_for_right_XOR_1[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_var_for_XOR_1_{round}_{bit}_{value}')
                                down_var_for_right_XOR_0[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_var_for_XOR_0_{round}_{bit}_{value}')

                #Variables needed to represent the upper part of the attack
                for round, bit in product(range(MITM_up_size), range(state_size)): 
                        for value in range(3):
                                up_left_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_equation_{round}_{bit}_{value}')
                                up_right_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_right_equation_{round}_{bit}_{value}')
                                up_AND_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND_equation_{round}_{bit}_{value}')
                                up_right2_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_right2_equation_{round}_{bit}_{value}')
                                up_AND1_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND1_equation_{round}_{bit}_{value}')
                                up_AND2_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND2_equation_{round}_{bit}_{value}')
                                up_AND1_statetest_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND1_statetest_equation_{round}_{bit}_{value}')
                                up_AND2_statetest_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND2_statetest_equation_{round}_{bit}_{value}')
                                
                                up_right_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_right_difference_{round}_{bit}_{value}')
                                up_left_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_difference_{round}_{bit}_{value}')
                                up_left_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_difference_XOR_{round}_{bit}_{value}')
                                up_right_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_right_difference_XOR_{round}_{bit}_{value}')

                                up_left_difference_AND[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_difference_AND_{round}_{bit}_{value}')

                                up_left_state_up[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_up_{round}_{bit}_{value}')
                                up_left_state_mid[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_mid_{round}_{bit}_{value}')
                        
                        for value in range(2):
                                up_state_test_or[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_state_test_or_{round}_{bit}_{value}')
                                up_right_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_right_state_{round}_{bit}_{value}')
                                up_left_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_{round}_{bit}_{value}')
                                up_left_state_down[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_down_{round}_{bit}_{value}')
                                up_var_for_right_XOR_1[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_var_for_XOR_1_{round}_{bit}_{value}')
                                up_var_for_right_XOR_0[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_var_for_XOR_0_{round}_{bit}_{value}')

                #Variables needed to compute the objective function 
                key_quantity_up = model.addVar(vtype= GRB.INTEGER, name = "key_quantity_up")
                key_quantity_down = model.addVar(vtype= GRB.INTEGER, name = "key_quantity_down")

                state_test_down_quantity = model.addVar(vtype= GRB.INTEGER, name = "state_test_down_quantity")
                state_test_up_quantity = model.addVar(vtype= GRB.INTEGER, name = "state_test_up_quantity")

                probabilistic_key_recovery_down = model.addVar(vtype= GRB.INTEGER, name = "probabilistic_key_recovery_down")
                probabilistic_key_recovery_up = model.addVar(vtype= GRB.INTEGER, name = "probabilistic_key_recovery_up")

                filtered_state_test_up = model.addVar(vtype= GRB.INTEGER, name = "filtered_state_test_up")
                filtered_state_test_down = model.addVar(vtype= GRB.INTEGER, name = "filtered_state_test_down")

                structure_fix = model.addVar(vtype= GRB.INTEGER, name = "structure_fix")
                structure_fix_first_round = model.addVar(vtype= GRB.INTEGER, name = "structure_fix_first_round")
                structure_match_differences = model.addVar(vtype= GRB.INTEGER, name = "structure_match_differences")

                total_key_information = model.addVar(vtype= GRB.INTEGER, name = "total_key_information")
                key_information = model.addVar(vtype= GRB.INTEGER, name = "key_information")

                time_complexity_up = model.addVar(vtype= GRB.INTEGER, name = "time_complexity_up")
                time_complexity_up = model.addVar(vtype= GRB.INTEGER, name = "time_complexity_up")
                time_complexity_up = model.addVar(vtype= GRB.INTEGER, name = "time_complexity_up")

                memory_complexity_up = model.addVar(vtype= GRB.INTEGER, name = "memory_complexity_up")
                memory_complexity_down = model.addVar(vtype= GRB.INTEGER, name = "memory_complexity_down")

                data_complexity = model.addVar(vtype= GRB.INTEGER, name = "data_complexity")

                # As we modelize the complexity as 2^x + 2^y 2^z, we cannot directly write it like this in MILP
                # We need to use a discret model, the following variables and constraints are used to build this discret model of the objective function 
                # However if the state is bigger than 120 bits we can no more use 2^x + 2^y 2^z, and sub optimize on the function : x + y + z
                complexity = model.addVar(vtype= GRB.CONTINUOUS, name = "complexity")
                m_complexity = model.addVar(vtype= GRB.CONTINUOUS, name = "m_complexity")
                memory_complexity_up = model.addVar(lb = state_size, ub = key_size,vtype= GRB.INTEGER, name = "memory_complexity_up")
                memory_complexity_down = model.addVar(lb = state_size, ub = key_size,vtype= GRB.INTEGER, name = "memory_complexity_down")

                if state_size<=60 :
                        time_complexity_up = model.addVar(lb = state_size, ub = 128,vtype= GRB.INTEGER, name = "time_complexity_up")
                        time_complexity_down = model.addVar(lb = state_size, ub = 128,vtype= GRB.INTEGER, name = "time_complexity_down")
                        time_complexity_match = model.addVar(lb = state_size, ub = 128,vtype= GRB.INTEGER, name = "time_complexity_match")

                else : 
                        time_complexity_up = model.addVar(lb = state_size, ub = state_size*2,vtype= GRB.INTEGER, name = "time_complexity_up")
                        time_complexity_down = model.addVar(lb = state_size, ub = state_size*2,vtype= GRB.INTEGER, name = "time_complexity_down")
                        time_complexity_match = model.addVar(lb = state_size, ub = state_size*2,vtype= GRB.INTEGER, name = "time_complexity_match")

                search_domain = range(int(state_size), int(128))

                binary_time_complexity_up = {i: model.addVar(vtype=GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in search_domain}
                binary_time_complexity_down = {i: model.addVar(vtype=GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in search_domain}
                binary_time_complexity_match = {i: model.addVar(vtype=GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in search_domain}
                binary_memory_complexity_up = {i: model.addVar(vtype=GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in search_domain}
                binary_memory_complexity_down = {i: model.addVar(vtype=GRB.BINARY, name=f"binary_time_complexity_up_{i}") for i in search_domain}

                #---------------------------------------------------------------------------------------------------------------------------------------
                #OBJECTIVE FUCNTION
                #---------------------------------------------------------------------------------------------------------------------------------------

                ### Variables used in the objective function 

                #Counting the key guessed in the attack 
                model.addConstr(key_quantity_up == gp.quicksum(key[round, bit, 1] for round, bit in product(range(structure_size, structure_size + MITM_up_size), range(state_size))) + gp.quicksum(key_structure[round, bit, 2] for round, bit in product(range(structure_size), range(state_size))), name="key_quantity_up_constraint")
                model.addConstr(key_quantity_down == gp.quicksum(key[round, bit, 1] for round, bit in product(range(structure_size + MITM_up_size + distinguisher_size, structure_size + MITM_up_size + distinguisher_size + MITM_down_size), range(state_size))) + gp.quicksum(key_structure[round, bit, 1] for round, bit in product(range(structure_size), range(state_size))), name="key_quantity_down_constraint")

                #counting the state test of the attack
                model.addConstr(state_test_down_quantity == gp.quicksum(down_state_test_or[round, bit, 1] for round in range(MITM_down_size) for bit in range(state_size)), name="state_test_down_quantity_constraint")
                model.addConstr(state_test_up_quantity == gp.quicksum(up_state_test_or[round, bit, 1] for round in range(MITM_up_size) for bit in range(state_size)), name="state_test_up_quantity_constraint")

                #counting the probabilist annulation of the attack
                model.addConstr(probabilistic_key_recovery_down == gp.quicksum(down_left_difference_AND[round, bit, 2] for round, bit in product(range(MITM_down_size), range(state_size))), name="probabilistic_key_recovery_down_constraint")      
                model.addConstr(probabilistic_key_recovery_up == gp.quicksum(up_left_difference_AND[round, bit, 2] for round, bit in product(range(MITM_up_size), range(state_size))), name="probabilistic_key_recovery_up_constraint")

                #counting the almost linear state test of the attack
                model.addConstr(filtered_state_test_up == gp.quicksum(up_state_test_or[round, bit, 1]*(1-up_left_equation[round, bit, 2]) for round, bit in product(range(MITM_up_size), range(state_size))), name="filtered_state_test_up_constraint")
                model.addConstr(filtered_state_test_down == gp.quicksum(down_state_test_or[round, bit, 1]*(1-down_right_equation[round, bit, 2]) for round, bit in product(range(MITM_down_size), range(state_size))), name="filtered_state_test_down_constraint")

                #Counting the filter trough the structure
                model.addConstr(structure_fix == gp.quicksum(fix_state[bit, value] for bit in range(state_size) for value in range(2)), name="structure_fix")
                model.addConstr(structure_fix_first_round == gp.quicksum(structure_right1[0, bit, 0, 1, 1] for bit in range(state_size))+gp.quicksum(structure_left1[0, bit, 0, 1, 1] for bit in range(state_size)), name="structure_fix_first_round")
                
                model.addConstr(structure_match_differences == gp.quicksum(filtered_difference[bit, value] for bit in range(state_size) for value in range(2)) - structure_fix, name="structure_match_differences")

                if key_schedule_linearity: #if the key schedule is linear we can filter the excessing key guess
                        model.addConstr(total_key_information == key_quantity_up + key_quantity_down + structure_match_differences + filtered_state_test_up + filtered_state_test_down - key_size, name="total_key_information")
                else :
                        model.addConstr(total_key_information == 0) #if the key schedule is not linear we cannot filter the excessing key guess and we need to ensure that we recover the full key after the attack
                        model.addConstr(key_information == key_quantity_up + key_quantity_down + structure_match_differences + filtered_state_test_up + filtered_state_test_down, name="total_key_information_constraint")
                        model.addConstr(key_information >= key_size, name="total_key_information>=key_size")

                model.addConstr(time_complexity_up ==  key_quantity_up + state_test_up_quantity + probabilistic_key_recovery_down, name="time_complexity_up_constraint")
                model.addConstr(time_complexity_down ==  key_quantity_down + state_test_down_quantity + probabilistic_key_recovery_up, name="time_complexity_down_constraint")
                model.addConstr(time_complexity_match ==  key_quantity_up + key_quantity_down + state_test_up_quantity + state_test_down_quantity + 2*state_size -2*structure_fix- structure_match_differences - total_key_information, name="time_complexity_match_constraint")

                model.addConstr(data_complexity >= distinguisher_proba + probabilistic_key_recovery_up + probabilistic_key_recovery_down)
                model.addConstr(data_complexity == state_size*2 - structure_fix_first_round)
                
                model.addConstr(memory_complexity_up == key_quantity_up + state_test_up_quantity - structure_fix, name="memory_complexity_up_constraints")
                model.addConstr(memory_complexity_down == key_quantity_down + state_test_down_quantity + (state_size-structure_fix), name="memory_complexity_down_constraints")

                if state_size <=60: # if state <120 we can use optimal function 2^x + 2^y 2^z
                        model.addConstr(time_complexity_up == gp.quicksum(i * binary_time_complexity_up[i] for i in search_domain), name="link between binary and integer complexity up")
                        model.addConstr(time_complexity_down == gp.quicksum(i * binary_time_complexity_down[i] for i in search_domain), name="link between binary and integer complexity down")
                        model.addConstr(time_complexity_match == gp.quicksum(i * binary_time_complexity_match[i] for i in search_domain), name="link between binary and integer complexity match")
                        model.addConstr(memory_complexity_up == gp.quicksum(i * binary_memory_complexity_up[i] for i in search_domain), name="link between binary and integer complexity match")
                        model.addConstr(memory_complexity_down == gp.quicksum(i * binary_memory_complexity_down[i] for i in search_domain), name="link between binary and integer complexity match")

                        model.addConstr(gp.quicksum(binary_time_complexity_up[i] for i in search_domain)==1, name="unique binary complexity up")
                        model.addConstr(gp.quicksum(binary_time_complexity_down[i] for i in search_domain)==1, name="unique binary complexity down")
                        model.addConstr(gp.quicksum(binary_time_complexity_match[i] for i in search_domain)==1, name="unique binary complexity match")
                        model.addConstr(gp.quicksum(binary_memory_complexity_up[i] for i in search_domain)==1, name="unique binary complexity match")
                        model.addConstr(gp.quicksum(binary_memory_complexity_down[i] for i in search_domain)==1, name="unique binary complexity match")

                        model.addConstr(complexity == gp.quicksum((2**i)*(binary_time_complexity_up[i] + binary_time_complexity_down[i] + binary_time_complexity_match[i]) for i in search_domain), name="time complexity")
                        model.addConstr(m_complexity <= gp.quicksum((2**i)*binary_memory_complexity_up[i] for i in search_domain), name="memory complexity up")
                        model.addConstr(m_complexity <= gp.quicksum((2**i)*binary_memory_complexity_down[i] for i in search_domain), name="memory complexity down")


                else : #sub optimal model x + y + z
                        model.addConstr(time_complexity_down <= complexity, name="suboptimal time complexity down")
                        model.addConstr(time_complexity_up <= complexity, name="suboptimal time complexity up")
                        model.addConstr(time_complexity_match <= complexity, name="suboptimal time complexity match")
                        model.addConstr(memory_complexity_up <= m_complexity, name="suboptimal m_complexity_up")
                        model.addConstr(memory_complexity_down <= m_complexity, name="suboptimal m_complexity down")

                        ### OBJECTIVE 
                model.setObjectiveN(complexity, 0, 10, abstol=1e-9, name='time complexity objective') #Minimize the time complexity

                model.setObjectiveN(m_complexity, 1, 8, abstol=1e-9, name='memory complexity objective') #Minimize the memory complexity

                model.setObjectiveN(data_complexity, 2, 9, abstol=1e-9, name='data complexity objective') #Minimize the data complexity

                # As we are not interest in doing a state that make us win only one key guess, 
                # we minimize the number of state test to ensure the model will not choose useless state test
                model.setObjectiveN(state_test_up_quantity+state_test_down_quantity,3, 5, name='min state test objective')

                
                #---------------------------------------------------------------------------------------------------------------------------------------
                ### MODEL'S CONSTRAINT
                #---------------------------------------------------------------------------------------------------------------------------------------

                #Global constraints
                model.addConstr(distinguisher_probability + probabilistic_key_recovery_down + probabilistic_key_recovery_up <= 2*state_size, "total probability of the attack cannot exceed the size of the state")

                model.addConstr(distinguisher_proba+probabilistic_key_recovery_up+probabilistic_key_recovery_down-(state_size*2-structure_fix) >=0)

                if not state_test : #constraints to avoid state test
                        model.addConstr(state_test_up_quantity == 0, name="State test limit")
                        model.addConstr(state_test_down_quantity == 0, name="State test limit")

                if not proba_key_rec : #constraints to avoid probabilist annulation
                        model.addConstr(probabilistic_key_recovery_up == 0, name = "probabilisitc key recovery limit")
                        model.addConstr(probabilistic_key_recovery_down == 0, name = "probabilisitc key recovery limit")

                #---------------------------------------------------------------------------------------------------------------------------------------
                ### STRUCTURE CONSTRAINTS ###
                #Structure is not considering the equivalent subkey techniques
                ### starting constraints
                for bit in range(state_size):
                        #states and differences are known by lower part at the start of the attack 
                        model.addConstr(structure_right1[0, bit, 0, 0, 1]==1, name = "values at the start of the structure are known by the lower part side")
                        model.addConstr(structure_left1[0, bit, 0, 0, 1]==1, name = "values at the start of the structure are known by the lower part side")
                        model.addConstr(structure_right1[0, bit, 1, 0, 1]==1, name = "differences at the end of the structure are known by the upper part side")
                        model.addConstr(structure_left1[0, bit, 1, 0, 1]==1, name = "differences at the end of the structure are known by the upper part side")

                        #states and differences are known by upper part at the end of the attack 
                        model.addConstr(structure_right2[structure_size-1, bit, 0, 1, 1]==1, name = "values at the end of the structure are known by the upper part side")
                        model.addConstr(structure_left2[structure_size-1, bit, 0, 1, 1]==1, name = "values at the end of the structure are known by the upper part side")
                        model.addConstr(structure_right2[structure_size-1, bit, 1, 1, 1]==1, name = "differences at the end of the structure are known by the upper part side")
                        model.addConstr(structure_left2[structure_size-1, bit, 1, 1, 1]==1, name = "differences at the end of the structure are known by the upper part side")

                ### Value propagation in a round 
                for round, bit in product(range(structure_size), range(state_size)):
                        #propagation of lower part values (forward propagation)
                        model.addConstr(structure_right2[round, bit, 0, 0, 1]==structure_left1[round, bit, 0, 0, 1], name="structure forward propagation of values inside a round")
                        model.addConstr(structure_left2[round, bit, 0, 0 ,1] == gp.and_([key_structure[round, bit, 1], structure_right1[round, bit, 0, 0, 1], structure_left1[round, (bit-dec_down)%state_size, 0, 0, 1], structure_left1[round, (bit-dec_mid)%state_size, 0, 0, 1], structure_left1[round, (bit-dec_up)%state_size, 0, 0, 1]]), name="structure forward propagation of values inside a round")
                        #propagation of upper part values (bacward propagation)
                        model.addConstr(structure_left1[round, bit, 0, 1, 1]==structure_right2[round, bit, 0, 1, 1], name="structure backward propagation of values inside a round")
                        model.addConstr(structure_right1[round, bit, 0, 1, 1]==gp.and_([key_structure[round, bit, 2], structure_left2[round, bit, 0, 1, 1], structure_right2[round, (bit-dec_down)%state_size, 0, 1, 1], structure_right2[round, (bit-dec_mid)%state_size, 0, 1, 1], structure_right2[round, (bit-dec_up)%state_size, 0, 1, 1]]), name="structure backward propagation of values inside a round")

                #State know by lower and upper part can be Fix, differences can be sieve
                for round, bit, state in product(range(structure_size), range(state_size), range(2)): 
                        model.addConstr(structure_left1[round, bit, state, 2, 1]==gp.and_(structure_left1[round, bit, state, 1, 1], structure_left1[round, bit, state, 0, 1]), name="structure Fix bit activity")
                        model.addConstr(structure_right1[round, bit, state, 2, 1]==gp.and_(structure_right1[round, bit, state, 1, 1], structure_right1[round, bit, state, 0, 1]), name="structure Fix bit activity")

                ###Difference propagation
                for round, bit in product(range(structure_size), range(state_size)):
                        #propagation of lower part differences (forward propagation)
                        model.addConstr(structure_AND[round, bit, 1, 0, 1]==gp.and_(structure_left1[round, (bit-dec_mid)%state_size, 0, 0, 1], structure_left1[round, (bit-dec_up)%state_size, 0, 0, 1]), name="structure forward propagation of differences through AND")
                        model.addConstr(structure_left2[round, bit, 1, 0, 1]==gp.and_([structure_left1[round, (bit-dec_down)%state_size, 1, 0, 1], structure_right1[round, bit, 1, 0, 1], structure_AND[round, bit, 1, 0, 1]]), name="structure forward propagation of differences through XOR")
                        model.addConstr(structure_right2[round, bit, 1, 0, 1]==structure_left1[round, bit, 1, 0, 1], name="structure forward propagation of differences through XOR")
                        #propagation of upper part differences (bacward propagation)
                        model.addConstr(structure_AND[round, bit, 1, 1, 1]==gp.and_(structure_left1[round, (bit-dec_mid)%state_size, 0, 1, 1], structure_left1[round, (bit-dec_up)%state_size, 0, 1, 1]), name="structure bacward propagation of differences through AND")
                        model.addConstr(structure_right1[round, bit, 1, 1, 1]==gp.and_([structure_left1[round, (bit-dec_down)%state_size, 1, 1, 1], structure_left2[round, bit, 1, 1, 1], structure_AND[round, bit, 1, 1, 1]]), name="structure backward propagation of differences through XOR")
                        model.addConstr(structure_right2[round, bit, 1, 1, 1]==structure_left1[round, bit, 1, 1, 1], name="structure backward propagation of differences through XOR")

                #lower part state and differences propagation to next rounds
                for round, bit, state, color in product(range(structure_size-1), range(state_size), range(2), range(2)):
                        model.addConstr(structure_left2[round, bit, state, color, 1]==structure_left1[round+1, bit, state, color, 1], name="forward propagation between round left2 = left1")
                        model.addConstr(structure_right2[round, bit, state, color, 1]==structure_right1[round+1, bit, state, color, 1], name="forward propagation between round right2 = right1")

                for bit in range(state_size):
                        model.addConstr(filtered_difference[bit, 0] == gp.or_([structure_left1[round, bit, 1, 2, 1] for round in range(0, structure_size, 2)],[structure_right1[round, bit, 1, 2, 1] for round in range(1, structure_size, 2)]), name = "difference match activity left state")    
                        model.addConstr(filtered_difference[bit, 1] == gp.or_([structure_right1[round, bit, 1, 2, 1] for round in range(0, structure_size, 2)],[structure_left1[round, bit, 1, 2, 1] for round in range(1, structure_size, 2)]), name = "difference match activity right state")    
                        model.addConstr(fix_state[bit, 0] == gp.or_([structure_left1[round, bit, 0, 2, 1] for round in range(0, structure_size, 2)],[structure_right1[round, bit, 0, 2, 1] for round in range(1, structure_size, 2)]), name ="Fix activity left state")    
                        model.addConstr(fix_state[bit, 1] == gp.or_([structure_right1[round, bit, 0, 2, 1] for round in range(0, structure_size, 2)],[structure_left1[round, bit, 0, 2, 1] for round in range(1, structure_size, 2)]), name="Fix activity right state")    

                #---------------------------------------------------------------------------------------------------------------------------------------
                ### KEY RECOVERY up ###
                #This part consider the equivalent subkey technique

                #Distinguisher input
                for bit in range(state_size):
                        if bit in right_active_input:
                                model.addConstr(up_right_difference[MITM_up_size-1, bit, 1] == 1, name = f"start disting 1 right ")
                        else :
                                model.addConstr(up_right_difference[MITM_up_size-1, bit, 0] == 1, name = f"start disting 0 right")
                        if bit in left_active_input:
                                model.addConstr(up_left_difference[MITM_up_size-1, bit, 1] == 1, name = f"start disting 1 left ")
                        else :
                                model.addConstr(up_left_difference[MITM_up_size-1, bit, 0] == 1, name = f"start disting 0 left")

                #difference backward propagation in a round
                for round, bit in product(range(MITM_up_size), range(state_size)):
                        #through AND
                        model.addConstr(up_left_difference_AND[round, bit, 0] == gp.and_(up_right_difference[round, (bit+dec_mid)%state_size, 0], up_right_difference[round, (bit+dec_up)%state_size, 0]), name = f"up AND")

                        #through XOR left 
                        model.addConstr(up_left_difference_XOR[round, bit, 2] == gp.or_(up_left_difference_AND[round, bit, 1], up_right_difference[round, (bit+dec_down)%state_size, 2]), name = f"up XOR left propagation of ?")
                        model.addConstr((up_right_difference[round, bit, 1] == 1) >> (up_left_difference_XOR[round, (bit-dec_down)%state_size, 0] == 0), name = f"up 1 => not 0")
                        model.addConstr((up_left_difference_XOR[round, (bit-dec_down)%state_size, 1] == 1) >> (up_right_difference[round, bit, 0] == 0), name = f"up not 0 <= 1")

                        #through XOR right
                        model.addConstr(up_right_difference_XOR[round, bit, 2] == gp.or_(up_left_difference[round, bit, 2], up_left_difference_XOR[round, bit, 2]), name = f"up XOR right propagation of ?")
                        model.addConstr(up_var_for_right_XOR_0[round, bit, 1] == gp.and_(up_left_difference_XOR[round, bit, 0], up_left_difference[round, bit, 0]), name = f"up var spe 0")
                        model.addConstr(up_var_for_right_XOR_1[round, bit, 1] == gp.and_(up_left_difference_XOR[round, bit, 1], up_left_difference[round, bit, 1]), name = f"up var spe 0")
                        model.addConstr(up_right_difference_XOR[round, bit, 0] == gp.or_(up_var_for_right_XOR_0[round, bit, 1], up_var_for_right_XOR_1[round, bit, 1]), name = f"up XOR right 0 form 0+0 or 1+1")

                #difference backward propagation between rounds
                for round, bit, value in product(range(1, MITM_up_size), range(state_size), range(3)):
                        model.addConstr(up_left_difference[round-1, bit, value] == up_right_difference[round, bit, value], name = f"up L-1 = R_XOR")
                        model.addConstr(up_right_difference[round-1, bit, value] == up_right_difference_XOR[round, bit, value], name = f"up R-1 = L")

                #link between Differential and State
                for round, bit in product(range(MITM_up_size), range(state_size)):
                        #if a difference is not null, state in this other branch is known or state tested
                        model.addConstr((up_right_difference[round, bit, 1] == 1) >> (up_left_state_mid[round, (bit-dec_up)%state_size, 0] == 0), name = f"up Link state-diff mid branch")
                        model.addConstr((up_right_difference[round, bit, 1] == 1) >> (up_left_state_up[round, (bit-dec_mid)%state_size, 0] == 0), name = f"up Link state-diff up branch")
                        model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_mid[round, (bit-dec_up)%state_size, 0] == 0), name = f"up Link state-diff mid branch")
                        model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_up[round, (bit-dec_mid)%state_size, 0] == 0), name = f"up Link state-diff up branch")
                        #state test can be perform only on known differences 
                        model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_mid[round, (bit-dec_mid)%state_size, 2] == 0), name = "no state test if unknow diff mid branch")
                        model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_up[round, (bit-dec_up)%state_size, 2] == 0), name = "no state test if unknow diff mid branch")

                #Forward State propagation in a round
                for round, bit in product(range(MITM_up_size), range(state_size)):
                        model.addConstr((up_left_state[round, bit, 1] == 1) >> (up_left_state_down[round, bit, 1] == 1), name = f"forward state propagation down branch")
                        model.addConstr((up_left_state[round, bit, 1] == 1) >> (up_left_state_up[round, bit, 1] == 1), name = f"forward state propagation up branch")
                        model.addConstr((up_left_state[round, bit, 1] == 1) >> (up_left_state_mid[round, bit, 1] == 1), name = f"forward state propagation mid branch")

                        model.addConstr((up_right_state[round, bit, 1] == 1) >> (up_left_state_mid[round, (bit-dec_mid)%state_size, 1]==1), name = f"forward state propagation mid branch")
                        model.addConstr((up_right_state[round, bit, 1] == 1) >> (up_left_state_down[round, (bit-dec_down)%state_size, 1]==1), name = f"forward state propagation down branch")
                        model.addConstr((up_right_state[round, bit, 1] == 1) >> (up_left_state_up[round, (bit-dec_up)%state_size, 1]==1), name = f"forward state propagation up branch")

                        #This constraints avoid doing the same state on the mid and up branch to be counted as two state test, but as one
                        model.addConstr(up_state_test_or[round, bit, 1] == gp.or_(up_left_state_up[round, (bit-dec_up)%state_size, 2], up_left_state_mid[round, (bit-dec_mid)%state_size, 2]), name="state_test_or_up")


                for round, bit in product(range(1,MITM_up_size), range(state_size)):
                        #Forward State propagation between round
                        model.addConstr((up_left_state_mid[round, bit, 1] == 1) >> (up_left_state[round-1, (bit+dec_mid)%state_size, 1] == 1), name = f"up state : L=R+1 <<1")
                        model.addConstr((up_left_state_down[round, bit, 1] == 1) >> (up_left_state[round-1, (bit+dec_down)%state_size, 1] == 1), name = f"up state : L=R+1 <<2")
                        model.addConstr((up_left_state_up[round, bit, 1] == 1) >> (up_left_state[round-1, (bit+dec_up)%state_size, 1] == 1), name = f"up state : L=R+1 <<8")
                        model.addConstr((up_left_state[round, bit, 1] == up_right_state[round-1, bit, 1]), name = f"up state : R=L-1")
                        #Key addition in a round (no key in the first round because of equivalent subkey technique)
                        model.addConstr((up_left_state_mid[round, bit, 1] == 1) >> (key[structure_size + round, (bit+dec_mid)%state_size, 1] == 1), name = f"up Key state implication <<1")
                        model.addConstr((up_left_state_up[round, bit, 1] == 1) >> (key[structure_size + round, (bit+dec_up)%state_size, 1] == 1), name = f"up Key state implication <<1")

                #---------------------------------------------------------------------------------------------------------------------------------------
                ### Key recovery DOWN ###
                #This part consider the equivalent subkey technique

                #Distinguisher output
                for bit in range(state_size):
                        if bit in left_active_output:
                                model.addConstr(down_left_difference[0, bit, 1] == 1, name = f"End disting 1 Left" )
                        else : 
                                model.addConstr(down_left_difference[0, bit, 0] == 1, name = f"End disting 0 Left")
                        if bit in right_active_output:
                                model.addConstr(down_right_difference[0, bit, 1] == 1, name = f"End disting 1 Right")
                        else : 
                                model.addConstr(down_right_difference[0, bit, 0] == 1, name = f"End disting 0 Right")

                #Differential forward propagation in a round
                for round, bit  in product(range(MITM_down_size), range(state_size)):
                        #AND rule : propagate a zero only if two zero, else propagate an unknow difference or a probabilistic annulation
                        model.addConstr(down_left_difference_AND[round, bit, 0] == gp.and_(down_left_difference[round, (bit+dec_up)%state_size, 0], down_left_difference[round, (bit+dec_mid)%state_size, 0]), name = f"AND rule")

                        #left_XOR : 0 only if two zeros, 1 only if 0 XOR 1, else case are necessarly unknown diff
                        model.addConstr(down_left_difference_XOR[round, bit, 2] == gp.or_(down_left_difference_AND[round, bit, 1], down_left_difference[round, (bit+dec_down)%state_size, 2]), name = f"Left XOR propagation of ?")
                        model.addConstr((down_left_difference[round, bit, 1] == 1) >> (down_left_difference_XOR[round, (bit-dec_down)%state_size, 0] == 0), name = f"Left XOR rule : 1 => not 0")
                        model.addConstr((down_left_difference_XOR[round, bit, 1] == 1) >> (down_left_difference[round, (bit+dec_down)%state_size, 0] == 0), name = f"Left XOR rule : not 0 <= 1")
                        
                        #right XOR : 0 if 0+0 or 1+1, 1 if 0+1 or 1+0, 2 in all the other case
                        model.addConstr(down_right_difference_XOR[round, bit, 2] == gp.or_(down_right_difference[round, bit, 2], down_left_difference_XOR[round, bit, 2]),name = f"Right XOR propagation of ?" )
                        model.addConstr(down_var_for_right_XOR_1[round, bit, 1] == gp.and_(down_left_difference_XOR[round, bit, 1], down_right_difference[round, bit, 1]),name = f"Difference forward propagation")
                        model.addConstr(down_var_for_right_XOR_0[round, bit, 1] == gp.and_(down_left_difference_XOR[round, bit, 0], down_right_difference[round, bit, 0]),name = f"Difference forward propagation" )
                        model.addConstr(down_right_difference_XOR[round, bit, 0] == gp.or_(down_var_for_right_XOR_0[round, bit, 1], down_var_for_right_XOR_1[round, bit, 1]),name = f"Difference forward propagation" )
                        
                #Differential forward propagation between rounds
                for round, bit, value in product(range(MITM_down_size-1), range(state_size), range(3)):
                        model.addConstr(down_left_difference[round, bit, value] == down_right_difference[round+1, bit, value], name = f"Diff L=R+1 ")
                        model.addConstr(down_right_difference_XOR[round, bit, value] == down_left_difference[round+1, bit, value], name = f"Diff R=L+1")

                #link between Differential and State
                for round, bit in product(range(MITM_down_size), range(state_size)):
                        #if a difference, state is known or state tested
                        model.addConstr((down_left_difference[round, bit, 1] == 1) >> (down_left_state_mid[round, (bit-dec_up)%state_size, 0] == 0), name = f"down Link state-diff <<1")
                        model.addConstr((down_left_difference[round, bit, 1] == 1) >> (down_left_state_up[round, (bit-dec_mid)%state_size, 0] == 0), name = f"down Link state-diff <<8")
                        model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_mid[round, (bit-dec_up)%state_size, 0] == 0), name = f"down Link state-diff <<1")
                        model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_up[round, (bit-dec_mid)%state_size, 0] == 0), name = f"down Link state-diff <<8")
                        #state test can be perform only on known differences 
                        model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_mid[round, (bit-dec_mid)%state_size, 2] == 0), name='state test perform only on known differences')
                        model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_up[round, (bit-dec_up)%state_size, 2] == 0), name='state test perform only on known differences')

                #State backward propagation inside a round
                for round, bit in product(range(MITM_down_size), range(state_size)):
                        model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state_mid[round, bit, 1] == 1), name = f"down state : right to left mid branch")
                        model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state_down[round, bit, 1] == 1), name = f"down state : right to left down branch")
                        model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state_up[round, bit, 1] == 1), name = f"down state : right to left up branch")

                        model.addConstr((down_left_state[round, bit, 1] == 1) >> (down_left_state_mid[round, (bit-dec_mid)%state_size, 1]==1), name = f"down left state propa mid branc")
                        model.addConstr((down_left_state[round, bit, 1] == 1) >> (down_left_state_down[round, (bit-dec_down)%state_size, 1]==1), name = f"down left state propa down branch")
                        model.addConstr((down_left_state[round, bit, 1] == 1) >> (down_left_state_up[round, (bit-dec_up)%state_size, 1]==1), name = f"down left state propa up branch")

                        #This constraints avoid doing the same state on the mid and up branch to be counted as two state test, but as one
                        model.addConstr(down_state_test_or[round, bit, 1] == gp.or_(down_left_state_up[round, (bit-dec_up)%state_size, 2], down_left_state_mid[round, (bit-dec_mid)%state_size, 2]), name="state_test_or_down")

                for round, bit in product(range(MITM_down_size-1), range(state_size)):
                        #State backward propagation between round
                        model.addConstr((down_left_state_mid[round, bit, 1] == 1) >> (down_right_state[round+1, (bit+dec_mid)%state_size, 1] == 1), name = f"down part state : L=R+1 mid branch")
                        model.addConstr((down_left_state_down[round, bit, 1] == 1) >> (down_right_state[round+1, (bit+dec_down)%state_size, 1] == 1), name = f"down part state : L=R+1 down branch")
                        model.addConstr((down_left_state_up[round, bit, 1] == 1) >> (down_right_state[round+1, (bit+dec_up)%state_size, 1] == 1), name = f"down part state : L=R+1 up branch")
                        model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state[round+1, bit, 1] == 1), name = f"down state : R=L+1")
                        #Key addition inside a round (not performed in the first round because of equivalent subkey technique)
                        model.addConstr((down_left_state_mid[round, bit, 1] == 1) >> (key[structure_size + MITM_up_size + distinguisher_size + round, (bit+dec_mid)%state_size, 1] == 1), name = f"down part Key state implication mid branch")
                        model.addConstr((down_left_state_up[round, bit, 1] == 1) >> (key[structure_size + MITM_up_size + distinguisher_size + round, (bit+dec_up)%state_size, 1] == 1), name = f"down part Key state implication up branch")

                #---------------------------------------------------------------------------------------------------------------------------------------
                ### Propagation of equations for the state test filtering ###

                ### up forward propagation

                #starting constraints : all the bit are linear
                for bit in range(state_size):
                        model.addConstr(up_left_equation[1, bit, 0]==1, name="Linear starting constraints")
                        model.addConstr(up_right_equation[1, bit, 0]==1, name="Linear starting constraints")

                #Forward propagation rules
                for round, bit in product(range(1, MITM_up_size), range(state_size)):
                        
                        model.addConstr(up_AND1_equation[round, bit, 0] == gp.and_(up_left_equation[round, (bit+dec_up)%state_size, 0], key[structure_size+round, (bit+dec_up)%state_size, 1]), name="linearity forward propagation rules 1")
                        model.addConstr(up_AND1_equation[round, bit, 2]==up_left_equation[round, (bit+dec_up)%state_size, 2], name="linearity forward propagation rules 2")

                        model.addConstr(up_AND1_statetest_equation[round, bit, 0]==gp.or_(up_AND1_equation[round, bit, 0], up_left_state_up[round, bit, 2]), name="linearity forward propagation rules 3")
                        model.addConstr((up_AND1_statetest_equation[round, bit, 1]==1)>>(up_AND1_equation[round, bit, 1]==1), name="linearity forward propagation rules 4")
                        model.addConstr((up_AND1_statetest_equation[round, bit, 2]==1)>>(up_AND1_equation[round, bit, 2]==1), name="linearity forward propagation rules 5")

                        model.addConstr(up_AND2_equation[round, bit, 0] == gp.and_(up_left_equation[round, (bit+dec_mid)%state_size, 0], key[structure_size+round, (bit+dec_mid)%state_size, 1]), name="linearity forward propagation rules 6")
                        model.addConstr(up_AND2_equation[round, bit, 2]==up_left_equation[round, (bit+dec_mid)%state_size, 2], name="linearity forward propagation rules 7")

                        model.addConstr(up_AND2_statetest_equation[round, bit, 0]==gp.or_(up_AND2_equation[round, bit, 0], up_left_state_mid[round, bit, 2]), name="linearity forward propagation rules 8")
                        model.addConstr((up_AND2_statetest_equation[round, bit, 1]==1)>>(up_AND2_equation[round, bit, 1]==1), name="linearity forward propagation rules 9")
                        model.addConstr((up_AND2_statetest_equation[round, bit, 2]==1)>>(up_AND2_equation[round, bit, 2]==1), name="linearity forward propagation rules 10")

                        model.addConstr((up_AND_equation[round, bit, 1] == 1) >> (up_AND1_statetest_equation[round, bit, 0] + up_AND2_statetest_equation[round, bit, 0] >=1), name="linearity forward propagation rules 11")

                        model.addConstr((up_AND_equation[round, bit, 2] == 1) >> (2*up_AND1_statetest_equation[round, bit, 2] + 2*up_AND2_statetest_equation[round, bit, 2] + up_AND1_statetest_equation[round, bit, 1] + up_AND2_statetest_equation[round, bit, 1] >=2), name="linearity forward propagation rules 12")
                        
                        model.addConstr((up_AND2_statetest_equation[round, bit, 2] == 1) >> (up_AND_equation[round, bit, 2] == 1), name="linearity forward propagation rules 13")
                        model.addConstr((up_AND1_statetest_equation[round, bit, 2] == 1) >> (up_AND_equation[round, bit, 2] == 1), name="linearity forward propagation rules 14")
                        
                        model.addConstr(up_AND_equation[round, bit, 0]==gp.and_(up_AND1_statetest_equation[round, bit, 0], up_AND2_statetest_equation[round, bit, 0]), name="linearity forward propagation rules 15")
                        
                        model.addConstr(up_right2_equation[round, bit, 2]==gp.or_(up_right_equation[round, bit, 2], up_left_equation[round, (bit+dec_down)%state_size, 2], up_AND_equation[round, bit, 2]), name="linearity forward propagation rules 16")
                        model.addConstr(up_right2_equation[round, bit, 0]==gp.and_(up_right_equation[round, bit, 0], up_left_equation[round, (bit+dec_down)%state_size, 0], up_AND_equation[round, bit, 0]), name="linearity forward propagation rules 17")

                #Forward propagation between rounds
                for round, bit, type_equation in product(range(1, MITM_up_size), range(state_size), range(3)):
                        model.addConstr(up_right_equation[round, bit, type_equation] == up_left_equation[round-1, bit, type_equation], name="forward propagation of linearity between rounds")
                        model.addConstr(up_left_equation[round, bit, type_equation] == up_right2_equation[round-1, bit, type_equation], name="forward propagation of linearity between rounds")

                ### down bacward propagation 

                #starting constraints
                for bit in range(state_size):
                        model.addConstr(down_left_equation[MITM_down_size-2, bit, 0]==1, name="linearity backward propagation rules 1")
                        model.addConstr(down_right_equation[MITM_down_size-2, bit, 0]==1, name="linearity backward propagation rules 2")

                #backward propagation rules
                for round, bit in product(range(MITM_down_size-1), range(state_size)):
                        model.addConstr(down_AND_up_equation[round, bit, 0] == gp.and_(down_right_equation[round, (bit+dec_up)%state_size, 0], key[structure_size+MITM_up_size+distinguisher_size+round, (bit+dec_up)%state_size, 1]), name="linearity backward propagation rules 3")
                        model.addConstr(down_AND_up_equation[round, bit, 2]==down_right_equation[round, (bit+dec_up)%state_size, 2], name="linearity backward propagation rules 4")

                        model.addConstr(down_AND1_statetest_equation[round, bit, 0]==gp.or_(down_AND_up_equation[round, bit, 0], down_left_state_up[round, bit, 2]), name="linearity backward propagation rules 5")
                        model.addConstr((down_AND1_statetest_equation[round, bit, 1]==1)>>(down_AND_up_equation[round, bit, 1]==1), name="linearity backward propagation rules 6")
                        model.addConstr((down_AND1_statetest_equation[round, bit, 2]==1)>>(down_AND_up_equation[round, bit, 2]==1), name="linearity backward propagation rules 7")

                        model.addConstr(down_AND_mid_equation[round, bit, 0] == gp.and_(down_right_equation[round, (bit+dec_mid)%state_size, 0], key[structure_size+MITM_up_size+distinguisher_size+round, (bit+dec_mid)%state_size, 1]), name="linearity backward propagation rules 8")
                        model.addConstr(down_AND_mid_equation[round, bit, 2]==down_right_equation[round, (bit+dec_mid)%state_size, 2], name="linearity backward propagation rules 9")

                        model.addConstr(down_AND2_statetest_equation[round, bit, 0]==gp.or_(down_AND_mid_equation[round, bit, 0], down_left_state_mid[round, bit, 2]), name="linearity backward propagation rules 10")
                        model.addConstr((down_AND2_statetest_equation[round, bit, 1]==1)>>(down_AND_mid_equation[round, bit, 1]==1), name="linearity backward propagation rules 11")
                        model.addConstr((down_AND2_statetest_equation[round, bit, 2]==1)>>(down_AND_mid_equation[round, bit, 2]==1), name="linearity backward propagation rules 12")
                        
                        model.addConstr(down_AND_equation[round, bit, 0]==gp.and_(down_AND1_statetest_equation[round, bit, 0], down_AND2_statetest_equation[round, bit, 0]), name="linearity backward propagation rules 13")
                        model.addConstr((down_AND2_statetest_equation[round, bit, 2] == 1) >> (down_AND_equation[round, bit, 2] == 1), name="linearity backward propagation rules 14")
                        
                        model.addConstr((down_AND1_statetest_equation[round, bit, 2] == 1) >> (down_AND_equation[round, bit, 2] == 1), name="linearity backward propagation rules 15")
                        model.addConstr((down_AND_equation[round, bit, 2] == 1) >> (2*down_AND1_statetest_equation[round, bit, 2] + 2*down_AND2_statetest_equation[round, bit, 2] + down_AND1_statetest_equation[round, bit, 1] + down_AND2_statetest_equation[round, bit, 1] >=2), name="linearity backward propagation rules 16")
                        
                        model.addConstr((down_AND_equation[round, bit, 1] == 1) >> (down_AND1_statetest_equation[round, bit, 0] + down_AND2_statetest_equation[round, bit, 0] >=1), name="linearity backward propagation rules 17")
                        model.addConstr(down_right2_equation[round, bit, 2]==gp.or_(down_left_equation[round, bit, 2], down_right_equation[round, (bit+dec_down)%state_size, 2], down_AND_equation[round, bit, 2]), name="linearity backward propagation rules 18")
                        model.addConstr(down_right2_equation[round, bit, 0]==gp.and_(down_left_equation[round, bit, 0], down_right_equation[round, (bit+dec_down)%state_size, 0], down_AND_equation[round, bit, 0]), name="linearity backward propagation rules 19")

                #Backward propagation between rounds
                for round, bit, type_equation in product(range(MITM_down_size-1), range(state_size), range(3)):
                        model.addConstr(down_right_equation[round, bit, type_equation] == down_right2_equation[round+1, bit, type_equation], name="backward propagation of linearity between rounds")
                        model.addConstr(down_left_equation[round, bit, type_equation] == down_right_equation[round+1, bit, type_equation], name="backward propagation of linearity between rounds")

                #---------------------------------------------------------------------------------------------------------------------------------------
                ### unique value constraints : thoose constraints ensure, for exemple, that the value of a state is no known an unknown at the same time ###
                for round, bit, state in product(range(structure_size), range(state_size), range(2)):
                        model.addConstr(gp.quicksum(key_structure[round, bit, key_color] for key_color in range(3)) == 1, name="unique key structure color")
                        for color in range(3):
                                model.addConstr(gp.quicksum(structure_left1[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_left1 color cannot be active and inactive")
                                model.addConstr(gp.quicksum(structure_right1[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_right1 cannot be active and inactive")
                        for color in range(2):
                                model.addConstr(gp.quicksum(structure_right2[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_right2 cannot be active and inactive")
                                model.addConstr(gp.quicksum(structure_AND[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_AND cannot be active and inactive")
                                model.addConstr(gp.quicksum(structure_left2[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_left2 cannot be active and inactive")

                for round, bit in product(range(MITM_down_size), range(state_size)):
                        model.addConstr(gp.quicksum(down_state_test_or[round, bit, value] for value in range(2))==1)
                        model.addConstr(gp.quicksum(down_left_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation left down')
                        model.addConstr(gp.quicksum(down_right_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation right down')
                        model.addConstr(gp.quicksum(down_right2_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation right2  down')
                        model.addConstr(gp.quicksum(down_AND_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND down')
                        model.addConstr(gp.quicksum(down_AND_up_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND1 down')
                        model.addConstr(gp.quicksum(down_AND_mid_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND2 down')   
                        model.addConstr(gp.quicksum(down_AND1_statetest_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND1 statetest down')
                        model.addConstr(gp.quicksum(down_AND2_statetest_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND2 statetest down')   
                        model.addConstr(gp.quicksum(down_left_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value down left difference")
                        model.addConstr(gp.quicksum(down_left_difference_AND[round, bit, value] for value in range(3)) == 1, name = f"unique value down left difference AND")
                        model.addConstr(gp.quicksum(down_left_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value down left difference XOR")
                        model.addConstr(gp.quicksum(down_right_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value down right difference XOR ")
                        model.addConstr(gp.quicksum(down_right_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value down right difference")
                        model.addConstr(gp.quicksum(down_left_state[round, bit, value] for value in range(2)) == 1, name = f"unique value down left state")
                        model.addConstr(gp.quicksum(down_left_state_mid[round, bit, value] for value in range(3)) == 1, name = f"unique value down left state")
                        model.addConstr(gp.quicksum(down_left_state_up[round, bit, value] for value in range(3)) == 1, name = f"unique value down left state")
                        model.addConstr(gp.quicksum(down_left_state_down[round, bit, value] for value in range(2)) == 1, name = f"unique value down left state")
                        model.addConstr(gp.quicksum(down_right_state[round, bit, value] for value in range(2)) == 1, name = f"unique value down right state")
                        model.addConstr(gp.quicksum(down_var_for_right_XOR_0[round, bit, value] for value in range(2)) == 1, name = f"unique value down_var_for_right_XOR_0")
                        model.addConstr(gp.quicksum(down_var_for_right_XOR_1[round, bit, value] for value in range(2)) == 1, name = f"unique value down_var_for_right_XOR_1")
                        
                for round, bit in product(range(MITM_up_size), range(state_size)):
                        model.addConstr(gp.quicksum(up_state_test_or[round, bit, value] for value in range(2))==1)
                        model.addConstr(gp.quicksum(up_left_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation left up')
                        model.addConstr(gp.quicksum(up_right_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation right up')
                        model.addConstr(gp.quicksum(up_right2_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation right2  up')
                        model.addConstr(gp.quicksum(up_AND_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND up')
                        model.addConstr(gp.quicksum(up_AND1_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND1 up')
                        model.addConstr(gp.quicksum(up_AND2_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND2 up')   
                        model.addConstr(gp.quicksum(up_AND1_statetest_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND1 statetest up')
                        model.addConstr(gp.quicksum(up_AND2_statetest_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND2 statetest up')   
                        model.addConstr(gp.quicksum(up_left_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value up left difference")
                        model.addConstr(gp.quicksum(up_left_difference_AND[round, bit, value] for value in range(3)) == 1, name = f"unique value up left difference AND")
                        model.addConstr(gp.quicksum(up_left_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value up left difference XOR")
                        model.addConstr(gp.quicksum(up_right_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value up right difference XOR ")
                        model.addConstr(gp.quicksum(up_right_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value up right difference")
                        model.addConstr(gp.quicksum(up_left_state[round, bit, value] for value in range(2)) == 1, name = f"unique value up left state")
                        model.addConstr(gp.quicksum(up_left_state_mid[round, bit, value] for value in range(3)) == 1, name = f"unique value up left state")
                        model.addConstr(gp.quicksum(up_left_state_up[round, bit, value] for value in range(3)) == 1, name = f"unique value up left state")
                        model.addConstr(gp.quicksum(up_left_state_down[round, bit, value] for value in range(2)) == 1, name = f"unique value up left state")
                        model.addConstr(gp.quicksum(up_right_state[round, bit, value] for value in range(2)) == 1, name = f"unique value up right state")
                        model.addConstr(gp.quicksum(up_var_for_right_XOR_0[round, bit, value] for value in range(2)) == 1, name = f"unique value up_var_for_right_XOR_0")
                        model.addConstr(gp.quicksum(up_var_for_right_XOR_1[round, bit, value] for value in range(2)) == 1, name = f"unique value up_var_for_right_XOR_1")
                        
                for round, bit in product(range(total_round), range(subkey_size)):
                        model.addConstr(gp.quicksum(key[round, bit, value] for value in range(2)) == 1, name=f"key unique value")
                #---------------------------------------------------------------------------------------------------------------------------------------
                #Constraints only for display
                display_constraint = gp.quicksum(up_left_state_mid[round, bit, 1] + up_left_state_up[round, bit, 1] + up_left_state[round, bit, 1] for round in range(MITM_up_size) for bit in range(state_size)) + gp.quicksum(down_left_state_mid[round, bit, 1] + down_left_state_up[round, bit, 1] + down_left_state[round, bit, 1] for round in range(MITM_down_size) for bit in range(state_size))
                model.setObjectiveN(-1*display_constraint, 4, 1)

                #---------------------------------------------------------------------------------------------------------------------------------------
                model.optimize()

                if model.Status != GRB.INFEASIBLE: 
                        with open("solution.csv", "w", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerow(["Variable", "Value"])
                                for v in model.getVars():
                                        writer.writerow([v.VarName, v.X])
                        return 1

                else : 
                        model.computeIIS()
                        model.write("model_infeasible.ilp")
                        return 0

                        
