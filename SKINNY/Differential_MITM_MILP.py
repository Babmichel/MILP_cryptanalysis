#Differential_MITM_MILP

import gurobipy as gp
from gurobipy import GRB
import numpy as np
from tqdm import tqdm

def tweakey(key):
    """Skinny tweaky.

    return the next key in the SKINNY key schedule

    Parameters
    ----------
    key : np.array

    Returns
    -------
    new_key : np.array
    the one-round tweaky on the provided key in np.array type
    """
    new_key = np.zeros((4, 4))
    new_key[0, 0] = key[2, 1]
    new_key[0, 1] = key[3, 3]
    new_key[0, 2] = key[2, 0]
    new_key[0, 3] = key[3, 1]
    new_key[1, 0] = key[2, 2]
    new_key[1, 1] = key[3, 2]
    new_key[1, 2] = key[3, 0]
    new_key[1, 3] = key[2, 3]
    new_key[2, 0] = key[0, 0]
    new_key[2, 1] = key[0, 1]
    new_key[2, 2] = key[0, 2]
    new_key[2, 3] = key[0, 3]
    new_key[3, 0] = key[1, 0]
    new_key[3, 1] = key[1, 1]
    new_key[3, 2] = key[1, 2]
    new_key[3, 3] = key[1, 3]
    return new_key

