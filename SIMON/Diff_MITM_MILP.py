import numpy as np
import gurobipy as gp
from gurobipy import GRB
from itertools import product
import os
import shutil
import sys

def diff_mitm_SIMON():
    options = {
            "WLSACCESSID" : "05be6d4e-f7e5-48eb-930b-2b1a07381d82",
            "WLSSECRET" : "7af01c72-80a9-41c8-bc7f-a298baeed4f3",
            "LICENSEID" : 2534357 }
    
    with gp.Env(params=options) as env, gp.Model(env=env) as model:
        #SIMON parameters :
        print('Enter the size of the state  :')
        state_size = int(input())
        print('Enter the size of the key :')
        key_size = int(input())
        print('Enter the size of the differential distinguisher :')
        distinguisher_size = int(input())
        print('Enter the probability of the differential distinguisher :')
        distinguisher_probability = float(input())
        print('Enter the quantity of active bits at the start of the distinguisher :')
        distinguisher_input_quantity = int(input())
        left_active_input =[]
        right_active_input =[]
        for input_value in range(distinguisher_input_quantity) :
                print("Enter the index of an active bit you didn't enter before :")
                active_bit= int(input())
                if active_bit < int(state_size/2):
                        left_active_input.append(active_bit)
                else :
                        right_active_input.append(active_bit-int(state_size/2))

        print('Enter the quantity of active bits at the end of the distinguisher :')
        distinguisher_output_quantity = int(input())
        left_active_output =[]
        right_active_output =[]
        for input_value in range(distinguisher_output_quantity) :
                print("Enter the index of an active bit you didn't enter before :")
                active_bit= int(input())
                if active_bit < int(state_size/2):
                        left_active_output.append(active_bit)
                else :
                        right_active_output.append(active_bit-int(state_size/2))
        print('Enter the size of the structure :')
        structure_size = int(input())
        print('Enter the size of the upper part :')
        MITM_up_size = int(input())
        print('Enter the size of the lower part :')
        MITM_down_size = int(input())
        print('Do you want to use state-test, type 1 for yes, 0 for no')
        state_test = int(input())
        print('Do you want to use probabilistic-key recovery, type 1 for yes, 0 for no')
        proba_key_rec = int(input())
        
        state_size = int(state_size/2)
        subkey_size = state_size
        subkey_quantity = int(key_size/subkey_size)
        total_round = structure_size + MITM_up_size + distinguisher_size + MITM_down_size

        ### Variable Creation ###

        #Key
        key = np.zeros([total_round, subkey_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know]

        #up_state
        up_left_state = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]

        up_right_state = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know]

        up_left_state_1 = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]

        up_left_state_8 = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]

        up_left_state_2 = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]

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

        down_left_state_1 = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]

        down_left_state_8 = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]

        down_left_state_2 = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]

        #down_differences
        down_left_difference = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]

        down_right_difference = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]

        down_left_difference_AND = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no differences, 1 = unknow differences, 2 = probabilistic annulation]

        down_left_difference_XOR = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]

        down_right_difference_XOR = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]

        down_var_for_right_XOR_1 = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value: 1 if 1+1]
        down_var_for_right_XOR_0 = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value: 0 if 0+0]

        ### MILP Variable initialisation ###
        for round, bit, value in product(range(total_round), range(subkey_size), range(2)):
                key[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'key {round}, {bit} value ={value}')
     
        for round, bit in product(range(MITM_down_size), range(state_size)): 
                for value in range(3):
                        down_right_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_right difference {round}, {bit} : value = {value}')
                        down_left_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left difference {round}, {bit} : value = {value}')
                        down_left_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left difference_XOR {round}, {bit} : value = {value}')
                        down_right_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_right difference_XOR {round}, {bit} : value = {value}')

                        down_left_difference_AND[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left difference_AND {round}, {bit} : value = {value}')

                        down_left_state_8[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_8 {round}, {bit} : value = {value}')
                        down_left_state_1[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_1 {round}, {bit} : value = {value}')
                
                for value in range(2):
                        down_right_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_right state {round}, {bit} : value = {value}')
                        down_left_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state {round}, {bit} : value = {value}')
                        down_left_state_2[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_2 {round}, {bit} : value = {value}')
                        down_var_for_right_XOR_1[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_var_for_XOR_1 {round} {bit} {value}')
                        down_var_for_right_XOR_0[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_var_for_XOR_0 {round} {bit} {value}')
        
        for round, bit in product(range(MITM_up_size), range(state_size)): 
                for value in range(3):
                        up_right_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_right difference {round}, {bit} : value = {value}')
                        up_left_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left difference {round}, {bit} : value = {value}')
                        up_left_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left difference_XOR {round}, {bit} : value = {value}')
                        up_right_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_right difference_XOR {round}, {bit} : value = {value}')

                        up_left_difference_AND[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left difference_AND {round}, {bit} : value = {value}')

                        up_left_state_8[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_8 {round}, {bit} : value = {value}')
                        up_left_state_1[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_1 {round}, {bit} : value = {value}')
                
                for value in range(2):
                        up_right_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_right state {round}, {bit} : value = {value}')
                        up_left_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state {round}, {bit} : value = {value}')
                        up_left_state_2[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_2 {round}, {bit} : value = {value}')
                        up_var_for_right_XOR_1[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_var_for_XOR_1 {round} {bit} {value}')
                        up_var_for_right_XOR_0[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_var_for_XOR_0 {round} {bit} {value}')
        
        complexity = model.addVar(lb = 0.0, ub = 1.2*key_size,vtype= GRB.INTEGER, name = "complexite")
        complexity_up = model.addVar(lb = 0.0, ub = 1.2*key_size,vtype= GRB.INTEGER, name = "complexite")
        complexity_down = model.addVar(lb = 0.0, ub = 1.2*key_size,vtype= GRB.INTEGER, name = "complexite")
        complexity_match = model.addVar(lb = 0.0, ub = 1.2*key_size,vtype= GRB.INTEGER, name = "complexite")
        guess_match = model.addVar(lb = 0.0, ub = 1.2*key_size,vtype= GRB.INTEGER, name = "guess match")

        #Objective function
        key_quantity_up = gp.quicksum(key[round, bit, 1] for round, bit in product(range(structure_size, structure_size + MITM_up_size), range(state_size)))
        key_quantity_down = gp.quicksum(key[round, bit, 1] for round, bit in product(range(structure_size + MITM_up_size + distinguisher_size, structure_size + MITM_up_size + distinguisher_size + MITM_down_size), range(state_size)))
        state_test_down_quantity = gp.quicksum(down_left_state_1[round, bit, 2] for round, bit in product(range(MITM_down_size), range(state_size))) + gp.quicksum(down_left_state_8[round, bit, 2] for round, bit in product(range(MITM_down_size), range(state_size)))
        probabilistic_key_recovery_down = gp.quicksum(down_left_difference_AND[round, bit, 2] for round, bit in product(range(MITM_down_size), range(state_size)))        
        state_test_up_quantity = gp.quicksum(up_left_state_1[round, bit, 2] for round, bit in product(range(MITM_up_size), range(state_size))) + gp.quicksum(up_left_state_8[round, bit, 2] for round, bit in product(range(MITM_up_size), range(state_size)))
        probabilistic_key_recovery_up = gp.quicksum(up_left_difference_AND[round, bit, 2] for round, bit in product(range(MITM_up_size), range(state_size)))

        #model.addConstr(probabilistic_key_recovery_up == 1)
        if not state_test :
                model.addConstr(state_test_up_quantity == 0, name="State test limit")
                model.addConstr(state_test_down_quantity == 0, name="State test limit")

        if not proba_key_rec :
                model.addConstr(probabilistic_key_recovery_up == 0, name = "probabilisitc key recovery limit")
                model.addConstr(probabilistic_key_recovery_down == 0, name = "probabilisitc key recovery limit")

        
        if structure_size == 0:
                model.addConstr(key_quantity_up + key_quantity_down + state_test_down_quantity + state_test_up_quantity >= key_size)
                model.addConstr(key_quantity_up + state_test_up_quantity + probabilistic_key_recovery_down <= complexity)
                model.addConstr(key_quantity_up + state_test_up_quantity + probabilistic_key_recovery_down <= complexity_up)

                model.addConstr(key_quantity_down + state_test_down_quantity + probabilistic_key_recovery_up <= complexity)
                model.addConstr(key_quantity_down + state_test_down_quantity + probabilistic_key_recovery_up <= complexity_down)
        
                model.addConstr(key_quantity_up + key_quantity_down + state_test_up_quantity + state_test_down_quantity <= complexity)
                model.addConstr(key_quantity_up + key_quantity_down + state_test_up_quantity + state_test_down_quantity <= complexity_match)
        
        if structure_size == 1:
                model.addConstr(guess_match + state_size + key_quantity_up + key_quantity_down + state_test_down_quantity + state_test_up_quantity >= key_size)
                model.addConstr(key_quantity_up + state_test_up_quantity + probabilistic_key_recovery_down <= complexity)
                model.addConstr(key_quantity_up + state_test_up_quantity + probabilistic_key_recovery_down <= complexity_up)

                model.addConstr(key_quantity_down + state_test_down_quantity + probabilistic_key_recovery_up <= complexity)
                model.addConstr(key_quantity_down + state_test_down_quantity + probabilistic_key_recovery_up <= complexity_down)
        
                model.addConstr(guess_match + key_quantity_up + key_quantity_down + state_test_up_quantity + state_test_down_quantity - state_size <= complexity)
                model.addConstr(guess_match + key_quantity_up + key_quantity_down + state_test_up_quantity + state_test_down_quantity - state_size <= complexity_match)

        if structure_size == 2:
                model.addConstr(guess_match + 2*state_size + key_quantity_up + key_quantity_down + state_test_down_quantity + state_test_up_quantity >= key_size)
                model.addConstr(key_quantity_up + state_test_up_quantity + probabilistic_key_recovery_down <= complexity)
                model.addConstr(key_quantity_up + state_test_up_quantity + probabilistic_key_recovery_down <= complexity_up)

                model.addConstr(key_quantity_down + state_test_down_quantity + probabilistic_key_recovery_up <= complexity)
                model.addConstr(key_quantity_down + state_test_down_quantity + probabilistic_key_recovery_up <= complexity_down)
        
                model.addConstr(guess_match + key_quantity_up + key_quantity_down + state_test_up_quantity + state_test_down_quantity + state_size <= complexity)
                model.addConstr(guess_match + key_quantity_up + key_quantity_down + state_test_up_quantity + state_test_down_quantity + state_size <= complexity_match)

        model.addConstr(distinguisher_probability + probabilistic_key_recovery_down + probabilistic_key_recovery_up <= 2*state_size)

        model.setObjectiveN(complexity, 0, 100)
        model.setObjectiveN(complexity_up + complexity_down + complexity_match, 1, 75)
        model.setObjectiveN(state_test_down_quantity, 2, 25)
        model.setObjectiveN(state_test_up_quantity, 3, 25)
        
        #Constraints 
        

        ### KEY RECOVERY up ###

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

        for round, bit in product(range(MITM_up_size), range(state_size)):
                #AND
                model.addConstr(up_left_difference_AND[round, bit, 0] == gp.and_(up_right_difference[round, (bit+1)%state_size, 0], up_right_difference[round, (bit+8)%state_size, 0]), name = f"up AND")

                #XOR left 
                model.addConstr(up_left_difference_XOR[round, bit, 2] == gp.or_(up_left_difference_AND[round, bit, 1], up_right_difference[round, (bit+2)%state_size, 2]), name = f"up XOR left propagation of ?")
                model.addConstr((up_right_difference[round, bit, 1] == 1) >> (up_left_difference_XOR[round, (bit-2)%state_size, 0] == 0), name = f"up 1 => not 0")
                model.addConstr((up_left_difference_XOR[round, (bit-2)%state_size, 1] == 1) >> (up_right_difference[round, bit, 0] == 0), name = f"up not 0 <= 1")

                #XOR right
                model.addConstr(up_right_difference_XOR[round, bit, 2] == gp.or_(up_left_difference[round, bit, 2], up_left_difference_XOR[round, bit, 2]), name = f"up XOR right propagation of ?")
                model.addConstr(up_var_for_right_XOR_0[round, bit, 1] == gp.and_(up_left_difference_XOR[round, bit, 0], up_left_difference[round, bit, 0]), name = f"up var spe 0")
                model.addConstr(up_var_for_right_XOR_1[round, bit, 1] == gp.and_(up_left_difference_XOR[round, bit, 1], up_left_difference[round, bit, 1]), name = f"up var spe 0")
                model.addConstr(up_right_difference_XOR[round, bit, 0] == gp.or_(up_var_for_right_XOR_0[round, bit, 1], up_var_for_right_XOR_1[round, bit, 1]), name = f"up XOR right 0 form 0+0 or 1+1")

        for round, bit, value in product(range(1, MITM_up_size), range(state_size), range(3)):
                model.addConstr(up_left_difference[round-1, bit, value] == up_right_difference[round, bit, value], name = f"up L-1 = R_XOR")
                model.addConstr(up_right_difference[round-1, bit, value] == up_right_difference_XOR[round, bit, value], name = f"up R-1 = L")

        #link between Differential and State
        for round, bit in product(range(MITM_up_size), range(state_size)):
                #if a difference, state is known or state tested
                model.addConstr((up_right_difference[round, bit, 1] == 1) >> (up_left_state_1[round, (bit-8)%state_size, 0] == 0), name = f"up Link state-diff <<1")
                model.addConstr((up_right_difference[round, bit, 1] == 1) >> (up_left_state_8[round, (bit-1)%state_size, 0] == 0), name = f"up Link state-diff <<8")
                model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_1[round, (bit-8)%state_size, 0] == 0), name = f"up Link state-diff <<1")
                model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_8[round, (bit-1)%state_size, 0] == 0), name = f"up Link state-diff <<8")

        #State propagation
        for round, bit in product(range(MITM_up_size), range(state_size)):
                model.addConstr((up_left_state[round, bit, 1] == 1) >> (up_left_state_2[round, bit, 1] == 1), name = f"up Link state-diff <<2")
                model.addConstr((up_left_state[round, bit, 1] == 1) >> (up_left_state_8[round, bit, 1] == 1), name = f"up Link state-diff <<8")
                model.addConstr((up_left_state[round, bit, 1] == 1) >> (up_left_state_1[round, bit, 1] == 1), name = f"up Link state-diff <<1")

                model.addConstr((up_right_state[round, bit, 1] == 1) >> (up_left_state_1[round, (bit-1)%state_size, 1]==1), name = f"up left state propa << 1 ")
                model.addConstr((up_right_state[round, bit, 1] == 1) >> (up_left_state_2[round, (bit-2)%state_size, 1]==1), name = f"up left state propa << 2 ")
                model.addConstr((up_right_state[round, bit, 1] == 1) >> (up_left_state_8[round, (bit-8)%state_size, 1]==1), name = f"up left state propa << 8 ")

        for round, bit in product(range(1,MITM_up_size), range(state_size)):
                #propagation to next round
                model.addConstr((up_left_state_1[round, bit, 1] == 1) >> (up_left_state[round-1, (bit+1)%state_size, 1] == 1), name = f"up state : L=R+1 <<1")
                model.addConstr((up_left_state_2[round, bit, 1] == 1) >> (up_left_state[round-1, (bit+2)%state_size, 1] == 1), name = f"up state : L=R+1 <<2")
                model.addConstr((up_left_state_8[round, bit, 1] == 1) >> (up_left_state[round-1, (bit+8)%state_size, 1] == 1), name = f"up state : L=R+1 <<8")
                model.addConstr((up_left_state[round, bit, 1] == up_right_state[round-1, bit, 1]), name = f"up state : R=L-1")
                #Key addition
                model.addConstr((up_left_state_1[round, bit, 1] == 1) >> (key[structure_size + round, (bit+1)%state_size, 1] == 1), name = f"up Key state implication <<1")
                model.addConstr((up_left_state_8[round, bit, 1] == 1) >> (key[structure_size + round, (bit+8)%state_size, 1] == 1), name = f"up Key state implication <<1")

        ### Key recovery DOWN ###

        #Distinguisher output
        for bit in range(state_size):
                if bit in left_active_output:
                        model.addConstr(down_left_difference[0, bit, 1] == 1, name = f"End disting 1 Left" )
                else : 
                        model.addConstr(down_left_difference[0, bit, 0] == 1, name = f"End disting 0 Left")
                if bit in right_active_output:
                        model.addConstr(down_right_difference[0, bit, 1] == 1, name = f"End disting 0 Right")
                else : 
                        model.addConstr(down_right_difference[0, bit, 0] == 1, name = f"End disting 0 Right")

        #Differential propagation
        for round, bit  in product(range(MITM_down_size), range(state_size)):
                #AND rule : propagate a zero only if two zero, else propagate an unknow difference or a probabilistic annulation
                model.addConstr(down_left_difference_AND[round, bit, 0] == gp.and_(down_left_difference[round, (bit+8)%state_size, 0], down_left_difference[round, (bit+1)%state_size, 0]), name = f"AND rule")

                #left_XOR : 0 only if two zeros, 1 only if 0 XOR 1, else case are necessarly unknown diff
                model.addConstr(down_left_difference_XOR[round, bit, 2] == gp.or_(down_left_difference_AND[round, bit, 1], down_left_difference[round, (bit+2)%state_size, 2]), name = f"Left XOR propagation of ?")
                model.addConstr((down_left_difference[round, bit, 1] == 1) >> (down_left_difference_XOR[round, (bit-2)%state_size, 0] == 0), name = f"Left XOR rule : 1 => not 0")
                model.addConstr((down_left_difference_XOR[round, bit, 1] == 1) >> (down_left_difference[round, (bit+2)%state_size, 0] == 0), name = f"Left XOR rule : not 0 <= 1")
                #model.addConstr(down_left_difference_XOR[round, bit, 0] == gp.and_(down_left_difference[round, (bit+2)%state_size, 0], down_left_difference_AND[round, bit, 1]), name = f"Left XOR rule : 0+0 => 0")
        
                #right XOR : 0 if 0+0 or 1+1, 1 if 0+1 or 1+0, 2 in all the other case
                model.addConstr(down_right_difference_XOR[round, bit, 2] == gp.or_(down_right_difference[round, bit, 2], down_left_difference_XOR[round, bit, 2]),name = f"Right XOR propagation of ?" )
 
                model.addConstr(down_var_for_right_XOR_1[round, bit, 1] == gp.and_(down_left_difference_XOR[round, bit, 1], down_right_difference[round, bit, 1]))
                
                model.addConstr(down_var_for_right_XOR_0[round, bit, 1] == gp.and_(down_left_difference_XOR[round, bit, 0], down_right_difference[round, bit, 0]))

                model.addConstr(down_right_difference_XOR[round, bit, 0] == gp.or_(down_var_for_right_XOR_0[round, bit, 1], down_var_for_right_XOR_1[round, bit, 1]))
                
        
        for round, bit, value in product(range(MITM_down_size-1), range(state_size), range(3)):
               model.addConstr(down_left_difference[round, bit, value] == down_right_difference[round+1, bit, value], name = f"Diff L=R+1 ")
               model.addConstr(down_right_difference_XOR[round, bit, value] == down_left_difference[round+1, bit, value], name = f"Diff R=L+1")
        
        #link between Differential and State
        for round, bit in product(range(MITM_down_size), range(state_size)):
                #if a difference, state is known or state tested
                model.addConstr((down_left_difference[round, bit, 1] == 1) >> (down_left_state_1[round, (bit-8)%state_size, 0] == 0), name = f"down Link state-diff <<1")
                model.addConstr((down_left_difference[round, bit, 1] == 1) >> (down_left_state_8[round, (bit-1)%state_size, 0] == 0), name = f"down Link state-diff <<8")
                model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_1[round, (bit-8)%state_size, 0] == 0), name = f"down Link state-diff <<1")
                model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_8[round, (bit-1)%state_size, 0] == 0), name = f"down Link state-diff <<8")

        #State propagation
        for round, bit in product(range(MITM_down_size), range(state_size)):
                model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state_1[round, bit, 1] == 1), name = f"down state : right to left <<1")
                model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state_2[round, bit, 1] == 1), name = f"down state : right to left <<2")
                model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state_8[round, bit, 1] == 1), name = f"down state : right to left <<8")

                model.addConstr((down_left_state[round, bit, 1] == 1) >> (down_left_state_1[round, (bit-1)%state_size, 1]==1), name = f"down left state propa << 1 ")
                model.addConstr((down_left_state[round, bit, 1] == 1) >> (down_left_state_2[round, (bit-2)%state_size, 1]==1), name = f"down left state propa << 2 ")
                model.addConstr((down_left_state[round, bit, 1] == 1) >> (down_left_state_8[round, (bit-8)%state_size, 1]==1), name = f"down left state propa << 8 ")

        for round, bit in product(range(MITM_down_size-1), range(state_size)):
                #propagation to next round
                model.addConstr((down_left_state_1[round, bit, 1] == 1) >> (down_right_state[round+1, (bit+1)%state_size, 1] == 1), name = f"down state : L=R+1 <<1")
                model.addConstr((down_left_state_2[round, bit, 1] == 1) >> (down_right_state[round+1, (bit+2)%state_size, 1] == 1), name = f"down state : L=R+1 <<2")
                model.addConstr((down_left_state_8[round, bit, 1] == 1) >> (down_right_state[round+1, (bit+8)%state_size, 1] == 1), name = f"down state : L=R+1 <<8")
                model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state[round+1, bit, 1] == 1), name = f"down state : R=L+1")
                #Key addition
                model.addConstr((down_left_state_1[round, bit, 1] == 1) >> (key[structure_size + MITM_up_size + distinguisher_size + round, (bit+1)%state_size, 1] == 1), name = f"down Key state implication <<1")
                model.addConstr((down_left_state_8[round, bit, 1] == 1) >> (key[structure_size + MITM_up_size + distinguisher_size + round, (bit+8)%state_size, 1] == 1), name = f"down Key state implication <<1")

        #unique value
        for round, bit in product(range(MITM_down_size), range(state_size)):
                model.addConstr(gp.quicksum(down_left_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value down left difference")
                model.addConstr(gp.quicksum(down_left_difference_AND[round, bit, value] for value in range(3)) == 1, name = f"unique value down left difference AND")
                model.addConstr(gp.quicksum(down_left_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value down left difference XOR")
                model.addConstr(gp.quicksum(down_right_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value down right difference XOR ")
                model.addConstr(gp.quicksum(down_right_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value down right difference")
                model.addConstr(gp.quicksum(down_left_state[round, bit, value] for value in range(2)) == 1, name = f"unique value down left state")
                model.addConstr(gp.quicksum(down_left_state_1[round, bit, value] for value in range(3)) == 1, name = f"unique value down left state")
                model.addConstr(gp.quicksum(down_left_state_8[round, bit, value] for value in range(3)) == 1, name = f"unique value down left state")
                model.addConstr(gp.quicksum(down_left_state_2[round, bit, value] for value in range(2)) == 1, name = f"unique value down left state")
                model.addConstr(gp.quicksum(down_right_state[round, bit, value] for value in range(2)) == 1, name = f"unique value down right state")
        for round, bit in product(range(MITM_up_size), range(state_size)):
                model.addConstr(gp.quicksum(up_left_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value up left difference")
                model.addConstr(gp.quicksum(up_left_difference_AND[round, bit, value] for value in range(3)) == 1, name = f"unique value up left difference AND")
                model.addConstr(gp.quicksum(up_left_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value up left difference XOR")
                model.addConstr(gp.quicksum(up_right_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value up right difference XOR ")
                model.addConstr(gp.quicksum(up_right_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value up right difference")
                model.addConstr(gp.quicksum(up_left_state[round, bit, value] for value in range(2)) == 1, name = f"unique value up left state")
                model.addConstr(gp.quicksum(up_left_state_1[round, bit, value] for value in range(3)) == 1, name = f"unique value up left state")
                model.addConstr(gp.quicksum(up_left_state_8[round, bit, value] for value in range(3)) == 1, name = f"unique value up left state")
                model.addConstr(gp.quicksum(up_left_state_2[round, bit, value] for value in range(2)) == 1, name = f"unique value up left state")
                model.addConstr(gp.quicksum(up_right_state[round, bit, value] for value in range(2)) == 1, name = f"unique value up right state")
        for round, bit in product(range(total_round), range(subkey_size)):
                model.addConstr(gp.quicksum(key[round, bit, value] for value in range(2)) == 1, name=f"key unique value")

        model.optimize()

        if model.Status != GRB.INFEASIBLE:
                print("Best key recovery path found :")
                for round in range(MITM_up_size):
                        print(f"\033[90m ROUND : {structure_size + round}")
                        for bit in range(state_size):
                                if key[structure_size + round, (bit-8)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + round, (bit-8)%state_size, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_8")
                        for bit in range(state_size):
                                couleur = 1*int(up_left_state_8[round, bit, 1].X) + 7*int(up_left_state_8[round, bit, 2].X)
                                if up_right_difference[round, (bit+8)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_right_difference[round, (bit+8)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_right_difference[round, (bit+8)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("\033[90m||", end="")
                        print("\033[90m L_8     ", end="")
                        for bit in range(state_size):
                                if key[structure_size + round, bit, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + round, bit, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K")
                        for bit in range(state_size):
                                if key[structure_size + round, (bit+1)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + round, (bit+1)%state_size, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_1")
                        for bit in range(state_size):
                                couleur = 1*int(up_left_state_1[round, bit, 1].X) + 7*int(up_left_state_1[round, bit, 2].X)
                                if up_right_difference[round, (bit+1)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_right_difference[round, (bit+1)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_right_difference[round, (bit+1)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("\033[90m||", end="")
                        print("\033[90m L_1     ", end="")
                        for bit in range(state_size):
                                couleur = 1*int(up_right_state[round, bit, 1].X)
                                if up_left_difference_AND[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_left_difference_AND[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if up_left_difference_AND[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m P ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_AND")
                        for bit in range(state_size):
                                couleur = 1*int(up_left_state_2[round, bit, 1].X)
                                if up_right_difference[round, (bit+2)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_right_difference[round, (bit+2)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_right_difference[round, (bit+2)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_2     ", end="")
                        for bit in range(state_size):
                                couleur = 1*int(up_right_state[round, bit, 1].X)
                                if up_left_difference_XOR[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_left_difference_XOR[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_left_difference_XOR[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_XOR")
                        for bit in range(state_size):
                                couleur = 1*int(up_left_state[round, bit, 1].X)
                                if up_left_difference[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_left_difference[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_left_difference[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L       ", end="")
                        for bit in range(state_size):
                                couleur = 1*int(up_right_state[round, bit, 1].X)
                                if up_right_difference[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_right_difference[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_right_difference[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if bit in [3, 7, 11]:
                                        print ("||", end="")
                        print("\033[90m R")
                print("")
                print("################################################### DISTINGUISHER ###########################################################")
                print("")
                for round in range(MITM_down_size):
                        print(f"\033[90m ROUND : {structure_size + MITM_up_size + distinguisher_size + round}")
                        for bit in range(state_size):
                                couleur = 4*int(down_left_state[round, bit, 1].X)
                                if down_left_difference[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L       ", end="")
                        for bit in range(state_size):
                                couleur = 4*int(down_right_state[round, bit, 1].X)
                                if down_right_difference[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_right_difference[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_right_difference[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m R")
                        for bit in range(state_size):
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-8)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-8)%state_size, 1].X == 1:
                                        print(f"\033[96m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_8")
                        for bit in range(state_size):
                                couleur = 4*int(down_left_state_8[round, bit, 1].X) + 7*int(down_left_state_8[round, bit, 2].X)
                                if down_left_difference[round, (bit+8)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference[round, (bit+8)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference[round, (bit+8)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_8     ", end="")
                        for bit in range(state_size):
                                if key[structure_size + MITM_up_size + distinguisher_size + round, bit, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + MITM_up_size + distinguisher_size + round, bit, 1].X == 1:
                                        print(f"\033[96m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K")
                        for bit in range(state_size):
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-1)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-1)%state_size, 1].X == 1:
                                        print(f"\033[96m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_1")
                        for bit in range(state_size):
                                couleur = 4*int(down_left_state_1[round, bit, 1].X) + 7*int(down_left_state_1[round, bit, 2].X)
                                if down_left_difference[round, (bit+1)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference[round, (bit+1)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference[round, (bit+1)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_1     ", end="")
                        for bit in range(state_size):
                                couleur = 4*int(down_right_state[round, bit, 1].X)
                                if down_left_difference_AND[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference_AND[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if down_left_difference_AND[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m P ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_AND")
                        for bit in range(state_size):
                                couleur = 4*int(down_left_state_2[round, bit, 1].X)
                                if down_left_difference[round, (bit+2)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference[round, (bit+2)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference[round, (bit+2)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_2     ", end="")
                        for bit in range(state_size):
                                couleur = 4*int(down_right_state[round, bit, 1].X)
                                if down_left_difference_XOR[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference_XOR[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference_XOR[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_XOR")

                print("UP part parameters")
                print("key : ", key_quantity_up.getValue())
                print("state test: ", state_test_up_quantity.getValue())
                print("proba key rec : ", probabilistic_key_recovery_up.getValue())
                print('complexity = ', distinguisher_probability + complexity_up.X)
                print("")
                print("DOWN values")
                print("key : ", key_quantity_down.getValue())
                print("state test : ", state_test_down_quantity.getValue())
                print("proba key rec : ", probabilistic_key_recovery_down.getValue())
                print('complexity = ', distinguisher_probability + complexity_down.X)
                print("")
                print("MATHC complexity = ", distinguisher_probability + complexity_match.X)
                print("guess match", guess_match.X)
                print("Key Quantity :", structure_size*subkey_size + key_quantity_down.getValue() + key_quantity_up.getValue() + state_test_down_quantity.getValue() + state_test_down_quantity.getValue())
        else :
                model.computeIIS()
                model.write("model_infeasible.ilp")
                return([False])

diff_mitm_SIMON()