def attack(structure_round, MITM_up_round, differential_round, MITM_down_round, key_space_size):
    options = {
    "WLSACCESSID" : "bb41a17b-b3b2-40d7-8c1c-01d90a2e2170",
    "WLSSECRET" : "4db1c96a-1e47-4fc9-83eb-28a57d08879f",
    "LICENSEID" : 2534357
    }
    with gp.Env(params=options) as env, gp.Model(env=env) as model:
        
        model.Params.MIRcuts = 2 #o for no cuts, 1 for classic cuts, 2 for agressive cuts
        #model.Params.Presolve = 2 
        model.Params.MIPFocus = 3 #1 for focusing feasible solution, 2 for optimality, 3 to focus on the bous (if best bound is not mooving)

        #ATTACK PARAMETERS
        total_round = structure_round + MITM_up_round + MITM_down_round + differential_round

        #KEY MATERIAL
        key_index_0 = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]])

        key_index_copy = key_index_0.copy()
        list_of_key_index = np.zeros((total_round,4,4))
        for index in range(total_round):
            list_of_key_index[index, :, :] = key_index_copy
            key_index_copy = tweakey(key_index_copy)

        #GUROBI Variables initalization
        structure_state = np.zeros((structure_round, 3, 4, 4, 5), dtype=object) #[indice tour, indice step, indice ligne, indice colonne, couleur(0=inconnue, 1= connue de rouge, 2= connu de bleu, 3 = connu de violet, 4 = Fix)]
        
        MITM_up_state = np.zeros((MITM_up_round, 3, 4, 4, 3), dtype=object) #[indice tour, indice step, indice ligne, indice colonne, couleur(0 = inconnue, 1 = bleu, 2=state_test)]
        
        MITM_down_state = np.zeros((MITM_down_round, 3, 4, 4, 3), dtype=object) #[indice tour, indice step, indice ligne, indice colonne, couleur(0 = inconnue, 1 = rouge, 2=state_test)]

        differential_up_state = np.zeros((MITM_up_round, 2, 4, 4, 4), dtype=object) #[indice tour, indice step, indice ligne indice colonne, couleur(0=inconnue, 1 = connue)]

        differential_down_state = np.zeros((MITM_down_round, 2, 4, 4, 4), dtype=object) #[indice tour, indice step, indice ligne indice colonne, couleur(0=inconnue, 1 = connue)]

        differential_state = np.zeros((differential_round, 3, 4, 4, 4), dtype=object) #[indice tour, indice step, indice ligne, indice colonne, couleur(0 = inconnue, 1 = connue, 2 = guess)]

        full_key = np.zeros((total_round, key_space_size + 1, 4, 4, 4), dtype = object) #[indice tour, indice clé, indice ligne, indice tour, couleur(0 = inconnue, 1 = rouge, 2 = bleu, 3 = violet)]

        key_knowledge = np.zeros((4, 4,key_space_size+1, 2), dtype = object) #[indice ligne, indice colonne, cle, couleur (0 = rouge, 1 = bleu)]

        if structure_round>0:
            MC_structure_branch = np.zeros((structure_round - 1, 4, 4, 5, 4), dtype = object) #[round, row, column, color, number of fix in the state]

        binary_bound_for_key_knowledge = np.zeros((4, 4,key_space_size+1, 2, 2), dtype = object) #binary variable to constraint the key knowledge following the key schedule(if three or more word of the same key element are guess, all the corresponding element are guessed)

        binary_key_XOR = np.zeros((total_round, 4, 4, 4), dtype = object) #Binary discriminator to know if the XOR of the key is purple, red blue or unknow

        binary_count_for_match = np.zeros((4,4,2), dtype = object) #binary discrimiator to count if we have more than three equations for a key that induce a linear relation to sieve the MATCH

        key_sum_count = np.zeros((4,4), dtype=object) #total amount of key guess per key word

        #GUROBI variable creation
        for row in range(4):
            for col in range(4):
                for key in range(key_space_size+1):
                    for color in range(2):
                        for binary in range(2):
                            binary_bound_for_key_knowledge[row, col, key, color, binary] = model.addVar(vtype = GRB.BINARY, name = f'binary_bound_for_key_knowledge {row} {col} {color} {binary}' )
        
        for round in range(structure_round):
            for step in range(3):
                for row in range(4):
                    for col in range(4):
                        for color in range(5):
                            structure_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name =f'structure_state:{round},{step},{row},{col},{color}')

        for round in range(MITM_up_round):
            for step in range(3):
                for row in range(4):
                    for col in range(4):
                        for color in range(3):
                            MITM_up_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f'MITM_down_round:{round},{step},{row},{col},{color}')

        for round in range(MITM_down_round):
            for step in range(3):
                for row in range(4):
                    for col in range(4):
                        for color in range(3):
                            MITM_down_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM_up_round:{round},{step},{row},{col},{color}")

        for round in range(MITM_down_round):
            for step in range(2):
                for row in range(4):
                    for col in range(4):
                        for color in range(4):
                            differential_down_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"differential_down_state:{round},{step},{row},{col},{color}")

        for round in range(MITM_up_round):
            for step in range(2):
                for row in range(4):
                    for col in range(4):
                        for color in range(4):
                            differential_up_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"differential_down_state:{round},{step},{row},{col},{color}")

        for round in range(differential_round):
            for step in range(3):
                for row in range(4):
                    for col in range(4):
                        for color in range(4):
                            differential_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"differential_round:{round},{step},{row},{col},{color}")
                            
        for round in range(total_round):
            for index in range(key_space_size + 1):
                for row in range(4):
                    for col in range(4):
                        for color in range(4):
                            full_key[round, index, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"structure_key:{round},{step},{row},{col},{color}")

        for row in range(4):
            for col in range(4):
                for key in range(key_space_size+1):
                    for color in range(2):
                        key_knowledge[row, col, key, color] = model.addVar(lb = 0.0,ub = total_round-differential_round, vtype = GRB.INTEGER, name = f'red_keyknowledge{row} {col} {color}')

        if structure_round>0:
            for round in range(structure_round-1):
                for row in range(4):
                    for col in range(4):
                        for color in range(5):
                            for fix in range(4):
                                MC_structure_branch[round, row, col, color, fix] = model.addVar(vtype = GRB.BINARY, name = f"MC_structure_branch:{round},{row},{col},{color},{fix}")

        for round in range(total_round):
            for col in range(4):
                for row in range(4):
                    for color in range(4):
                        binary_key_XOR[round, col, row, color] = model.addVar(vtype = GRB.BINARY, name = f"XOR key info{round},{row},{col},{color}")

        for row in range(4):
            for col in range(4):
                key_sum_count[row, col] = model.addVar(vtype = GRB.INTEGER)
                for binary in range(2):
                    binary_count_for_match[row, col, binary] = model.addVar(vtype= GRB.BINARY, name = f"binarymatch{row}{col}")

        complexite_rouge = model.addVar(lb = 0.0, ub = 360.0,vtype= GRB.INTEGER, name = "complexite")
        complexite_bleu = model.addVar(lb = 0.0, ub = 360.0,vtype= GRB.INTEGER, name = "complexite")
        complexite_match = model.addVar(lb = 0.0, ub = 360.0,vtype= GRB.INTEGER, name = "complexite")
        complexite = model.addVar(lb = 0.0, ub = 360.0,vtype= GRB.INTEGER, name = "complexite")

        #Optimization function

        #count of the state test
        state_test_up = gp.quicksum(MITM_up_state[round, step, row, col, 2] for round in range(MITM_up_round) for step in range(3) for row in range(4) for col in range(4))
        state_test_down = gp.quicksum(MITM_down_state[round, step, row, col, 2] for round in range(MITM_down_round) for step in range(3) for row in range(4) for col in range(4))
        
        #Probabilistic key recovery 
        MITM_up_guess = gp.quicksum(differential_up_state[round, 1, row, col, 2] for round in range(MITM_up_round) for row in range(4) for col in range(4))
        MITM_down_guess = gp.quicksum(differential_down_state[round, 0, row, col, 2] for round in range(MITM_down_round) for row in range(4) for col in range(4))
       
        #count of the fix in structure
         #count of the fix in structure
        if structure_round>0:
            fix_quantity_structure = gp.quicksum(structure_state[round, step, row, col, 4] for round in range(structure_round) for step in range(3) for row in range(4) for col in range(4))
            end_structure_active = gp.quicksum(structure_state[structure_round-1, 2, row, col, color] for row in range(4) for col in range(4) for color in [2,3,4])
            start_structure_active = gp.quicksum(structure_state[0, 0, row, col, color] for row in range(4) for col in range(4) for color in [1,3,4])
        else : 
            fix_quantity_structure = 16
            end_structure_active = 16
            start_structure_active = 16

        #count of the cost of the differential
        cost_differential = 0.25*gp.quicksum(differential_state[round, 0, row, col, 1] for round in range(differential_round) for row in range(4) for col in range(4))
        objective_differential_end = 0.25*gp.quicksum(differential_state[differential_round-1, 1, row, col, 1] for row in range(4) for col in range(4))

        #mombre de bleu et rouge guess
        count_blue = gp.quicksum(binary_bound_for_key_knowledge[row, col, 0, 1, 1]*key_knowledge[row, col, 0, 1] for row in range(4) for col in range(4)) + (key_space_size)*gp.quicksum(binary_bound_for_key_knowledge[row, col, 0, 1, 0] for row in range(4) for col in range(4))
        count_red = gp.quicksum(binary_bound_for_key_knowledge[row, col, 0, 0, 1]*key_knowledge[row, col, 0, 0] for row in range(4) for col in range(4)) + (key_space_size)*gp.quicksum(binary_bound_for_key_knowledge[row, col, 0, 0, 0] for row in range(4) for col in range(4))
        
        #nombre de violet guess
        count_equation = gp.quicksum(binary_count_for_match[row,col,1]*(key_sum_count[row,col]-3) for row in range(4) for col in range(4))
        
        #complexity constraints
        
        blue_complexity = count_blue + cost_differential + state_test_up + MITM_up_guess + fix_quantity_structure - end_structure_active
        red_complexity = count_red + cost_differential + state_test_down + MITM_down_guess + fix_quantity_structure - start_structure_active
        MATCH_complexity = blue_complexity + red_complexity + (fix_quantity_structure - end_structure_active - start_structure_active)- 2*(16-fix_quantity_structure) - count_equation
        model.addConstr(blue_complexity <= complexite + complexite_bleu)
        model.addConstr(red_complexity <= complexite + complexite_rouge)
        model.addConstr(MATCH_complexity <= complexite + complexite_match)
        #Objective : Minimize the attack complexity
        model.setObjectiveN(complexite + complexite_rouge + complexite_bleu + complexite_match, 0, 10)
        #model.setObjective(complexite_bleu+complexite_rouge)
        
        model.ModelSense = GRB.MINIMIZE

        ### CONSTRAINTS ###
        #without state test
        #model.addConstr(state_test_up == 0)
        #model.addConstr(state_test_down == 0)

        #without probabilistic key recovery
        #model.addConstr(MITM_up_guess == 0)
        #model.addConstr(MITM_down_guess == 0)

        #We need less text generated by the structure than the one needed at the start of the distinguisher
        model.addConstr(16 - end_structure_active <= cost_differential)

        #Count for the match:
        for row in range(4):
            for col in range(4):
                model.addConstr(binary_count_for_match[row, col,0] + binary_count_for_match[row, col,1] == 1)
                for binary in range(2):
                    model.addGenConstrIndicator(binary_count_for_match[row, col,1], True, key_sum_count[row, col], gp.GRB.GREATER_EQUAL, 3) 
                    model.addGenConstrIndicator(binary_count_for_match[row, col,0], True, key_sum_count[row, col], gp.GRB.LESS_EQUAL, 2)

        for row in range(4):
            for col in range(4):
                model.addConstr(key_sum_count[row,col] == gp.quicksum((binary_bound_for_key_knowledge[row, col, 0, color, 1]*key_knowledge[row, col, 0, color] + (key_space_size)*(binary_bound_for_key_knowledge[row, col, 0, color, 0])) for color in range(2)))            

        ### KEY Constraints

        for round in range (total_round):
            for key in range(key_space_size + 1):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(gp.quicksum(full_key[round, key, row, col, color] for color in range(4)) == 1) #key must be unkown, red, blue, or purple
        
        for round in range(total_round-differential_round):
            for key in range(1, key_space_size + 1):
                model.addConstr(gp.quicksum([full_key[round, key, row, col, color]  for row in range(4) for col in range(4) for color in [1, 3]]) <= 15) #on ne peux pas connaître toute la clé du coté des rouges
                model.addConstr(gp.quicksum([full_key[round, key, row, col, color]  for row in range(4) for col in range(4) for color in [2, 3]]) <= 15) #on ne peux pas connaître toute la clé du coté des bleus  

        for round in range(structure_round + MITM_up_round, structure_round + MITM_up_round + differential_round): #no key use in the distinguisher
            for key in range(key_space_size+1):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(full_key[round, key, row, col, 0] == 1)

        #Key schedule :  if we guess more than two time a key word of the full key, we guessed it for all the others

        for row in range(4):
            for col in range(4):
                for key in range(key_space_size+1):
                    for colour in range(2):
                        model.addConstr(key_knowledge[row,col,key,colour] == gp.quicksum(full_key[round, key, np.where(list_of_key_index[round] == key_index_0[row,col])[0][0], np.where(list_of_key_index[round] == key_index_0[row,col])[1][0], key_color] for round in range(total_round) for key_color in [colour+1,3]))
                        model.addConstr(binary_bound_for_key_knowledge[row, col,key, colour,0] + binary_bound_for_key_knowledge[row, col,key, colour, 1] == 1)

        for row in range(4):
            for col in range(4):
                for colour in range(2):                
                    model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col, 0, colour, 0], True, key_knowledge[row, col, 0, colour], gp.GRB.GREATER_EQUAL, (total_round-differential_round)) 
                    model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col, 0, colour, 1], True, key_knowledge[row, col, 0, colour], gp.GRB.LESS_EQUAL, key_space_size-1)
                    
                    model.addConstr((binary_bound_for_key_knowledge[row, col,0, colour,0] == 1) >> (binary_bound_for_key_knowledge[row, col,1, colour,0] == 1))
                    model.addConstr((binary_bound_for_key_knowledge[row, col,0, colour,1] == 1) >> (binary_bound_for_key_knowledge[row, col,1, colour,1] == 1))
                    if key_space_size > 1 :
                        model.addConstr((binary_bound_for_key_knowledge[row, col,0, colour,0] == 1) >> (binary_bound_for_key_knowledge[row, col,2, colour,0] == 1))
                        model.addConstr((binary_bound_for_key_knowledge[row, col,0, colour,1] == 1) >> (binary_bound_for_key_knowledge[row, col,2, colour,1] == 1))
                    if key_space_size > 2 :
                        model.addConstr((binary_bound_for_key_knowledge[row, col,0, colour,0] == 1) >> (binary_bound_for_key_knowledge[row, col,3, colour,0] == 1))
                        model.addConstr((binary_bound_for_key_knowledge[row, col,0, colour,1] == 1) >> (binary_bound_for_key_knowledge[row, col,3, colour,1] == 1))
                    for key in range(1,key_space_size+1):          
                        model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col, key, colour, 0], True, key_knowledge[row, col,key, colour], gp.GRB.GREATER_EQUAL, total_round-differential_round) 
                        model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col, key, colour, 1], True, key_knowledge[row, col,key, colour], gp.GRB.LESS_EQUAL,0)

        #Structure constraints
        if structure_round>0:
            #same unkown element through structure
            
            #starting constraints
            for row in range(4):
                for col in range(4):
                    model.addConstr(structure_state[0, 0, row, col, 2] == 0) #first state must be kown only by red, fix or unknow
                    model.addConstr(structure_state[0, 0, row, col, 3] == 0)
            
                    model.addConstr(structure_state[structure_round - 1, 2, row, col, 1] == 0) #last state must be kown only by blue or purple or unknow
            
            model.addConstr(gp.quicksum(structure_state[0,0,row, col, color] for col in range(4) for row in range(4) for color in range(1,5)) == fix_quantity_structure) # we must know at the start of the structure as many word than we fix
            model.addConstr(gp.quicksum(structure_state[structure_round-1,2,row, col, color] for col in range(4) for row in range(4) for color in range(1,5)) == fix_quantity_structure) # we must know at the end of the structure as many word than we fix 
            
            model.addConstr(gp.quicksum(structure_state[0, 0, row, col, 0] for row in range(4) for col in range(4)) <= 15) # on ne peux pas ne pas connaître tout l'état de depart
            model.addConstr(gp.quicksum(structure_state[structure_round - 1, 2, row, col, 0] for row in range(4) for col in range(4)) <= 15) # on ne peux pas ne pas connaître tout l'état d'arrive
            
            #Maximum of 16 fix word 
            model.addConstr(fix_quantity_structure<=16)

            #Color constraint states
            for round in range(structure_round):
                for step in range(3):
                    for row in range(4):
                        for col in range(4):
                            model.addConstr(gp.quicksum(structure_state[round, step, row, col, color] for color in range(5)) == 1) #state can be only in one colour
            
            #Key addition constraints
            for round in range(structure_round):
                for row in range(2):
                    for col in range(4):
                        model.addConstr((structure_state[round, 0, row, col, 0] == 1) >> (structure_state[round, 1, row, col, 0] == 1)) #unknow state is unknow after AK
                        model.addConstr((full_key[round, 0, row, col, 0] == 1) >> (structure_state[round, 1, row, col, 0] == 1)) #unknow key lead to unknow state after AK
                        
                        model.addConstr((structure_state[round, 1, row, col, 1] == 1) >> (structure_state[round, 0, row, col, 2] == 0)) #state after AK is red, state before cannot be blue
                        model.addConstr((structure_state[round, 1, row, col, 1] == 1) >> (full_key[round, 0, row, col, 2] == 0)) #state after AK is red, key before cannot be blue

                        model.addConstr((structure_state[round, 1, row, col, 2] == 1) >> (structure_state[round, 0, row, col, 1] == 0)) #state after AK is blue, state before cannot be red
                        model.addConstr((structure_state[round, 1, row, col, 2] == 1) >> (full_key[round, 0, row, col, 1] == 0)) #state after AK is blue, key before cannot be red

                        model.addConstr((structure_state[round, 1, row, col, 3] == 1) >> (structure_state[round, 0, row, col, 1] == 0)) #state after AK is purple, state before cannot be red
                        model.addConstr((structure_state[round, 1, row, col, 3] == 1) >> (full_key[round, 0, row, col, 1] == 0)) #state after AK is purple, state before cannot be red

                        model.addConstr((structure_state[round, 1, row, col, 3] == 1) >> (structure_state[round, 0, row, col, 2] == 0)) #state after AK is purple, state before cannot be blue
                        model.addConstr((structure_state[round, 1, row, col, 3] == 1) >> (full_key[round, 0, row, col, 2] == 0)) #state after AK is purple, state before cannot be blue

                        model.addConstr((structure_state[round, 1, row, col, 2] == gp.or_(structure_state[round, 0, row, col, 2], full_key[round, 0, row, col, 2]))) #blue after AK only if blue in the key or previous state
                        model.addConstr((structure_state[round, 0, row, col, 1] == gp.or_(structure_state[round, 1, row, col, 1], full_key[round, 0, row, col, 1]))) #red before AK only if red in the key or next state

                for row in range(2,4): # last rows not impacted by the AK (Fix became purple)
                    for col in range(4):
                        for color in range(4):
                            model.addConstr((structure_state[round, 0, row , col, color] == 1) >> (structure_state[round, 1, row , col, color] == 1))
                        model.addConstr((structure_state[round, 0, row , col, 4] == 1) >> (structure_state[round, 1, row , col, 3] == 1))

            #Permutation :
            for round in range(structure_round):
                for col in range(4):
                    for color in range(4):
                        model.addConstr((structure_state[round, 1, 0, col, color] == 1) >> (structure_state[round, 2, 0, col, color] == 1))
                        model.addConstr((structure_state[round, 1, 1, col, color] == 1) >> (structure_state[round, 2, 1, (col +1) % 4, color] == 1))
                        model.addConstr((structure_state[round, 1, 2, col, color] == 1) >> (structure_state[round, 2, 2, (col +2) % 4, color] == 1))
                        model.addConstr((structure_state[round, 1, 3, col, color] == 1) >> (structure_state[round, 2, 3, (col +3) % 4, color] == 1))
                    model.addConstr((structure_state[round, 1, 0, col, 4] == 1) >> (structure_state[round, 2, 0, col, 3] == 1))
                    model.addConstr((structure_state[round, 1, 1, col, 4] == 1) >> (structure_state[round, 2, 1, (col + 1) % 4, 3] == 1))
                    model.addConstr((structure_state[round, 1, 2, col, 4] == 1) >> (structure_state[round, 2, 2, (col + 2) % 4, 3] == 1))
                    model.addConstr((structure_state[round, 1, 3, col, 4] == 1) >> (structure_state[round, 2, 3, (col + 3) % 4, 3] == 1))

            
            #MC
            for round in range(structure_round - 1):
                for row in range(4):
                    for col in range(4):
                        for color in [0,1,2,4]:
                            for index in [1,2,3]:
                                model.addConstr(MC_structure_branch[round, row, col, color, index] == 0) #pas de cas particulier autre que avec un violet

            for round in range(structure_round-1):
                for col in range(4):
                    #FIRST LINE
                    #setting the branch
                    model.addConstr(gp.quicksum(MC_structure_branch[round, 0, col, color, index] for color in range(5)  for index in range(4)) == 1)
                    model.addConstr((MC_structure_branch[round, 0, col, 0, 0] == 1) >> (structure_state[round + 1, 0, 0, col, 0] == 1)) #unknow
                    model.addConstr((MC_structure_branch[round, 0, col, 1, 0] == 1) >> (structure_state[round + 1, 0, 0, col, 1] == 1)) #red
                    model.addConstr((MC_structure_branch[round, 0, col, 2, 0] == 1) >> (structure_state[round + 1, 0, 0, col, 2] == 1)) #blue
                    model.addConstr((MC_structure_branch[round, 0, col, 3, 0] == 1) >> (structure_state[round + 1, 0, 0, col, 3] == 1)) #purple and not fixe
                    #model.addConstr((MC_structure_branch[round, 0, col, 3, 0] == 1) >> (structure_state[round + 1, 0, 3, col, 4] == 0)) #purple and not fixe
                    model.addConstr((MC_structure_branch[round, 0, col, 3, 1] == 1) >> (structure_state[round + 1, 0, 0, col, 3]  + structure_state[round + 1, 0, 3, col, 4] == 2)) #purple and fixe
                    model.addConstr((MC_structure_branch[round, 0, col, 4, 0] == 1) >> (structure_state[round + 1, 0, 0, col, 4] == 1)) #fixe
                    model.addConstr(MC_structure_branch[round, 0, col, 3, 2] == 0) #no other one fix situation
                    model.addConstr(MC_structure_branch[round, 0, col, 3, 3] == 0) #no two fix situation
                    
                    #unkwown
                    for i in [1,3,4]:
                        for j in [1,3,4]:
                            for k in [1,3,4]:
                                model.addConstr((MC_structure_branch[round, 0, col, 0, 0] == 1) >> (structure_state[round, 2, 0, col, i] + structure_state[round, 2, 2, col, j] + structure_state[round, 2, 3, col, k] <= 2)) #unknow element can't come to a red known XOR

                    for i in [2,3,4]:
                        for j in [2,3,4]:
                            for k in [2,3,4]:
                                model.addConstr((MC_structure_branch[round, 0, col, 0, 0] == 1) >> (structure_state[round, 2, 0, col, i] + structure_state[round, 2, 2, col, j] + structure_state[round, 2, 3, col, k] <= 2)) #unknow element can't come to a blue known XOR

                    #if a red element
                    model.addConstr((MC_structure_branch[round, 0, col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 0] == 0)) #no unknown element 
                    model.addConstr((MC_structure_branch[round, 0, col, 1, 0] == 1) >> (structure_state[round, 2, 2, col, 0] == 0)) #no unknown element
                    model.addConstr((MC_structure_branch[round, 0, col, 1, 0] == 1) >> (structure_state[round, 2, 3, col, 0] == 0)) #no unknown element

                    model.addConstr((MC_structure_branch[round, 0, col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 2] == 0)) #no blue element 
                    model.addConstr((MC_structure_branch[round, 0, col, 1, 0] == 1) >> (structure_state[round, 2, 2, col, 2] == 0)) #no blue element
                    model.addConstr((MC_structure_branch[round, 0, col, 1, 0] == 1) >> (structure_state[round, 2, 3, col, 2] == 0)) #no blue element

                    for i in range(2): #not three purple or fix
                        for j in range(2):
                            for k in range(2): 
                                model.addConstr((MC_structure_branch[round, 0, col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 3+i] + structure_state[round, 2, 2, col, 3+j] + structure_state[round, 2, 3, col, 3+k] <= 2))

                    #if a blue element
                    model.addConstr((MC_structure_branch[round, 0, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 0] == 0)) #no unknown element 
                    model.addConstr((MC_structure_branch[round, 0, col, 2, 0] == 1) >> (structure_state[round, 2, 2, col, 0] == 0)) #no unknown element
                    model.addConstr((MC_structure_branch[round, 0, col, 2, 0] == 1) >> (structure_state[round, 2, 3, col, 0] == 0)) #no unknown element

                    model.addConstr((MC_structure_branch[round, 0, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 1] == 0)) #no red element 
                    model.addConstr((MC_structure_branch[round, 0, col, 2, 0] == 1) >> (structure_state[round, 2, 2, col, 1] == 0)) #no red element
                    model.addConstr((MC_structure_branch[round, 0, col, 2, 0] == 1) >> (structure_state[round, 2, 3, col, 1] == 0)) #no red element

                    for i in range(2): #not three purple or fix
                        for j in range(2):
                            for k in range(2): 
                                model.addConstr((MC_structure_branch[round, 0, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 3+i] + structure_state[round, 2, 2, col, 3+j] + structure_state[round, 2, 3, col, 3+k] <= 2))

                    #if a purple element without fix, previous state can only be purple
                    model.addConstr((MC_structure_branch[round, 0, col, 3, 0] == 1) >> (structure_state[round, 2, 0, col, 3] + structure_state[round, 2, 0, col, 4] == 1)) 
                    model.addConstr((MC_structure_branch[round, 0, col, 3, 0] == 1) >> (structure_state[round, 2, 2, col, 3] + structure_state[round, 2, 2, col, 4] == 1))
                    model.addConstr((MC_structure_branch[round, 0, col, 3, 0] == 1) >> (structure_state[round, 2, 3, col, 3] + structure_state[round, 2, 3, col, 4] == 1))

                    #if a purple element and a fix in last position, previous last element of same column can be purple or fix by backward prop
                    model.addConstr((MC_structure_branch[round, 0, col, 3, 1] == 1) >> (structure_state[round, 2, 3, col, 3] + structure_state[round, 2, 3, col, 4] == 1)) 

                    #if fix word, previous must be known by red to have equations
                    
                    model.addConstr((MC_structure_branch[round, 0, col, 4, 0] == 1) >> (structure_state[round, 2, 0, col, 0] == 0))
                    model.addConstr((MC_structure_branch[round, 0, col, 4, 0] == 1) >> (structure_state[round, 2, 2, col, 0] == 0))
                    model.addConstr((MC_structure_branch[round, 0, col, 4, 0] == 1) >> (structure_state[round, 2, 3, col, 0] == 0))
                    
                    model.addConstr((MC_structure_branch[round, 0, col, 4, 0] == 1) >> (structure_state[round, 2, 0, col, 2] == 0))
                    model.addConstr((MC_structure_branch[round, 0, col, 4, 0] == 1) >> (structure_state[round, 2, 2, col, 2] == 0))
                    model.addConstr((MC_structure_branch[round, 0, col, 4, 0] == 1) >> (structure_state[round, 2, 3, col, 2] == 0))
                    

                    #SECOND LINE
                    #setting the branch
                    model.addConstr(gp.quicksum(MC_structure_branch[round, 1, col, color, index] for color in range(5) for index in range(4)) == 1)
                    model.addConstr((MC_structure_branch[round, 1, col, 0, 0] == 1) >> (structure_state[round + 1, 0, 1, col, 0] == 1)) #unknow
                    model.addConstr((MC_structure_branch[round, 1, col, 1, 0] == 1) >> (structure_state[round + 1, 0, 1, col, 1] == 1)) #red
                    model.addConstr((MC_structure_branch[round, 1, col, 2, 0] == 1) >> (structure_state[round + 1, 0, 1, col, 2] == 1)) #blue
                    model.addConstr((MC_structure_branch[round, 1, col, 3, 0] == 1) >> (structure_state[round + 1, 0, 1, col, 3] == 1)) #purple and not fixe
                    #model.addConstr((MC_structure_branch[round, 1, col, 3, 0] == 1) >> (structure_state[round + 1, 0, 3, col, 4] == 0)) #purple and not fixe
                    model.addConstr((MC_structure_branch[round, 1, col, 3, 1] == 1) >> (structure_state[round + 1, 0, 1, col, 3]  + structure_state[round + 1, 0, 3, col, 4] == 2)) #purple and fixe
                    #model.addConstr((MC_structure_branch[round, 1, col, 3, 1] == 1) >> (structure_state[round + 1, 0, 2, col, 3] == 0)) #purple and fix
                    model.addConstr((MC_structure_branch[round, 1, col, 3, 3] == 1) >> (structure_state[round + 1, 0, 1, col, 3]  + structure_state[round + 1, 0, 2, col, 4] + structure_state[round + 1, 0, 3, col, 4] == 3)) #purple and 2 fixe
                    model.addConstr((MC_structure_branch[round, 1, col, 4, 0] == 1) >> (structure_state[round + 1, 0, 1, col, 4] == 1)) #fixe
                    model.addConstr(MC_structure_branch[round, 1, col, 3, 2] == 0) #no other one fix situation

                    #unkwown
                    for i in [1,2,3,4]:
                        model.addConstr((MC_structure_branch[round, 1, col, 0, 0] == 1) >> (structure_state[round, 2, 0, col, i] == 0)) #unknow element can come to a red known XOR

                    #if a red element
                    model.addConstr((MC_structure_branch[round, 1, col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 0] == 0)) #no unknown element 
                    model.addConstr((MC_structure_branch[round, 1, col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 2] == 0)) #no blue element 
                    model.addConstr((MC_structure_branch[round, 1, col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 3] == 0)) #no purple element 
                    model.addConstr((MC_structure_branch[round, 1, col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 4] == 0)) #no fix element 

                    #if a blue element
                    model.addConstr((MC_structure_branch[round, 1, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 0] == 0)) #no unknown element
                    model.addConstr((MC_structure_branch[round, 1, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 1] == 0)) #no red element 
                    model.addConstr((MC_structure_branch[round, 1, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 3] == 0)) #no purple element 
                    model.addConstr((MC_structure_branch[round, 1, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 4] == 0)) #no fix element 
                    
                    #if a purple element without fix, previous state can only be purple
                    model.addConstr((MC_structure_branch[round, 1, col, 3, 0] == 1) >> (structure_state[round, 2, 0, col, 3] + structure_state[round, 2, 0, col, 4] == 1)) 

                    #if a purple element and a fix in last position, previous third element of same column can be purple or fix by backward prop
                    model.addConstr((MC_structure_branch[round, 1, col, 3, 1] == 1) >> (structure_state[round, 2, 2, col, 3] + structure_state[round, 2, 2, col, 4] == 1)) 

                    #if a purple element with two fix, previous second element can be purple or fix
                    model.addConstr((MC_structure_branch[round, 1, col, 3, 3] == 1) >> (structure_state[round, 2, 1, col, 3] + structure_state[round, 2, 1, col, 4] == 1)) 

                    #fix
                    
                    model.addConstr((MC_structure_branch[round, 1, col, 4, 0] == 1) >> (structure_state[round, 2, 0, col, 0] == 0))
                    
                    model.addConstr((MC_structure_branch[round, 1, col, 4, 0] == 1) >> (structure_state[round, 2, 0, col, 2] == 0))
                    

                    #THIRD LINE
                    model.addConstr(gp.quicksum(MC_structure_branch[round, 2, col, color, index] for color in range(5) for index in range(4)) == 1)
                    model.addConstr((MC_structure_branch[round, 2, col, 0, 0] == 1) >> (structure_state[round + 1, 0, 2, col, 0] == 1)) #unknow
                    model.addConstr((MC_structure_branch[round, 2, col, 1, 0] == 1) >> (structure_state[round + 1, 0, 2, col, 1] == 1)) #red
                    model.addConstr((MC_structure_branch[round, 2, col, 2, 0] == 1) >> (structure_state[round + 1, 0, 2, col, 2] == 1)) #blue
                    model.addConstr((MC_structure_branch[round, 2, col, 3, 0] == 1) >> (structure_state[round + 1, 0, 2, col, 3] == 1)) #purple and not fixe
                    #model.addConstr((MC_structure_branch[round, 2, col, 3, 0] == 1) >> (structure_state[round + 1, 0, 3, col, 4] + structure_state[round + 1, 0, 1, col, 4] <= 1)) #purple and not fixe
                    model.addConstr((MC_structure_branch[round, 2, col, 3, 3] == 1) >> (structure_state[round + 1, 0, 2, col, 3]  + structure_state[round+1, 0, 3, col, 4] + structure_state[round+1, 0, 1, col, 4] == 3)) #purple and 2 fixe
                    model.addConstr((MC_structure_branch[round, 2, col, 4, 0] == 1) >> (structure_state[round + 1, 0, 2, col, 4] == 1)) #fixe
                    model.addConstr(MC_structure_branch[round, 2, col, 3, 1] == 0) #no one fix situation
                    model.addConstr(MC_structure_branch[round, 2, col, 3, 2] == 0) #no one fix situation
                    
                    #unkwown
                    for i in [1,3,4]:
                        for j in [1,3,4]:
                            model.addConstr((MC_structure_branch[round, 2, col, 0, 0] == 1) >> (structure_state[round, 2, 1, col, i] + structure_state[round, 2, 2, col, j] <= 1)) #unknow element can come to a red known XOR

                    for i in [2,3,4]:
                        for j in [2,3,4]:
                            model.addConstr((MC_structure_branch[round, 2, col, 0, 0] == 1) >> (structure_state[round, 2, 1, col, i] + structure_state[round, 2, 2, col, j] <= 1)) #unknow element can come to a blue known XOR

                    #if a red element
                    model.addConstr((MC_structure_branch[round, 2, col, 1, 0] == 1) >> (structure_state[round, 2, 1, col, 0] == 0)) #no unknown element 
                    model.addConstr((MC_structure_branch[round, 2, col, 1, 0] == 1) >> (structure_state[round, 2, 2, col, 0] == 0)) #no unknown element

                    model.addConstr((MC_structure_branch[round, 2, col, 1, 0] == 1) >> (structure_state[round, 2, 1, col, 2] == 0)) #no blue element 
                    model.addConstr((MC_structure_branch[round, 2, col, 1, 0] == 1) >> (structure_state[round, 2, 2, col, 2] == 0)) #no blue element

                    for i in range(2): #not three purple or fix
                        for j in range(2):
                            model.addConstr((MC_structure_branch[round, 2,col, 1, 0] == 1) >> (structure_state[round, 2, 1, col, 3+i] + structure_state[round, 2, 2, col, 3+j] <= 1))

                    #if a blue element
                    model.addConstr((MC_structure_branch[round, 2, col, 2, 0] == 1) >> (structure_state[round, 2, 1, col, 0] == 0)) #no unknown element 
                    model.addConstr((MC_structure_branch[round, 2, col, 2, 0] == 1) >> (structure_state[round, 2, 2, col, 0] == 0)) #no unknown element

                    model.addConstr((MC_structure_branch[round, 2, col, 2, 0] == 1) >> (structure_state[round, 2, 1, col, 1] == 0)) #no red element 
                    model.addConstr((MC_structure_branch[round, 2, col, 2, 0] == 1) >> (structure_state[round, 2, 2, col, 1] == 0)) #no red element

                    for i in range(2): #not three purple or fix
                        for j in range(2):
                            model.addConstr((MC_structure_branch[round, 2,col, 2, 0] == 1) >> (structure_state[round, 2, 1, col, 3+i] + structure_state[round, 2, 2, col, 3+j] <= 1))

                    #if a purple element without fix, previous state can only be purple or fix 
                    model.addConstr((MC_structure_branch[round, 2, col, 3, 0] == 1) >> (structure_state[round, 2, 1, col, 3] + structure_state[round, 2, 1, col, 4] == 1)) 
                    model.addConstr((MC_structure_branch[round, 2, col, 3, 0] == 1) >> (structure_state[round, 2, 2, col, 3] + structure_state[round, 2, 2, col, 4] == 1))

                    #if a purple element and 2 fix in second and last position, previous last element of same column can be purple or fix by backward prop
                    model.addConstr((MC_structure_branch[round, 2, col, 3, 3] == 1) >> (structure_state[round, 2, 1, col, 3] + structure_state[round, 2, 1, col, 4] == 2))    
                    
                    #fix, the previous element for calculation must not be blue or unknown
                    
                    model.addConstr((MC_structure_branch[round, 2, col, 4, 0] == 1) >> (structure_state[round, 2, 1, col, 0] == 0))
                    model.addConstr((MC_structure_branch[round, 2, col, 4, 0] == 1) >> (structure_state[round, 2, 2, col, 0] == 0))
                    
                    model.addConstr((MC_structure_branch[round, 2, col, 4, 0] == 1) >> (structure_state[round, 2, 2, col, 2] == 0))
                    model.addConstr((MC_structure_branch[round, 2, col, 4, 0] == 1) >> (structure_state[round, 2, 1, col, 2] == 0))
                    

                    #LASTLINE
                    model.addConstr(gp.quicksum(MC_structure_branch[round, 3, col, color, index] for color in range(5) for index in range(4)) == 1)
                    model.addConstr((MC_structure_branch[round, 3, col, 0, 0] == 1) >> (structure_state[round + 1, 0, 3, col, 0] == 1)) #unknow
                    model.addConstr((MC_structure_branch[round, 3, col, 1, 0] == 1) >> (structure_state[round + 1, 0, 3, col, 1] == 1)) #red
                    model.addConstr((MC_structure_branch[round, 3, col, 2, 0] == 1) >> (structure_state[round + 1, 0, 3, col, 2] == 1)) #blue
                    model.addConstr((MC_structure_branch[round, 3, col, 3, 0] == 1) >> (structure_state[round + 1, 0, 3, col, 3] == 1)) #purple and not fixe
                    #model.addConstr((MC_structure_branch[round, 3, col, 3, 0] == 1) >> (structure_state[round + 1, 0, 0, col, 4] == 0)) #purple and not fixe
                    #model.addConstr((MC_structure_branch[round, 3, col, 3, 0] == 1) >> (structure_state[round + 1, 0, 1, col, 4] == 0)) #purple and not fixe

                    model.addConstr((MC_structure_branch[round, 3, col, 3, 1] == 1) >> (structure_state[round + 1, 0, 3, col, 3] + structure_state[round + 1, 0, 0, col, 4] == 2)) #purple and one fixe
                                    
                    model.addConstr((MC_structure_branch[round, 3, col, 3, 2] == 1) >> (structure_state[round + 1, 0, 3, col, 3] + structure_state[round + 1, 0, 1, col, 4] == 2)) #purple and one fixe
                    #model.addConstr((MC_structure_branch[round, 3, col, 3, 2] == 1) >> (structure_state[round + 1, 0, 2, col, 4] == 0))
                                                                                        
                    model.addConstr((MC_structure_branch[round, 3, col, 3, 3] == 1) >> (structure_state[round + 1, 0, 3, col, 3]  + structure_state[round + 1, 0, 2, col, 4] + structure_state[round+1, 0, 1, col, 4] == 3)) #purple and 2 fixe
                    
                    model.addConstr((MC_structure_branch[round, 3, col, 4, 0] == 1) >> (structure_state[round + 1, 0, 3, col, 4] == 1)) #fixe
                    
                    #unkwown
                    for i in [1,3,4]:
                        for j in [1,3,4]:
                            model.addConstr((MC_structure_branch[round, 3, col, 0, 0] == 1) >> (structure_state[round, 2, 0, col, i] + structure_state[round, 2, 2, col, j] <= 1)) #unknow element can come to a red known XOR

                    for i in [2,3,4]:
                        for j in [2,3,4]:
                            model.addConstr((MC_structure_branch[round, 3, col, 0, 0] == 1) >> (structure_state[round, 2, 0, col, i] + structure_state[round, 2, 2, col, j] <= 1)) #unknow element can come to a blue known XOR

                    #if a red element
                    model.addConstr((MC_structure_branch[round, 3, col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 0] == 0)) #no unknown element 
                    model.addConstr((MC_structure_branch[round, 3, col, 1, 0] == 1) >> (structure_state[round, 2, 2, col, 0] == 0)) #no unknown element

                    model.addConstr((MC_structure_branch[round, 3, col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 2] == 0)) #no blue element 
                    model.addConstr((MC_structure_branch[round, 3, col, 1, 0] == 1) >> (structure_state[round, 2, 2, col, 2] == 0)) #no blue element

                    for i in range(2): #not three purple or fix
                        for j in range(2):
                            model.addConstr((MC_structure_branch[round, 3,col, 1, 0] == 1) >> (structure_state[round, 2, 0, col, 3+i] + structure_state[round, 2, 2, col, 3+j] <= 1))

                    #if a blue element
                    model.addConstr((MC_structure_branch[round, 3, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 0] == 0)) #no unknown element 
                    model.addConstr((MC_structure_branch[round, 3, col, 2, 0] == 1) >> (structure_state[round, 2, 2, col, 0] == 0)) #no unknown element

                    model.addConstr((MC_structure_branch[round, 3, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 1] == 0)) #no red element 
                    model.addConstr((MC_structure_branch[round, 3, col, 2, 0] == 1) >> (structure_state[round, 2, 2, col, 1] == 0)) #no red element

                    for i in range(2): #not three purple or fix
                        for j in range(2):
                            model.addConstr((MC_structure_branch[round, 3, col, 2, 0] == 1) >> (structure_state[round, 2, 0, col, 3+i] + structure_state[round, 2, 2, col, 3+j] <= 1))

                    #if a purple element without fix, previous state can only be purple
                    model.addConstr((MC_structure_branch[round, 3, col, 3, 0] == 1) >> (structure_state[round, 2, 0, col, 3] + structure_state[round, 2, 0, col, 4] == 1)) 
                    model.addConstr((MC_structure_branch[round, 3, col, 3, 0] == 1) >> (structure_state[round, 2, 2, col, 3] + structure_state[round, 2, 2, col, 4] == 1))

                    #if a purple element with a fix in first position
                    model.addConstr((MC_structure_branch[round, 3, col, 3, 1] == 1) >> (structure_state[round, 2, 3, col, 3] + structure_state[round, 2, 3, col, 4] == 1))

                    #if a purple element with a fix in second position
                    model.addConstr((MC_structure_branch[round, 3, col, 3, 2] == 1) >> (structure_state[round, 2, 2, col, 3] + structure_state[round, 2, 2, col, 4] == 1))

                    #if a purple element and 2 fix in second and third position, previous last element of same column can be purple or fix by backward prop
                    model.addConstr((MC_structure_branch[round, 3, col, 3, 3] == 1) >> (structure_state[round, 2, 1, col, 3] + structure_state[round, 2, 1, col, 4] == 1))    
                    
                    #fix
                    model.addConstr((MC_structure_branch[round, 3, col, 4, 0] == 1) >> (structure_state[round, 2, 0, col, 0] == 0)) 
                    model.addConstr((MC_structure_branch[round, 3, col, 4, 0] == 1) >> (structure_state[round, 2, 2, col, 0] == 0))
                    
                    model.addConstr((MC_structure_branch[round, 3, col, 4, 0] == 1) >> (structure_state[round, 2, 2, col, 2] == 0))
                    model.addConstr((MC_structure_branch[round, 3, col, 4, 0] == 1) >> (structure_state[round, 2, 0, col, 2] == 0))
                    
        ### MITM up constraints
        for round in range(MITM_up_round):
            for step in range(3):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(gp.quicksum(MITM_up_state[round, step, row, col, color] for color in range(3)) == 1) #state can be only unknow, blue or state tested

        #state test is performed just after MC
        for round in range(MITM_up_round):
            for step in range(1, 3):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(MITM_up_state[round, step, row, col, 2] == 0)
        
        #state test is performed only where the difference is known
        for round in range(MITM_up_round):
                for row in range(4):
                    for col in range(4):
                        model.addConstr((differential_up_state[round, 0, row, col, 0] == 1) >> (MITM_up_state[round, 0, row, col, 2] == 0))
        
        #state tests are necessarly useless in the first two round of MITM
        for row in range(4):
            for col in range(4):
                model.addConstr((MITM_up_state[0, 0, row, col, 2] == 0))
                model.addConstr((MITM_up_state[1, 0, row, col, 2] == 0))
        
        #state test are made only if at least one difference in the link differences before MC are zero (if not,state test is useless)
        for round in range(1,MITM_up_round):
            for col in range(4):
                model.addConstr((MITM_up_state[round, 0, 0, col, 2] == 1) >> (gp.quicksum(differential_up_state[round-1, 1, row_diff, col, 0] for row_diff in [0,2,3]) >= 1))
                model.addConstr((MITM_up_state[round, 0, 1, col, 2] == 1) >> (gp.quicksum(differential_up_state[round-1, 1, row_diff, col, 0] for row_diff in [1]) >= 1))
                model.addConstr((MITM_up_state[round, 0, 2, col, 2] == 1) >> (gp.quicksum(differential_up_state[round-1, 1, row_diff, col, 0] for row_diff in [1,2]) >= 1))
                model.addConstr((MITM_up_state[round, 0, 3, col, 2] == 1) >> (gp.quicksum(differential_up_state[round-1, 1, row_diff, col, 0] for row_diff in [0,2]) >= 1))
        
        #to ensure state test to be usefull, they need to make us win at least two key
        for round in range(2,MITM_up_round):
            for row in range(4):
                for col in range(4):
                    model.addConstr((MITM_up_state[round, 0, row, col, 2] == 1) >> (gp.quicksum(MITM_up_state[round-2, 1, row_2, col_2, 0] for row_2 in range(2) for col_2 in range(4)) >= 2))
        
        #key addition
        for round in range(MITM_up_round):
            for row in range(2):
                for col in range(4):
                    #state is unknow if the key is red or unknow or if the state before key addition is unknow
                    model.addConstr(MITM_up_state[round, 1, row, col, 0] == gp.or_(MITM_up_state[round, 0, row, col, 0], full_key[round + structure_round, 0, row, col, 0], full_key[round + structure_round, 0, row, col, 1])) 
            for row in range(2,4):
                for col in range(4):
                    #AK is not made on the two last rows
                    model.addConstr(MITM_up_state[round, 1, row, col, 0] == MITM_up_state[round, 0, row, col, 0])

        #permutation
        for round in range(MITM_up_round):
            for col in range(4):

                    model.addConstr((MITM_up_state[round, 1, 0, col, 1] == 1) >> (MITM_up_state[round, 2, 0, col, 1] == 1))
                    model.addConstr((MITM_up_state[round, 1, 1, col, 1] == 1) >> (MITM_up_state[round, 2, 1, (col +1) % 4, 1] == 1))
                    model.addConstr((MITM_up_state[round, 1, 2, col, 1] == 1) >> (MITM_up_state[round, 2, 2, (col +2) % 4, 1] == 1))
                    model.addConstr((MITM_up_state[round, 1, 3, col, 1] == 1) >> (MITM_up_state[round, 2, 3, (col +3) % 4, 1] == 1))


                    model.addConstr((MITM_up_state[round, 1, 0, col, 0] == 1) >> (MITM_up_state[round, 2, 0, col, 0] == 1))
                    model.addConstr((MITM_up_state[round, 1, 1, col, 0] == 1) >> (MITM_up_state[round, 2, 1, (col +1) % 4, 0] == 1))
                    model.addConstr((MITM_up_state[round, 1, 2, col, 0] == 1) >> (MITM_up_state[round, 2, 2, (col +2) % 4, 0] == 1))
                    model.addConstr((MITM_up_state[round, 1, 3, col, 0] == 1) >> (MITM_up_state[round, 2, 3, (col +3) % 4, 0] == 1))
        
        #MC
        for round in range(MITM_up_round - 1):
                for col in range(4):
                    model.addConstr((MITM_up_state[round+1, 0, 0, col, 1] == gp.and_(MITM_up_state[round, 2, row, col, 1] for row in [0, 2, 3])))
                    model.addConstr((MITM_up_state[round+1, 0, 1, col, 1] == gp.and_(MITM_up_state[round, 2, row, col, 1] for row in [0])))
                    model.addConstr((MITM_up_state[round+1, 0, 2, col, 1] == gp.and_(MITM_up_state[round, 2, row, col, 1] for row in [1, 2])))
                    model.addConstr((MITM_up_state[round+1, 0, 3, col, 1] == gp.and_(MITM_up_state[round, 2, row, col, 1] for row in [0, 2])))

        ###DIFFERENTIAL UP constraints
        for round in range(MITM_up_round):
            for step in range(2):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(gp.quicksum(differential_up_state[round, step, row, col, color] for color in range(3)) == 1) #state can only be unknown, blue or guess
        
        #probabilist key recovery only made through MC
        for round in range(MITM_up_round):
            for row in range(4):
                for col in range(4):
                    model.addConstr(differential_up_state[round, 0, row, col, 2] == 0)

        #MC-1
        for round in range(MITM_up_round-1):
            for col in range(4):
                model.addConstr(differential_up_state[round, 1, 0, col, 0] == gp.and_(differential_up_state[round + 1, 0, row, col, 0] for row in [1]))
                model.addConstr(differential_up_state[round, 1, 1, col, 0] == gp.and_(differential_up_state[round + 1, 0, row, col, 0]for row in [1,2,3]))
                model.addConstr(differential_up_state[round, 1, 2, col, 0] == gp.and_(differential_up_state[round + 1, 0, row, col, 0] for row in [1,3]))
                model.addConstr(differential_up_state[round, 1, 3, col, 0] == gp.and_(differential_up_state[round + 1, 0, row, col, 0] for row in [0,3]))
                
                model.addConstr(differential_up_state[round, 1, 0, col, 2] == 0)
                model.addConstr((differential_up_state[round, 1, 1, col, 2] == 1) >> (differential_up_state[round+1, 0, 1, col, 1]+ differential_up_state[round+1, 0, 3, col, 1]  + differential_up_state[round+1, 0, 2, col, 1] >= 2))
                model.addConstr((differential_up_state[round, 1, 2, col, 2] == 1) >> (differential_up_state[round+1, 0, 1, col, 1]+ differential_up_state[round+1, 0, 3, col, 1] == 2))
                model.addConstr((differential_up_state[round, 1, 3, col, 2] == 1) >> (differential_up_state[round+1, 0, 0, col, 1]+ differential_up_state[round+1, 0, 3, col, 1] == 2))

                model.addConstr(differential_up_state[round, 1, 0, col, 3] == 0)
                model.addConstr(differential_up_state[round, 1, 1, col, 3] == gp.and_(differential_up_state[round, 1, 2, col, 2],differential_up_state[round +1, 0, 2, col, 0]))
                model.addConstr(differential_up_state[round, 1, 2, col, 3] == 0)
                model.addConstr(differential_up_state[round, 1, 3, col, 3] == 0)
    
    
        #permutation-1
        for round in range(MITM_up_round):
            for col in range(4):
                model.addConstr(differential_up_state[round, 0, 0, col, 1] == differential_up_state[round, 1, 0, col, 1])
                model.addConstr(differential_up_state[round, 0, 1, col, 1] == differential_up_state[round, 1, 1, (col +1) % 4, 1])
                model.addConstr(differential_up_state[round, 0, 2, col, 1] == differential_up_state[round, 1, 2, (col +2) % 4, 1])
                model.addConstr(differential_up_state[round, 0, 3, col, 1] == differential_up_state[round, 1, 3, (col +3) % 4, 1])

        #differential need to be known after SB by value (MITM)
        for round in range(MITM_up_round):
            for row in range(4):
                for col in range(4):
                    model.addConstr((differential_up_state[round, 0, row, col, 1] == 1) >> (MITM_up_state[round, 0, row, col, 0] == 0))

        #with differential dist, we need to know the last state before the distinguisher
        for row in range(4):
            for col in range(4):
                model.addConstr((differential_up_state[MITM_up_round-1, 1, row, col, 1] == 1) >> (MITM_up_state[MITM_up_round-1, 2, row, col, 0] == 0))
        
        ###TRUNCATED FORWARD constraint
        """
        model.addConstr(differential_state[0, 0, 0, 0, 1] == 0)
        model.addConstr(differential_state[0, 0, 0, 1, 1] == 0)
        model.addConstr(differential_state[0, 0, 0, 2, 1] == 0)
        model.addConstr(differential_state[0, 0, 0, 3, 1] == 1)

        model.addConstr(differential_state[0, 0, 1, 0, 1] == 0)
        model.addConstr(differential_state[0, 0, 1, 1, 1] == 0)
        model.addConstr(differential_state[0, 0, 1, 2, 1] == 0)
        model.addConstr(differential_state[0, 0, 1, 3, 1] == 0)

        model.addConstr(differential_state[0, 0, 2, 0, 1] == 0)
        model.addConstr(differential_state[0, 0, 2, 1, 1] == 0)
        model.addConstr(differential_state[0, 0, 2, 2, 1] == 0)
        model.addConstr(differential_state[0, 0, 2, 3, 1] == 0)

        model.addConstr(differential_state[0, 0, 3, 0, 1] == 1)
        model.addConstr(differential_state[0, 0, 3, 1, 1] == 0)
        model.addConstr(differential_state[0, 0, 3, 2, 1] == 0)
        model.addConstr(differential_state[0, 0, 3, 3, 1] == 0)

        model.addConstr(differential_state[differential_round-1, 0, 0, 0, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 0, 1, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 0, 2, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 0, 3, 1] == 0)

        model.addConstr(differential_state[differential_round-1, 0, 1, 0, 1] == 1)
        model.addConstr(differential_state[differential_round-1, 0, 1, 1, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 1, 2, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 1, 3, 1] == 0)

        model.addConstr(differential_state[differential_round-1, 0, 2, 0, 1] == 1)
        model.addConstr(differential_state[differential_round-1, 0, 2, 1, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 2, 2, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 2, 3, 1] == 0)

        model.addConstr(differential_state[differential_round-1, 0, 3, 0, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 3, 1, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 3, 2, 1] == 0)
        model.addConstr(differential_state[differential_round-1, 0, 3, 3, 1] == 0)
        """
        
        #Color constraints
        for round in range(differential_round):
            for step in range(2):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(gp.quicksum(differential_state[round, step, row, col, color] for color in range(4)) == 1) #State can only be 0, known differential, or guessed differential 
        
        #start, bacward propagation with proba 1 in the differential up state
        for col in range(4):
            model.addConstr(differential_up_state[MITM_up_round - 1, 1, 0, col, 1] == differential_state[0, 0, 1, col, 1])
            model.addConstr((differential_up_state[MITM_up_round - 1, 1, 1, col, 1]) == gp.or_(differential_state[0, 0, row, col, 1] for row in [1, 2, 3]))
            model.addConstr((differential_up_state[MITM_up_round - 1, 1, 2, col, 1]) == gp.or_(differential_state[0, 0, row, col, 1] for row in [1, 3]))
            model.addConstr((differential_up_state[MITM_up_round - 1, 1, 3, col, 1]) == gp.or_(differential_state[0, 0, row, col, 1] for row in [0, 3]))

            model.addConstr((differential_up_state[MITM_up_round - 1, 1, 0, col, 0]) == (differential_state[0, 0, 1, col, 0]))
            model.addConstr((differential_up_state[MITM_up_round - 1, 1, 1, col, 0]) == gp.and_(differential_state[0, 0, row, col, 0] for row in [1, 2, 3]))
            model.addConstr((differential_up_state[MITM_up_round - 1, 1, 2, col, 0]) == gp.and_(differential_state[0, 0, row, col, 0] for row in [1, 3]))
            model.addConstr((differential_up_state[MITM_up_round - 1, 1, 3, col, 0]) == gp.and_(differential_state[0, 0, row, col, 0] for row in [0, 3]))

            for row in range(4):
                model.addConstr(differential_state[0,0,row,col,2] == 0)
                model.addConstr(differential_state[0,0,row,col,3] == 0)
        
        #end, forward propagation with proba 1 in the differential down state
        for col in range(4):
            model.addConstr((differential_down_state[0, 0, 0, col, 1]) == gp.or_(differential_state[differential_round-1, 1, row, col, 1] for row in [0,2,3]))
            model.addConstr((differential_down_state[0, 0, 1, col, 1]) == gp.or_(differential_state[differential_round-1, 1, row, col, 1] for row in [0]))
            model.addConstr((differential_down_state[0, 0, 2, col, 1]) == gp.or_(differential_state[differential_round-1, 1, row, col, 1] for row in [1, 2]))
            model.addConstr((differential_down_state[0, 0, 3, col, 1]) == gp.or_(differential_state[differential_round-1, 1, row, col, 1] for row in [0, 2]))
            
            model.addConstr((differential_down_state[0, 0, 0, col, 0]) == gp.and_(differential_state[differential_round-1, 1, row, col, 0] for row in [0, 2, 3]))
            model.addConstr((differential_down_state[0, 0, 1, col, 0]) == gp.and_(differential_state[differential_round-1, 1, row, col, 0] for row in [0]))
            model.addConstr((differential_down_state[0, 0, 2, col, 0]) == gp.and_(differential_state[differential_round-1, 1, row, col, 0] for row in [1, 2]))
            model.addConstr((differential_down_state[0, 0, 3, col, 0]) == gp.and_(differential_state[differential_round-1, 1, row, col, 0] for row in [0, 2]))
        
        #states can never be fully unkown or fully know to be a valid truncated distinguisher
        for round in range(differential_round):
            for step in range(2):
                model.addConstr(gp.quicksum(differential_state[round, step, row, col, 0] for row in range(4) for col in range(4)) <= 15)
                model.addConstr(gp.quicksum(differential_state[round, step, row, col, 0] for row in range(4) for col in range(4)) >= 1)
                model.addConstr(gp.quicksum(differential_state[round, step, row, col, 1] for row in range(4) for col in range(4)) <= 15)
    
        #permutation
        for round in range(0, differential_round):
            for col in range(4):
                model.addConstr((differential_state[round, 0, 0, col, 2] == 1) >> (differential_state[round, 1, 0, col, 0] == 1))
                model.addConstr((differential_state[round, 0, 1, col, 2] == 1) >> (differential_state[round, 1, 1, (col +1) % 4, 0] == 1))
                model.addConstr((differential_state[round, 0, 2, col, 2] == 1) >> (differential_state[round, 1, 2, (col +2) % 4, 0] == 1))
                model.addConstr((differential_state[round, 0, 3, col, 2] == 1) >> (differential_state[round, 1, 3, (col +3) % 4, 0] == 1))
                
                model.addConstr((differential_state[round, 0, 0, col, 3] == 1) >> (differential_state[round, 1, 0, col, 0] == 1))
                model.addConstr((differential_state[round, 0, 1, col, 3] == 1) >> (differential_state[round, 1, 1, (col +1) % 4, 0] == 1))
                model.addConstr((differential_state[round, 0, 2, col, 3] == 1) >> (differential_state[round, 1, 2, (col +2) % 4, 0] == 1))
                model.addConstr((differential_state[round, 0, 3, col, 3] == 1) >> (differential_state[round, 1, 3, (col +3) % 4, 0] == 1))
                
                model.addConstr((differential_state[round, 0, 0, col, 0] == 1) >> (differential_state[round, 1, 0, col, 0] == 1 ))
                model.addConstr((differential_state[round, 0, 1, col, 0] == 1) >> (differential_state[round, 1, 1, (col +1) % 4, 0]== 1))
                model.addConstr((differential_state[round, 0, 2, col, 0] == 1) >> (differential_state[round, 1, 2, (col +2) % 4, 0] == 1))
                model.addConstr((differential_state[round, 0, 3, col, 0] == 1) >> (differential_state[round, 1, 3, (col +3) % 4, 0] == 1))
                
                model.addConstr((differential_state[round, 0, 0, col, 1] == 1) >> (differential_state[round, 1, 0, col, 1] == 1))
                model.addConstr((differential_state[round, 0, 1, col, 1] == 1) >> (differential_state[round, 1, 1, (col +1) % 4, 1] == 1))
                model.addConstr((differential_state[round, 0, 2, col, 1] == 1) >> (differential_state[round, 1, 2, (col +2) % 4, 1] == 1))
                model.addConstr((differential_state[round, 0, 3, col, 1] == 1) >> (differential_state[round, 1, 3, (col +3) % 4, 1] == 1))
            
        #MC
        for round in range(differential_round-1):
            for col in range(4):
                model.addConstr((differential_state[round+1, 0, 0, col, 0] == gp.and_(differential_state[round, 1, row, col, 0] for row in [0, 2, 3])))
                model.addConstr((differential_state[round+1, 0, 1, col, 0] == gp.and_(differential_state[round, 1, row, col, 0] for row in [0])))
                model.addConstr((differential_state[round+1, 0, 2, col, 0] == gp.and_(differential_state[round, 1, row, col, 0] for row in [1, 2])))
                model.addConstr((differential_state[round+1, 0, 3, col, 0] == gp.and_(differential_state[round, 1, row, col, 0] for row in [0, 2])))
                
                model.addConstr((differential_state[round+1, 0, 0, col, 2] == 1) >> (differential_state[round, 1, 0, col, 1] + differential_state[round, 1, 2, col, 1] + differential_state[round, 1, 3, col, 1] >= 2))
                model.addConstr(differential_state[round+1, 0, 0, col, 3] == gp.and_((differential_state[round+1, 0, row, col, 2] for row in [3]),(differential_state[round, 1, row, col, 0] for row in [3])))

                model.addConstr((differential_state[round+1, 0, 1, col, 2] == 0))
                model.addConstr((differential_state[round+1, 0, 1, col, 3] == 0))

                model.addConstr((differential_state[round+1, 0, 2, col, 2] == 1) >> (differential_state[round, 1, 1, col, 1] + differential_state[round, 1, 2, col, 1] == 2))
                model.addConstr((differential_state[round+1, 0, 2, col, 3] == 0))
                
                model.addConstr((differential_state[round+1, 0, 3, col, 2] == 1) >> (differential_state[round, 1, 0, col, 1] + differential_state[round, 1, 2, col, 1] == 2))
                model.addConstr((differential_state[round+1, 0, 3, col, 3] == 0))

                for row in range(4):
                    model.addConstr((differential_state[round, 1, row, col, 3] == 0))
                    model.addConstr((differential_state[round, 1, row, col, 2] == 0))
        
        #Validity condition of truncated
        model.addConstr(16 - objective_differential_end >= cost_differential)

        ###DIFFERENTIAL DOWN constraints
        for round in range(MITM_down_round):
            for step in range(2):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(gp.quicksum(differential_down_state[round, step, row, col, color] for color in range(3)) == 1) 
        
        #probabilist key recovery only through MC
        for round in range(MITM_down_round):
            for row in range(4):
                for col in range(4):
                    model.addConstr(differential_down_state[round, 1, row, col, 2] == 0)

        #MC
        for round in range(MITM_down_round-1):
            for col in range(4):
                model.addConstr(differential_down_state[round + 1, 0, 0, col, 0] == gp.and_(differential_down_state[round, 1, row, col, 0] for row in [0, 2, 3]))
                model.addConstr(differential_down_state[round + 1, 0, 1, col, 0] == gp.and_(differential_down_state[round, 1, 0, col, 0] ))
                model.addConstr(differential_down_state[round + 1, 0, 2, col, 0] == gp.and_(differential_down_state[round, 1, row, col, 0] for row in [1, 2]))
                model.addConstr(differential_down_state[round + 1, 0, 3, col, 0] == gp.and_(differential_down_state[round, 1, row, col, 0] for row in [0, 2]))
                
                model.addConstr(differential_down_state[round + 1, 0, 0, col, 3] == gp.and_(differential_down_state[round + 1, 0, 3, col, 2], differential_down_state[round, 1, 3, col, 0]))
                model.addConstr(differential_down_state[round + 1, 0, 1, col, 3] == 0)
                model.addConstr(differential_down_state[round + 1, 0, 2, col, 3] == 0)
                model.addConstr(differential_down_state[round + 1, 0, 3, col, 3] == 0)
                                                                
                model.addConstr((differential_down_state[round + 1, 0, 3, col, 2] == 1) >> (differential_down_state[round, 1, 0, col, 1] + differential_down_state[round, 1, 3, col, 1] == 2 ))
                model.addConstr((differential_down_state[round + 1, 0, 2, col, 2] == 1) >> (differential_down_state[round, 1, 1, col, 1] + differential_down_state[round, 1, 3, col, 1] == 2 ))
                model.addConstr((differential_down_state[round + 1, 0, 0, col, 2] == 1) >> (differential_down_state[round, 1, 1, col, 1] + differential_down_state[round, 1, 2, col, 1] + differential_down_state[round, 1, 3, col, 1] >= 2 ))
                model.addConstr((differential_down_state[round + 1, 0, 1, col, 2]) == 0)

        #permutation
        for round in range(MITM_down_round):
            for col in range(4):
                model.addConstr(differential_down_state[round, 0, 0, col, 1] == differential_down_state[round, 1, 0, col, 1])
                model.addConstr(differential_down_state[round, 0, 1, col, 1] == differential_down_state[round, 1, 1, (col +1) % 4, 1])
                model.addConstr(differential_down_state[round, 0, 2, col, 1] == differential_down_state[round, 1, 2, (col +2) % 4, 1])
                model.addConstr(differential_down_state[round, 0, 3, col, 1] == differential_down_state[round, 1, 3, (col +3) % 4, 1])
        
        #Link between MITM down and differential down
        for round in range(MITM_down_round):
            for row in range(4):
                for col in range(4):
                    model.addConstr((differential_down_state[round, 0, row, col, 1] == 1) >> (MITM_down_state[round, 0, row, col, 0] == 0))
        
        ### MITM DOWN constraints
        for round in range(MITM_down_round):
            for step in range(3):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(gp.quicksum(MITM_down_state[round, step, row, col, color] for color in range(3)) == 1) 
        
        #state test is performed only after MC (before M-1)
        for round in range(MITM_down_round):
            for step in range(1,3):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(MITM_down_state[round, step, row, col, 2] == 0)
        
        #state test is performed only where the difference is known
        for round in range(MITM_down_round):
                for row in range(4):
                    for col in range(4):
                        model.addConstr((differential_down_state[round, 0, row, col, 0] == 1) >> (MITM_down_state[round, 0, row, col, 2] == 0))
        
        #state test are necessrly useless in the last round of the MITM
        for row in range(4):
            for col in range(4):
                    model.addConstr((MITM_down_state[MITM_down_round-1, 0, row, col, 2] == 0))
        
        #state test are made only if some differences are zero in the next round (if not state test are non sense)
        for round in range(0,MITM_down_round-1):
            for col in range(4):
                model.addConstr((MITM_down_state[round, 0, 0, col, 2] == 1) >> (gp.quicksum(differential_down_state[round+1, 0, row_diff, (col+1)%4, 0] for row_diff in [1]) >= 1))
                model.addConstr((MITM_down_state[round, 0, 1, col, 2] == 1) >> (gp.quicksum(differential_down_state[round+1, 0, row_diff, (col +row_diff)%4, 0] for row_diff in [1,2,3]) >= 1))
                model.addConstr((MITM_down_state[round, 0, 2, col, 2] == 1) >> (gp.quicksum(differential_down_state[round+1, 0, row_diff, (col +row_diff)%4, 0] for row_diff in [1,3]) >= 1))
                model.addConstr((MITM_down_state[round, 0, 3, col, 2] == 1) >> (gp.quicksum(differential_down_state[round+1, 0, row_diff, (col +row_diff)%4, 0] for row_diff in [0,3]) >= 1))
        
        #to ensure state test to be usefull, they need to make us win at least two key
        for round in range(MITM_down_round-1):
            for row in range(4):
                for col in range(4):
                    model.addConstr((MITM_down_state[round, 0, row, col, 2] == 1) >> (gp.quicksum(MITM_down_state[round+1, 0, row_2, col_2, 0] for row_2 in range(2) for col_2 in range(4)) >= 1))
        
        #MC
        for round in range(MITM_down_round - 1):
            for col in range(4):
                model.addConstr((MITM_down_state[round, 2, 0, col, 0] == gp.or_(MITM_down_state[round + 1, 0, row, col, 0] for row in [1])))
                model.addConstr((MITM_down_state[round, 2, 1, col, 0] == gp.or_(MITM_down_state[round + 1, 0, row, col, 0] for row in [1, 2, 3])))
                model.addConstr((MITM_down_state[round, 2, 2, col, 0] == gp.or_(MITM_down_state[round + 1, 0, row, col, 0] for row in [1, 3])))
                model.addConstr((MITM_down_state[round, 2, 3, col, 0] == gp.or_(MITM_down_state[round + 1, 0, row, col, 0] for row in [0, 3])))

        #permutation
        for round in range(MITM_down_round):
            for col in range(4):
                for color in range(2):
                    model.addConstr((MITM_down_state[round, 1, 0, col, 1] == 1) >> (MITM_down_state[round, 2, 0, col, 1] == 1))
                    model.addConstr((MITM_down_state[round, 1, 1, col, 1] == 1) >> (MITM_down_state[round, 2, 1, (col +1) % 4, 1] == 1))
                    model.addConstr((MITM_down_state[round, 1, 2, col, 1] == 1) >> (MITM_down_state[round, 2, 2, (col +2) % 4, 1] == 1))
                    model.addConstr((MITM_down_state[round, 1, 3, col, 1] == 1) >> (MITM_down_state[round, 2, 3, (col +3) % 4, 1] == 1))

                    model.addConstr((MITM_down_state[round, 1, 0, col, 0] == 1) >> (MITM_down_state[round, 2, 0, col, 1] == 0))
                    model.addConstr((MITM_down_state[round, 1, 1, col, 0] == 1) >> (MITM_down_state[round, 2, 1, (col +1) % 4, 1] == 0))
                    model.addConstr((MITM_down_state[round, 1, 2, col, 0] == 1) >> (MITM_down_state[round, 2, 2, (col +2) % 4, 1] == 0))
                    model.addConstr((MITM_down_state[round, 1, 3, col, 0] == 1) >> (MITM_down_state[round, 2, 3, (col +3) % 4, 1] == 0))
        
        #key_add
        for round in range(MITM_down_round):
            for row in range(2):
                for col in range(4):
                    #model.addConstr(MITM_down_state[round, 0, row, col, 0] == gp.or_(MITM_down_state[round, 1, row, col, 0], full_key[round + structure_round + MITM_up_round, 0, row, col, 0], full_key[round + structure_round + MITM_up_round, 0, row, col, 2]))
                    model.addConstr((full_key[round + structure_round + MITM_up_round + differential_round, 0, row, col, 2] == 1) >> (MITM_down_state[round, 0, row, col, 1] == 0))
                    model.addConstr((full_key[round + structure_round + MITM_up_round + differential_round, 0, row, col, 0] == 1) >> (MITM_down_state[round, 0, row, col, 1] == 0))
                    model.addConstr((MITM_down_state[round, 1, row, col, 0] == 1) >> (MITM_down_state[round, 0, row, col, 1] == 0))
            for row in range(2,4):
                for col in range(4):
                    model.addConstr(MITM_down_state[round, 0, row, col, 0] == MITM_down_state[round, 1, row, col, 0])
        
        model.optimize()

        #SI on a trouvé une solution on formate le résultat et on l'affiche avec la fonction d'affichage
        if model.Status == GRB.OPTIMAL:
            compteur_rouge = count_red.getValue()
            compteur_bleu = count_blue.getValue()
            compteur_violet = count_equation.getValue()
            #compteur_differentielle = cost_differential
            compteur_differentielle = cost_differential.getValue()
            compteur_statetest_haut = state_test_up.getValue()
            compteur_statetest_bas = state_test_down.getValue()
            compteur_fix = fix_quantity_structure.getValue()
            compteur_proba_up = MITM_up_guess.getValue()
            compteur_proba_down = MITM_down_guess.getValue()
            Cblue= blue_complexity.getValue()
            Cred = red_complexity.getValue()
            Cmatch = MATCH_complexity.getValue()

            liste_X = [np.zeros((4, 4)) for i in range(total_round)]
            liste_Y = [np.zeros((4, 4)) for i in range(total_round)]
            liste_Z = [np.zeros((4, 4)) for i in range(total_round)]

            Liste_X_diff = [np.zeros((4, 4)) for i in range(total_round)]
            Liste_Y_diff = [np.zeros((4, 4)) for i in range(total_round)]

            for i in range(structure_round):
                for row in range(4):
                    for col in range(4):
                        if structure_state[i, 0, row, col, 0].X == 1.0:
                            liste_X[i][row, col] = 1
                        if structure_state[i, 0, row, col, 1].X == 1.0:
                            liste_X[i][row, col] = 2
                        if structure_state[i, 0, row, col, 2].X == 1.0:
                            liste_X[i][row, col] = 3
                        if structure_state[i, 0, row, col, 3].X == 1.0:
                            liste_X[i][row, col] = 5
                        if structure_state[i, 0, row, col, 4].X == 1.0:
                            liste_X[i][row, col] = -1

                        if structure_state[i, 1, row, col, 0].X == 1.0:
                            liste_Y[i][row, col] = 1
                        if structure_state[i, 1, row, col, 1].X == 1.0:
                            liste_Y[i][row, col] = 2
                        if structure_state[i, 1, row, col, 2].X == 1.0:
                            liste_Y[i][row, col] = 3
                        if structure_state[i, 1, row, col, 3].X == 1.0:
                            liste_Y[i][row, col] = 5
                        if structure_state[i, 1, row, col, 4].X == 1.0:
                            liste_Y[i][row, col] = -1

                        if structure_state[i, 2, row, col, 0].X == 1.0:
                            liste_Z[i][row, col] = 1
                        if structure_state[i, 2, row, col, 1].X == 1.0:
                            liste_Z[i][row, col] = 2
                        if structure_state[i, 2, row, col, 2].X == 1.0:
                            liste_Z[i][row, col] = 3
                        if structure_state[i, 2, row, col, 3].X == 1.0:
                            liste_Z[i][row, col] = 5
                        if structure_state[i, 2, row, col, 4].X == 1.0:
                            liste_Z[i][row, col] = -1

                        Liste_X_diff[i][row, col] = -1 
                        Liste_Y_diff[i][row, col] = -1 

            for i in range(MITM_up_round):
                for row in range(4):
                    for col in range(4):
                        if MITM_up_state[i, 0, row, col, 0].X == 1.0:
                            liste_X[structure_round + i][row, col] = 1
                        if MITM_up_state[i, 0, row, col,1].X == 1.0:
                            liste_X[structure_round + i][row, col] = 3
                        if MITM_up_state[i, 0, row, col, 2].X == 1.0:
                            liste_X[structure_round + i][row, col] = -1

                        if MITM_up_state[i, 1, row, col, 0].X == 1.0:
                            liste_Y[structure_round + i][row, col] = 1
                        if MITM_up_state[i, 1, row, col, 1].X == 1.0:
                            liste_Y[structure_round + i][row, col] = 3
                        if MITM_up_state[i, 1, row, col, 2].X == 1.0:
                            liste_Y[structure_round + i][row, col] = -1

                        if MITM_up_state[i, 2, row, col, 0].X == 1.0:
                            liste_Z[structure_round + i][row, col] = 1
                        if MITM_up_state[i, 2, row, col, 1].X == 1.0:
                            liste_Z[structure_round + i][row, col] = 3
                        if MITM_up_state[i, 2, row, col, 2].X == 1.0:
                            liste_Z[structure_round + i][row, col] = -1 

                        if differential_up_state[i, 0, row, col, 0].X == 1.0:
                            Liste_X_diff[structure_round + i][row, col] = 1
                        
                        if differential_up_state[i, 0, row, col, 1].X == 1.0:
                            Liste_X_diff[structure_round + i][row, col] = 3

                        if differential_up_state[i, 1, row, col, 0].X == 1.0:
                            Liste_Y_diff[structure_round + i][row, col] = 1
                        
                        if differential_up_state[i, 1, row, col, 1].X == 1.0:
                            Liste_Y_diff[structure_round + i][row, col] = 3 

                        if differential_up_state[i, 1, row, col, 2].X == 1.0:
                            Liste_Y_diff[structure_round + i][row, col] = -1   
            
            for i in range(differential_round):
                for row in range(4):
                    for col in range(4):
                        if differential_state[i, 0, row, col, 0].X == 1.0:
                            liste_X[structure_round + MITM_up_round + i][row, col] = 1       
                        if differential_state[i, 0, row, col,1].X == 1.0:
                            liste_X[structure_round + MITM_up_round + i][row, col] = 5
                        if differential_state[i, 0, row, col,2].X == 1.0:
                            liste_X[structure_round + MITM_up_round + i][row, col] = -1
                        if differential_state[i, 0, row, col,3].X == 1.0:
                            liste_X[structure_round + MITM_up_round + i][row, col] = 0
                        
                        if differential_state[i, 1, row, col, 0].X == 1.0:
                            liste_Y[structure_round + MITM_up_round + i][row, col] = 1       
                        if differential_state[i, 1, row, col, 1].X == 1.0:
                            liste_Y[structure_round + MITM_up_round + i][row, col] = 5
                        if differential_state[i, 1, row, col, 2].X == 1.0:
                            liste_Y[structure_round + MITM_up_round + i][row, col] = -1
                        if differential_state[i, 1, row, col, 3].X == 1.0:
                            liste_Y[structure_round + MITM_up_round + i][row, col] = -1

            for i in range(MITM_down_round):
                for row in range(4):
                    for col in range(4):
                        if MITM_down_state[i, 0, row, col, 1].X == 1.0:
                            liste_X[structure_round + MITM_up_round + differential_round + i][row, col] = 2
                        if MITM_down_state[i, 1, row, col, 1].X == 1.0:
                            liste_Y[structure_round + MITM_up_round + differential_round + i][row, col] = 2
                        if MITM_down_state[i, 2, row, col, 1].X == 1.0:
                            liste_Z[structure_round + MITM_up_round + differential_round + i][row, col] = 2
                        
                        if MITM_down_state[i, 0, row, col, 0].X == 1.0:
                            liste_X[structure_round + MITM_up_round + differential_round + i][row, col] = 1
                        if MITM_down_state[i, 1, row, col, 0].X == 1.0:
                            liste_Y[structure_round + MITM_up_round + differential_round + i][row, col] = 1
                        if MITM_down_state[i, 2, row, col, 0].X == 1.0:
                            liste_Z[structure_round + MITM_up_round + differential_round + i][row, col] = 1
                        
                        if MITM_down_state[i, 0, row, col, 2].X == 1.0:
                            liste_X[structure_round + MITM_up_round + differential_round + i][row, col] = -1
                        if MITM_down_state[i, 1, row, col, 2].X == 1.0:
                            liste_Y[structure_round + MITM_up_round + differential_round + i][row, col] = -1
                        if MITM_down_state[i, 2, row, col, 2].X == 1.0:
                            liste_Z[structure_round + MITM_up_round + differential_round + i][row, col] = -1
                        if differential_down_state[i, 0, row, col, 0].X == 1.0:
                            Liste_X_diff[structure_round + MITM_up_round + differential_round + i][row, col] = 1
                        
                        if differential_down_state[i, 0, row, col, 1].X == 1.0:
                            Liste_X_diff[structure_round + MITM_up_round + differential_round + i][row, col] = 2
                        
                        if differential_down_state[i, 0, row, col, 2].X == 1.0:
                            Liste_X_diff[structure_round + MITM_up_round + differential_round + i][row, col] = -1

                        if differential_down_state[i, 1, row, col, 0].X == 1.0:
                            Liste_Y_diff[structure_round + MITM_up_round + differential_round + i][row, col] = 1
                        
                        if differential_down_state[i, 1, row, col, 1].X == 1.0:
                            Liste_Y_diff[structure_round + MITM_up_round + differential_round + i][row, col] = 2

            key_M=np.zeros((total_round, 4, 4))
            for tour in range(structure_round):
                for row in range(4):
                    for col in range(4):
                        if full_key[tour, 0, row, col, 0].X == 1.0:
                            key_M[tour, row, col] = 1
                        if full_key[tour, 0, row, col, 1].X == 1.0:
                            key_M[tour, row, col] = 2
                        if full_key[tour, 0, row, col, 2].X == 1.0:
                            key_M[tour, row, col] = 3
                        if full_key[tour, 0, row, col, 3].X == 1.0:
                            key_M[tour, row, col] = 5

            for tour in range(MITM_up_round):
                for row in range(4):
                    for col in range(4):
                        if full_key[tour + structure_round, 0, row, col, 0].X == 1.0:
                            key_M[tour + structure_round, row, col] = 1
                        if full_key[tour + structure_round, 0, row, col, 1].X == 1.0:
                            key_M[tour + structure_round, row, col] = 2
                        if full_key[tour + structure_round, 0, row, col, 2].X == 1.0:
                            key_M[tour + structure_round, row, col] = 3
                        if full_key[tour + structure_round, 0, row, col, 3].X == 1.0:
                            key_M[tour + structure_round, row, col] = 5

            for tour in range(differential_round):
                for row in range(4):
                    for col in range(4):
                            key_M[tour + structure_round + MITM_up_round, row, col] = 0
            
            for tour in range(MITM_down_round):
                for row in range(4):
                    for col in range(4):
                        if full_key[tour + structure_round + MITM_up_round + differential_round, 0, row, col, 0].X == 1.0:
                            key_M[tour + structure_round + MITM_up_round + differential_round, row, col] = 1
                        if full_key[tour + structure_round + MITM_up_round+ differential_round, 0, row, col, 1].X == 1.0:
                            key_M[tour + structure_round + MITM_up_round + differential_round, row, col] = 2
                        if full_key[tour + structure_round + MITM_up_round+ differential_round, 0, row, col, 2].X == 1.0:
                            key_M[tour + structure_round + MITM_up_round + differential_round, row, col] = 3
                        if full_key[tour + structure_round + MITM_up_round+ differential_round, 0, row, col, 3].X == 1.0:
                            key_M[tour + structure_round + MITM_up_round + differential_round, row, col] = 5


            key_0 = np.zeros((total_round, 4, 4))
            if key_space_size >= 2 :
                for tour in range(structure_round):
                    for row in range(4):
                        for col in range(4):
                            if full_key[tour, 1, row, col, 0].X == 1.0:
                                key_0[tour, row, col] = 1
                            if full_key[tour, 1, row, col, 1].X == 1.0:
                                key_0[tour, row, col] = 2
                            if full_key[tour, 1, row, col, 2].X == 1.0:
                                key_0[tour, row, col] = 3
                            if full_key[tour, 1, row, col, 3].X == 1.0:
                                key_0[tour, row, col] = 5

                for tour in range(MITM_up_round):
                    for row in range(4):
                        for col in range(4):
                            if full_key[tour + structure_round, 1, row, col, 0].X == 1.0:
                                key_0[tour + structure_round, row, col] = 1
                            if full_key[tour + structure_round, 1, row, col, 1].X == 1.0:
                                key_0[tour + structure_round, row, col] = 2
                            if full_key[tour + structure_round, 1, row, col, 2].X == 1.0:
                                key_0[tour + structure_round, row, col] = 3
                            if full_key[tour + structure_round, 1, row, col, 3].X == 1.0:
                                key_0[tour + structure_round, row, col] = 5
                
                for tour in range(differential_round):
                    for row in range(4):
                        for col in range(4):
                                key_0[tour + structure_round + MITM_up_round, row, col] = 0
                
                for tour in range(MITM_down_round):
                    for row in range(4):
                        for col in range(4):
                            if full_key[tour + structure_round + MITM_up_round+ differential_round, 1, row, col, 0].X == 1.0:
                                key_0[tour + structure_round + MITM_up_round + differential_round, row, col] = 1
                            if full_key[tour + structure_round + MITM_up_round+ differential_round, 1, row, col, 1].X == 1.0:
                                key_0[tour + structure_round + MITM_up_round + differential_round, row, col] = 2
                            if full_key[tour + structure_round + MITM_up_round+ differential_round, 1, row, col, 2].X == 1.0:
                                key_0[tour + structure_round + MITM_up_round + differential_round, row, col] = 3
                            if full_key[tour + structure_round + MITM_up_round+ differential_round, 1, row, col, 3].X == 1.0:
                                key_0[tour + structure_round + MITM_up_round + differential_round, row, col] = 5

            key_1=np.zeros((total_round, 4, 4))
            if key_space_size > 1:
                for tour in range(structure_round):
                    for row in range(4):
                        for col in range(4):
                            if full_key[tour, 2, row, col, 0].X == 1.0:
                                key_1[tour, row, col] = 1
                            if full_key[tour, 2, row, col, 1].X == 1.0:
                                key_1[tour, row, col] = 2
                            if full_key[tour, 2, row, col, 2].X == 1.0:
                                key_1[tour, row, col] = 3
                            if full_key[tour, 2, row, col, 3].X == 1.0:
                                key_1[tour, row, col] = 5

                for tour in range(MITM_up_round):
                    for row in range(4):
                        for col in range(4):
                            if full_key[tour + structure_round, 2, row, col, 0].X == 1.0:
                                key_1[tour + structure_round, row, col] = 1
                            if full_key[tour + structure_round, 2, row, col, 1].X == 1.0:
                                key_1[tour + structure_round, row, col] = 2
                            if full_key[tour + structure_round, 2, row, col, 2].X == 1.0:
                                key_1[tour + structure_round, row, col] = 3
                            if full_key[tour + structure_round, 2, row, col, 3].X == 1.0:
                                key_1[tour + structure_round, row, col] = 5
                
                for tour in range(differential_round):
                    for row in range(4):
                        for col in range(4):
                                key_1[tour + structure_round + MITM_up_round, row, col] = 0
                
                for tour in range(MITM_down_round):
                    for row in range(4):
                        for col in range(4):
                            if full_key[tour + MITM_up_round + structure_round+ differential_round, 2, row, col, 0].X == 1.0:
                                key_1[tour + structure_round + MITM_up_round + differential_round, row, col] = 1
                            if full_key[tour + MITM_up_round + structure_round+ differential_round, 2, row, col, 1].X == 1.0:
                                key_1[tour + structure_round + MITM_up_round + differential_round, row, col] = 2
                            if full_key[tour + MITM_up_round + structure_round+ differential_round, 2, row, col, 2].X == 1.0:
                                key_1[tour + structure_round + MITM_up_round + differential_round, row, col] = 3
                            if full_key[tour + MITM_up_round + structure_round+ differential_round, 2, row, col, 3].X == 1.0:
                                key_1[tour + structure_round + MITM_up_round + differential_round, row, col] = 5

            key_2=np.zeros((total_round, 4, 4))
            if key_space_size == 3:
                for tour in range(structure_round):
                    for row in range(4):
                        for col in range(4):
                            if full_key[tour, 3, row, col, 0].X == 1.0:
                                key_2[tour, row, col] = 1
                            if full_key[tour, 3, row, col, 1].X == 1.0:
                                key_2[tour, row, col] = 2
                            if full_key[tour, 3, row, col, 2].X == 1.0:
                                key_2[tour, row, col] = 3
                            if full_key[tour, 3, row, col, 3].X == 1.0:
                                key_2[tour, row, col] = 5

                for tour in range(MITM_up_round):
                    for row in range(4):
                        for col in range(4):
                            if full_key[tour + structure_round, 3, row, col, 0].X == 1.0:
                                key_2[tour + structure_round, row, col] = 1
                            if full_key[tour + structure_round, 3, row, col, 1].X == 1.0:
                                key_2[tour + structure_round, row, col] = 2
                            if full_key[tour + structure_round, 3, row, col, 2].X == 1.0:
                                key_2[tour + structure_round, row, col] = 3
                            if full_key[tour + structure_round, 3, row, col, 3].X == 1.0:
                                key_2[tour + structure_round, row, col] = 5
                
                for tour in range(differential_round):
                    for row in range(4):
                        for col in range(4):
                                key_2[tour + structure_round + MITM_up_round, row, col] = 0
                
                for tour in range(MITM_down_round):
                    for row in range(4):
                        for col in range(4):
                            if full_key[tour + structure_round + MITM_up_round+ differential_round, 3, row, col, 0].X == 1.0:
                                key_2[tour + structure_round + MITM_up_round + differential_round, row, col] = 1
                            if full_key[tour + structure_round + MITM_up_round+ differential_round, 3, row, col, 1].X == 1.0:
                                key_2[tour + structure_round + MITM_up_round + differential_round, row, col] = 2
                            if full_key[tour + structure_round + MITM_up_round+ differential_round, 3, row, col, 2].X == 1.0:
                                key_2[tour + structure_round + MITM_up_round + differential_round, row, col] = 3
                            if full_key[tour + structure_round + MITM_up_round+ differential_round, 3, row, col, 3].X == 1.0:
                                key_2[tour + structure_round + MITM_up_round + differential_round, row, col] = 5

            return(True, key_M, key_0, key_1, key_2, liste_X, liste_Y, liste_Z,Liste_X_diff, Liste_Y_diff, compteur_bleu, compteur_rouge, compteur_differentielle, compteur_fix, compteur_violet, compteur_statetest_haut, compteur_statetest_bas, compteur_proba_up, compteur_proba_down, Cblue, Cred, Cmatch)
        else :
            return([False])

