#Truncated_Differential_MITM MILP with fix difference
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

def affichage_grille(key, key_0, key_1, key_2, x_list, y_list, z_list, Liste_X_diff, Liste_Y_diff):
    """Display function of a structure, NO RETURN.

    Display the X,Y Z and key element of each round of a strucutre

    Parameters
    ----------
    key : np.array
        The original key of the structure

    x_list : list of np.array
        The list of the X state of each round

    y_list : list of np.array
        The list of the Y state of each round

    z_list : list of np.array
        The list of the Z state of each round
    """
    list_key = key
    list_key0 = key_0
    list_key1 = key_1
    list_key2 = key_2

    for i in range(len(x_list)):
        print("TOUR", i)
        print("  _ _X_ _    _ _Y_ _    _ _Z_ _      _K_E_Y_      _K_E_Y_0   _K_E_Y_1   _K_E_Y_2     _D_F_Y_    _D_F_Z_")
        for ligne in range(4):
            print("\033[90m|", end="")
            for colonne in range(4):
                if x_list[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif x_list[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif x_list[i][ligne, colonne] == 5 or \
                        x_list[i][ligne, colonne] == 25 or \
                        x_list[i][ligne, colonne] == 55 or \
                        x_list[i][ligne, colonne] == 35:
                    print("\033[95m ■", end="")
                elif x_list[i][ligne, colonne] == 7:
                    print("\033[93m ■", end="")
                elif x_list[i][ligne, colonne] == 11:
                    print("\033[96m ■", end="")
                elif x_list[i][ligne, colonne] == 1:
                    print("\033[90m ■", end="")
                elif x_list[i][ligne, colonne] == -1:
                    print("\033[95m F", end="")
                else:
                    print("\033[99m X", end="")
            print("\033[90m| |", end="")
            for colonne in range(4):
                if y_list[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif y_list[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif y_list[i][ligne, colonne] == 5 or \
                        y_list[i][ligne, colonne] == 25 or \
                        y_list[i][ligne, colonne] == 55 or \
                        y_list[i][ligne, colonne] == 35:
                    print("\033[95m ■", end="")
                elif y_list[i][ligne, colonne] == 7:
                    print("\033[93m ■", end="")
                elif y_list[i][ligne, colonne] == 11:
                    print("\033[96m ■", end="")
                elif y_list[i][ligne, colonne] == 1:
                    print("\033[90m ■", end="")
                elif y_list[i][ligne, colonne] == -1:
                    print("\033[95m F", end="")
                else:
                    print("\033[99m X", end="")
            print("\033[90m| |", end="")
            for colonne in range(4):
                if z_list[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif z_list[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif z_list[i][ligne, colonne] == 5 or \
                        z_list[i][ligne, colonne] == 25 or \
                        z_list[i][ligne, colonne] == 55 or \
                        z_list[i][ligne, colonne] == 35:
                    print("\033[95m ■", end="")
                elif z_list[i][ligne, colonne] == 7:
                    print("\033[93m ■", end="")
                elif z_list[i][ligne, colonne] == 11:
                    print("\033[96m ■", end="")
                elif z_list[i][ligne, colonne] == 1:
                    print("\033[90m ■", end="")
                elif z_list[i][ligne, colonne] == -1:
                    print("\033[95m F", end="")
                else:
                    print("\033[99m X", end="")
            print("\033[90m|   |", end="")
            for colonne in range(4):
                if list_key[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif list_key[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif list_key[i][ligne, colonne] == 5:
                    print("\033[95m ■", end="")
                else:
                    print("\033[90m ■", end="")
            print("\033[90m|   |", end="")            
            for colonne in range(4):
                if list_key0[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif list_key0[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif list_key0[i][ligne, colonne] == 5:
                    print("\033[95m ■", end="")
                else :
                    print("\033[90m ■", end="")
            print("\033[90m| |", end="")
            for colonne in range(4):
                if list_key1[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif list_key1[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif list_key1[i][ligne, colonne] == 5:
                    print("\033[95m ■", end="")
                else:
                    print("\033[90m ■", end="")
            print("\033[90m| |", end="")
            for colonne in range(4):
                if list_key2[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif list_key2[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif list_key2[i][ligne, colonne] == 5:
                    print("\033[95m ■", end="")
                else:
                    print("\033[90m ■", end="")
            print("\033[90m|   |", end="")
            for colonne in range(4):
                if Liste_X_diff[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif Liste_X_diff[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif Liste_X_diff[i][ligne, colonne] == 1:
                    print("\033[90m ■", end="")
                elif Liste_X_diff[i][ligne, colonne] == -1:
                    print("\033[99m X", end="")
                else:
                    print("\033[90m ■", end="")
            print("\033[90m| |", end="")
            for colonne in range(4):
                if Liste_Y_diff[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif Liste_Y_diff[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif Liste_Y_diff[i][ligne, colonne] == 1:
                    print("\033[90m ■", end="")
                elif Liste_Y_diff[i][ligne, colonne] == -1:
                    print("\033[99m X", end="")
                else:
                    print("\033[90m ■", end="")
            print("\033[90m|")
        print("  ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾      ‾ ‾ ‾ ‾      ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾      ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾\n \n")

options = {
"WLSACCESSID" : "bb41a17b-b3b2-40d7-8c1c-01d90a2e2170",
"WLSSECRET" : "4db1c96a-1e47-4fc9-83eb-28a57d08879f",
"LICENSEID" : 2534357
}

with gp.Env(params=options) as env, gp.Model(env=env) as model:
    
    #ATTACK PARAMETERS
    structure_round = 2
    MITM_up_round = 6
    differential_round = 9
    MITM_down_round = 6
    z=4
    probability_diff = 52
    start_diff = 4
    end_diff = 8

    key_space_size = 3

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
    
    MITM_up_state = np.zeros((MITM_up_round, 3, 4, 4, 2), dtype=object) #[indice tour, indice step, indice ligne, indice colonne, couleur(0 = inconnue, 1 = bleu)]
    
    MITM_down_state = np.zeros((MITM_down_round, 3, 4, 4, 2), dtype=object) #[indice tour, indice step, indice ligne, indice colonne, couleur(0 = inconnue, 1 = rouge)]

    differential_up_state = np.zeros((MITM_up_round, 2, 4, 4, 2), dtype=object) #[indice tour, indice step, indice lignem indice colonne, couleur(0=inconnue, 1 = connue)]

    differential_down_state = np.zeros((MITM_down_round, 2, 4, 4, 2), dtype=object) #[indice tour, indice step, indice lignem indice colonne, couleur(0=inconnue, 1 = connue)]

    differential_state = np.zeros((differential_round, 3, 4, 4, 4), dtype=object) #[indice tour, indice step, indice ligne, indice colonne, couleur(0 = inconnue, 1 = connue, 2 = guess)]

    full_key = np.zeros((total_round - differential_round, key_space_size + 1, 4, 4, 4), dtype = object) #[indice tour, indice clé, indice ligne, indice tour, couleur(0 = inconnue, 1 = rouge, 2 = bleu, 3 = violet)]

    key_knowledge = np.zeros((4, 4,key_space_size+1, 2), dtype = object) #[indice ligne, indice colonne, couleur (0 = rouge, 1 = bleu)]

    MC_structure_branch = np.zeros((structure_round - 1, 4, 4, 5, 4), dtype = object) #[round, row, column, color, number of fix in the state]

    binary_bound_for_key_knowledge = np.zeros((4, 4,key_space_size+1, 2, 2), dtype = object) #binary variable to constraint the key knowledge following the key schedule(if three or more word of the same key element are guess, all the corresponding element are guessed)

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
                    for color in range(2):
                        MITM_up_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f'MITM_down_round:{round},{step},{row},{col},{color}')

    for round in range(MITM_down_round):
        for step in range(3):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        MITM_down_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM_up_round:{round},{step},{row},{col},{color}")

    for round in range(MITM_down_round):
        for step in range(2):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        differential_down_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"differential_down_state:{round},{step},{row},{col},{color}")

    for round in range(MITM_up_round):
        for step in range(2):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        differential_up_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"differential_down_state:{round},{step},{row},{col},{color}")

    for round in range(differential_round):
        for step in range(3):
            for row in range(4):
                for col in range(4):
                    for color in range(4):
                        differential_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"differential_round:{round},{step},{row},{col},{color}")
    
    for round in range(total_round - differential_round):
        for index in range(key_space_size + 1):
            for row in range(4):
                for col in range(4):
                    for color in range(4):
                        full_key[round, index, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"structure_key:{round},{step},{row},{col},{color}")

    for row in range(4):
        for col in range(4):
            for key in range(key_space_size+1):
                for color in range(2):
                    key_knowledge[row, col, key, color] = model.addVar(lb = 0.0,ub = total_round, vtype = GRB.INTEGER, name = f'red_keyknowledge{row} {col} {color}')

    for round in range(structure_round-1):
        for row in range(4):
            for col in range(4):
                for color in range(5):
                    for fix in range(4):
                        MC_structure_branch[round, row, col, color, fix] = model.addVar(vtype = GRB.BINARY, name = f"MC_structure_branch:{round},{row},{col},{color},{fix}")

    #Optimization function
    objective_blue = gp.quicksum(full_key[round, key, row, col, color] for round in range(total_round-differential_round) for row in range(2) for key in range(key_space_size+1) for col in range(4) for color in [2,3])
    objective_red = gp.quicksum(full_key[round, key, row, col, color] for round in range(total_round-differential_round) for row in range(2) for key in range(key_space_size+1) for col in range(4) for color in [1,3]) 
    objective_purple = gp.quicksum(full_key[round, key, row, col, color] for round in range(total_round-differential_round) for row in range(2) for key in range(key_space_size+1) for col in range(4) for color in [3]) 
    #objective_blue2 = gp.quicksum(key_knowledge[row, col, key, 1] for row in range(4) for col in range(4) for key in range(key_space_size+1))
    #objective_red2 = gp.quicksum(key_knowledge[row, col, key, 0] for row in range(4) for col in range(4) for key in range(key_space_size+1))
    fix_quantity_structure = gp.quicksum(structure_state[round, step, row, col, 4] for round in range(structure_round) for step in range(3) for row in range(4) for col in range(4))
    mean = (objective_blue + objective_red)/2
    model.setObjective(objective_blue+objective_red+objective_purple)
    
    model.ModelSense = GRB.MINIMIZE
    ### CONSTRAINTS ###

    ### KEY Constraints

    for round in range (total_round - differential_round):
        for key in range(key_space_size + 1):
            for row in range(4):
                for col in range(4):
                    model.addConstr(gp.quicksum(full_key[round, key, row, col, color] for color in range(4)) == 1) #key must be unkown, red, blue, or purple
    
    for round in range(structure_round):
        for key in range(1, key_space_size + 1):
            model.addConstr(gp.quicksum([full_key[round, key, row, col, color]  for row in range(4) for col in range(4) for color in [1, 3]]) <= 15) #on ne peux pas connaître toute la clé du coté des rouges
            model.addConstr(gp.quicksum([full_key[round, key, row, col, color]  for row in range(4) for col in range(4) for color in [2, 3]]) <= 15) #on ne peux pas connaître toute la clé du coté des bleus  

    #Key schedule :  if we guess more than two time a key word of the full key, we guessed it for all the others
    for row in range(4):
        for col in range(4):
            for key in range(key_space_size+1):
                for colour in range(2):
                    key_knowledge[row,col,key,colour] = gp.quicksum(full_key[round, key, np.where(list_of_key_index[round] == key_index_0[row,col])[0][0], np.where(list_of_key_index[round] == key_index_0[row,col])[1][0], key_color] for round in range(total_round - differential_round) for key_color in [colour+1,3])
                    model.addConstr(binary_bound_for_key_knowledge[row, col,key, colour,0] + binary_bound_for_key_knowledge[row, col,key, colour, 1] == 1)

    for row in range(4):
        for col in range(4):
            for colour in range(2):                
                model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col, 0, colour, 0], True, key_knowledge[row, col,0, colour], gp.GRB.GREATER_EQUAL, (total_round - differential_round)) 
                model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col, 0, colour, 1], True, key_knowledge[row, col,0, colour], gp.GRB.LESS_EQUAL, key_space_size-1)
                model.addConstr((binary_bound_for_key_knowledge[row, col,0, colour,0] == 1) >> (binary_bound_for_key_knowledge[row, col,1, colour,0] == 1))
                if key_space_size > 1 :
                    model.addConstr((binary_bound_for_key_knowledge[row, col,0, colour,0] == 1) >> (binary_bound_for_key_knowledge[row, col,2, colour,0] == 1))
                if key_space_size > 2 :
                    model.addConstr((binary_bound_for_key_knowledge[row, col,0, colour,0] == 1) >> (binary_bound_for_key_knowledge[row, col,3, colour,0] == 1))
                for key in range(1,key_space_size+1):          
                    model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col, key, colour, 0], True, key_knowledge[row, col,key, colour], gp.GRB.GREATER_EQUAL, total_round - differential_round) 
                    model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col, key, colour, 1], True, key_knowledge[row, col,key, colour], gp.GRB.LESS_EQUAL,0)

    for round in range(structure_round):
        for row in range(4):
            for col in range(4):
                for color in range(4):
                    model.addConstr(full_key[round,0,row,col,color] == gp.and_(full_key[round,key,row,col,color] for key in range(1,key_space_size+1)))

    #Structure constraints
    #same unkown element through structure
    
    #starting constraints
    for row in range(4):
        for col in range(4):
            model.addConstr(structure_state[0, 0, row, col, 2] == 0) #first state must be kown only by red, fix or unknow
            model.addConstr(structure_state[0, 0, row, col, 3] == 0)
    
            model.addConstr(structure_state[structure_round - 1, 2, row, col, 1] == 0) #last state must be kown only by blue or purple or unknow
            #model.addConstr(structure_state[structure_round - 1, 2, row, col, 0] == 0)
            
    model.addConstr(gp.quicksum(structure_state[0,0,row, col, color] for col in range(4) for row in range(4) for color in range(1,5)) == fix_quantity_structure)
    model.addConstr(gp.quicksum(structure_state[structure_round-1,2,row, col, color] for col in range(4) for row in range(4) for color in range(1,5)) == fix_quantity_structure)
    
    model.addConstr(gp.quicksum(structure_state[0, 0, row, col, 0] for row in range(4) for col in range(4)) <= 15) # on ne peux pas ne pas connaître tout l'état de depart
    model.addConstr(gp.quicksum(structure_state[structure_round - 1, 2, row, col, 0] for row in range(4) for col in range(4)) <= 15) # on ne peux pas ne pas connaître tout l'état d'arrive
    
    #Maximum of 16 fix word 
    model.addConstr(gp.quicksum(structure_state[round, step, row, col, 4] for round in range(structure_round) for step in range(3) for row in range(4) for col in range(4)) <= 16)
    
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
                model.addConstr((structure_state[round, 0, row, col, 1] == gp.or_(structure_state[round, 1, row, col, 1], full_key[round, 0, row, col, 1]))) #red before AK only if red in the key or previous state

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
            
    
    ### MITM UP CONSTRAINTS
    for round in range(MITM_up_round):
        for step in range(3):
            for row in range(4):
                for col in range(4):
                    model.addConstr(gp.quicksum(MITM_up_state[round, step, row, col, color] for color in range(2)) == 1) #state can be only blue or unkown

    #key addition
    for round in range(MITM_up_round - 1):
        for row in range(2):
            for col in range(4):
                model.addConstr(MITM_up_state[round, 1, row, col, 0] == gp.or_(MITM_up_state[round, 0, row, col, 0], full_key[round + structure_round, 0, row, col, 0], full_key[round + structure_round, 0, row, col, 1]))
        for row in range(2,4):
            for col in range(4):
                model.addConstr(MITM_up_state[round, 1, row, col, 0] == MITM_up_state[round, 0, row, col, 0])
    
    #last state is not impacted
    for row in range(4):
        for col in range(4):
            model.addConstr(MITM_up_state[MITM_up_round-1, 1, row , col, 0] == MITM_up_state[MITM_up_round-1, 0, row , col, 0])
            model.addConstr(MITM_up_state[MITM_up_round-1, 1, row , col, 1] == MITM_up_state[MITM_up_round-1, 0, row , col, 1])

    #forward permutation
    for round in range(MITM_up_round):
        for col in range(4):
            for color in range(2):
                model.addConstr((MITM_up_state[round, 1, 0, col, color] == 1) >> (MITM_up_state[round, 2, 0, col, color] == 1))
                model.addConstr((MITM_up_state[round, 1, 1, col, color] == 1) >> (MITM_up_state[round, 2, 1, (col +1) % 4, color] == 1))
                model.addConstr((MITM_up_state[round, 1, 2, col, color] == 1) >> (MITM_up_state[round, 2, 2, (col +2) % 4, color] == 1))
                model.addConstr((MITM_up_state[round, 1, 3, col, color] == 1) >> (MITM_up_state[round, 2, 3, (col +3) % 4, color] == 1))
    
    #forward MC
    for round in range(MITM_up_round - 1):
            for col in range(4):
                model.addConstr((MITM_up_state[round+1, 0, 0, col, 1] == gp.and_(MITM_up_state[round, 2, row, col, 1] for row in [0, 2, 3])))
                model.addConstr((MITM_up_state[round+1, 0, 1, col, 1] == gp.and_(MITM_up_state[round, 2, row, col, 1] for row in [0])))
                model.addConstr((MITM_up_state[round+1, 0, 2, col, 1] == gp.and_(MITM_up_state[round, 2, row, col, 1] for row in [1, 2])))
                model.addConstr((MITM_up_state[round+1, 0, 3, col, 1] == gp.and_(MITM_up_state[round, 2, row, col, 1] for row in [0, 2])))

    ### DIFFERENTIAL UP CONSTRAINT
    for round in range(MITM_up_round):
        for step in range(2):
            for row in range(4):
                for col in range(4):
                    model.addConstr(gp.quicksum(differential_up_state[round, step, row, col, color] for color in range(2)) == 1) 
    
    #bacward MC propagation
    for round in range(MITM_up_round-1):
        for col in range(4):
            model.addConstr((differential_up_state[round, 1, 0, col, 1] == gp.or_(differential_up_state[round + 1, 0, row, col, 1] for row in [1])))
            model.addConstr((differential_up_state[round, 1, 1, col, 1] == gp.or_(differential_up_state[round + 1, 0, row, col, 1]for row in [1,2,3])))
            model.addConstr((differential_up_state[round, 1, 2, col, 1] == gp.or_(differential_up_state[round + 1, 0, row, col, 1] for row in [1,3])))
            model.addConstr((differential_up_state[round, 1, 3, col, 1] == gp.or_(differential_up_state[round + 1, 0, row, col, 1] for row in [0,3])))
    
    #backward permutation
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
                model.addConstr((differential_up_state[round, 0, row, col, 1] == 1) >> (MITM_up_state[round, 0, row, col, 1] == 1))
    
    #truncated Differential constraints
    
    model.addConstr(differential_up_state[MITM_up_round-1,1,0,0,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,0,1,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,0,2,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,0,3,1] == 0)

    model.addConstr(differential_up_state[MITM_up_round-1,1,1,0,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,1,1,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,1,2,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,1,3,1] == 1)

    model.addConstr(differential_up_state[MITM_up_round-1,1,2,0,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,2,1,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,2,2,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,2,3,1] == 1)

    model.addConstr(differential_up_state[MITM_up_round-1,1,3,0,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,3,1,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,3,2,1] == 0)
    model.addConstr(differential_up_state[MITM_up_round-1,1,3,3,1] == 1)
    
    model.addConstr(differential_down_state[0, 0, 0, 0, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 0, 1, 1] == 1)
    model.addConstr(differential_down_state[0, 0, 0, 2, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 0, 3, 1] == 0)

    model.addConstr(differential_down_state[0, 0, 1, 0, 1] == 1)
    model.addConstr(differential_down_state[0, 0, 1, 1, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 1, 2, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 1, 3, 1] == 0)

    model.addConstr(differential_down_state[0, 0, 2, 0, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 2, 1, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 2, 2, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 2, 3, 1] == 0)

    model.addConstr(differential_down_state[0, 0, 3, 0, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 3, 1, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 3, 2, 1] == 0)
    model.addConstr(differential_down_state[0, 0, 3, 3, 1] == 0)
    
    ### DIFFERENTIAL DOWN CONSTRAINTS
    for round in range(MITM_down_round):
        for step in range(2):
            for row in range(4):
                for col in range(4):
                    model.addConstr(gp.quicksum(differential_down_state[round, step, row, col, color] for color in range(2)) == 1) 
    
    #Forward MC
    for round in range(MITM_down_round-1):
        for col in range(4):
            model.addConstr(differential_down_state[round + 1, 0, 0, col, 1] == gp.or_(differential_down_state[round, 1, row, col, 1] for row in [0, 2, 3]))
            model.addConstr(differential_down_state[round + 1, 0, 1, col, 1] == gp.or_(differential_down_state[round, 1, 0, col, 1] ))
            model.addConstr(differential_down_state[round + 1, 0, 2, col, 1] == gp.or_(differential_down_state[round, 1, row, col, 1] for row in [1, 2]))
            model.addConstr(differential_down_state[round + 1, 0, 3, col, 1] == gp.or_(differential_down_state[round, 1, row, col, 1] for row in [0, 2]))
    
    #Forward pernutation
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
                model.addConstr((differential_down_state[round, 0, row, col, 1] == 1) >> (MITM_down_state[round, 0, row, col, 1] == 1))
    
    ### MITM DOWN CONSTRAINTS
    for round in range(MITM_down_round):
        for step in range(3):
            for row in range(4):
                for col in range(4):
                    model.addConstr(gp.quicksum(MITM_down_state[round, step, row, col, color] for color in range(2)) == 1) 

    #MC
    for round in range(MITM_down_round - 1):
        for col in range(4):
            model.addConstr((MITM_down_state[round, 2, 0, col, 1] == gp.and_(MITM_down_state[round + 1, 0, row, col, 1] for row in [1])))
            model.addConstr((MITM_down_state[round, 2, 1, col, 1] == gp.and_(MITM_down_state[round + 1, 0, row, col, 1] for row in [1, 2, 3])))
            model.addConstr((MITM_down_state[round, 2, 2, col, 1] == gp.and_(MITM_down_state[round + 1, 0, row, col, 1] for row in [1, 3])))
            model.addConstr((MITM_down_state[round, 2, 3, col, 1] == gp.and_(MITM_down_state[round + 1, 0, row, col, 1] for row in [0, 3])))

    #permutation
    for round in range(MITM_down_round):
        for col in range(4):
            for color in range(2):
                model.addConstr((MITM_down_state[round, 1, 0, col, color] == 1) >> (MITM_down_state[round, 2, 0, col, color] == 1))
                model.addConstr((MITM_down_state[round, 1, 1, col, color] == 1) >> (MITM_down_state[round, 2, 1, (col + 1) % 4, color] == 1))
                model.addConstr((MITM_down_state[round, 1, 2, col, color] == 1) >> (MITM_down_state[round, 2, 2, (col + 2) % 4, color] == 1))
                model.addConstr((MITM_down_state[round, 1, 3, col, color] == 1) >> (MITM_down_state[round, 2, 3, (col + 3) % 4, color] == 1))
    
    #key_add
    for round in range(1, MITM_down_round):
        for row in range(2):
            for col in range(4):
                model.addConstr(MITM_down_state[round, 0, row, col, 0] == gp.or_(MITM_down_state[round, 1, row, col, 0], full_key[round + structure_round + MITM_up_round, 0, row, col, 0], full_key[round + structure_round + MITM_up_round, 0, row, col, 2]))
        for row in range(2,4):
            for col in range(4):
                model.addConstr(MITM_down_state[round, 0, row, col, 0] == MITM_down_state[round, 1, row, col, 0])
    
    #key is not added during the round just after truncated differential
    for row in range(4):
        for col in range(4):
            model.addConstr(MITM_down_state[0, 0, row , col, 1] == MITM_down_state[0, 1, row , col, 1])
            model.addConstr(MITM_down_state[0, 0, row , col, 0] == MITM_down_state[0, 1, row , col, 0])

    
    model.optimize()

    #SI on a trouvé une solution on formate le résultat et on l'affiche avec la fonction d'affichage
    compteur_bleu = 0
    compteur_rouge = 0
    compteur_violet = 0
    compteur_differentielle = 0
    compteur_fix = 0

    if model.Status == GRB.OPTIMAL:
        compteur_fix = 0
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
                        compteur_fix+=1

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
                        compteur_fix+=1

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
                        compteur_fix+=1

                    Liste_X_diff[i][row, col] = -1 
                    Liste_Y_diff[i][row, col] = -1 

        for i in range(MITM_up_round):
            for row in range(4):
                for col in range(4):
                    if MITM_up_state[i, 0, row, col, 0].X == 1.0:
                        liste_X[structure_round + i][row, col] = 1

                    if MITM_up_state[i, 0, row, col,1].X == 1.0:
                        liste_X[structure_round + i][row, col] = 3

                    if MITM_up_state[i, 1, row, col, 0].X == 1.0:
                        liste_Y[structure_round + i][row, col] = 1
                    if MITM_up_state[i, 1, row, col, 1].X == 1.0:
                        liste_Y[structure_round + i][row, col] = 3

                    if MITM_up_state[i, 2, row, col, 0].X == 1.0:
                        liste_Z[structure_round + i][row, col] = 1
                    if MITM_up_state[i, 2, row, col, 1].X == 1.0:
                        liste_Z[structure_round + i][row, col] = 3

                    if differential_up_state[i, 0, row, col, 0].X == 1.0:
                        Liste_X_diff[structure_round + i][row, col] = 1
                    
                    if differential_up_state[i, 0, row, col, 1].X == 1.0:
                        Liste_X_diff[structure_round + i][row, col] = 3

                    if differential_up_state[i, 1, row, col, 0].X == 1.0:
                        Liste_Y_diff[structure_round + i][row, col] = 1
                    
                    if differential_up_state[i, 1, row, col, 1].X == 1.0:
                        Liste_Y_diff[structure_round + i][row, col] = 3

        for i in range(differential_round):
            for row in range(4):
                for col in range(4):
                    if differential_state[i, 0, row, col, 0].X == 1.0:
                        liste_X[structure_round + MITM_up_round + i][row, col] = 1       
                    if differential_state[i, 0, row, col,1].X == 1.0:
                        liste_X[structure_round + MITM_up_round + i][row, col] = 5
                    if differential_state[i, 0, row, col,2].X == 1.0:
                        liste_X[structure_round + MITM_up_round + i][row, col] = -1
                        compteur_differentielle+=1
                    if differential_state[i, 0, row, col,3].X == 1.0:
                        liste_X[structure_round + MITM_up_round + i][row, col] = -1
                        compteur_differentielle+=2
                    
                    if differential_state[i, 1, row, col, 0].X == 1.0:
                        liste_Y[structure_round + MITM_up_round + i][row, col] = 1       
                    if differential_state[i, 1, row, col, 1].X == 1.0:
                        liste_Y[structure_round + MITM_up_round + i][row, col] = 5
                    if differential_state[i, 1, row, col, 2].X == 1.0:
                        liste_Y[structure_round + MITM_up_round + i][row, col] = -1
                        compteur_differentielle+=1
                    if differential_state[i, 1, row, col, 3].X == 1.0:
                        liste_Y[structure_round + MITM_up_round + i][row, col] = -1
                        compteur_differentielle+=2
                    
                    Liste_X_diff[structure_round + MITM_up_round + i][row, col] = -1
                    Liste_Y_diff[structure_round + MITM_up_round + i][row, col] = -1 
        
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

                    if differential_down_state[i, 0, row, col, 0].X == 1.0:
                        Liste_X_diff[structure_round + MITM_up_round + differential_round + i][row, col] = 1
                    
                    if differential_down_state[i, 0, row, col, 1].X == 1.0:
                        Liste_X_diff[structure_round + MITM_up_round + differential_round + i][row, col] = 2

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
                    if full_key[tour + structure_round + MITM_up_round, 0, row, col, 0].X == 1.0:
                        key_M[tour + structure_round + MITM_up_round + differential_round, row, col] = 1
                    if full_key[tour + structure_round + MITM_up_round, 0, row, col, 1].X == 1.0:
                        key_M[tour + structure_round + MITM_up_round + differential_round, row, col] = 2
                    if full_key[tour + structure_round + MITM_up_round, 0, row, col, 2].X == 1.0:
                        key_M[tour + structure_round + MITM_up_round + differential_round, row, col] = 3
                    if full_key[tour + structure_round + MITM_up_round, 0, row, col, 3].X == 1.0:
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
                        if full_key[tour + structure_round + MITM_up_round, 1, row, col, 0].X == 1.0:
                            key_0[tour + structure_round + MITM_up_round + differential_round, row, col] = 1
                        if full_key[tour + structure_round + MITM_up_round, 1, row, col, 1].X == 1.0:
                            key_0[tour + structure_round + MITM_up_round + differential_round, row, col] = 2
                        if full_key[tour + structure_round + MITM_up_round, 1, row, col, 2].X == 1.0:
                            key_0[tour + structure_round + MITM_up_round + differential_round, row, col] = 3
                        if full_key[tour + structure_round + MITM_up_round, 1, row, col, 3].X == 1.0:
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
                        if full_key[tour + MITM_up_round + structure_round, 2, row, col, 0].X == 1.0:
                            key_1[tour + structure_round + MITM_up_round + differential_round, row, col] = 1
                        if full_key[tour + MITM_up_round + structure_round, 2, row, col, 1].X == 1.0:
                            key_1[tour + structure_round + MITM_up_round + differential_round, row, col] = 2
                        if full_key[tour + MITM_up_round + structure_round, 2, row, col, 2].X == 1.0:
                            key_1[tour + structure_round + MITM_up_round + differential_round, row, col] = 3
                        if full_key[tour + MITM_up_round + structure_round, 2, row, col, 3].X == 1.0:
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
                        if full_key[tour + structure_round + MITM_up_round, 3, row, col, 0].X == 1.0:
                            key_2[tour + structure_round + MITM_up_round + differential_round, row, col] = 1
                        if full_key[tour + structure_round + MITM_up_round, 3, row, col, 1].X == 1.0:
                            key_2[tour + structure_round + MITM_up_round + differential_round, row, col] = 2
                        if full_key[tour + structure_round + MITM_up_round, 3, row, col, 2].X == 1.0:
                            key_2[tour + structure_round + MITM_up_round + differential_round, row, col] = 3
                        if full_key[tour + structure_round + MITM_up_round, 3, row, col, 3].X == 1.0:
                            key_2[tour + structure_round + MITM_up_round + differential_round, row, col] = 5
        
        for row in range(4):
                    for col in range(4):
                        print("rouge", row, col, key_knowledge[row,col,0,0].getValue(), key_knowledge[row,col,1,0].getValue())
                        print("bleu", row, col, key_knowledge[row,col,0,1].getValue(), key_knowledge[row,col,1,1].getValue())
                        print("________")
                        if key_knowledge[row,col,0,0].getValue() >=3 :
                            compteur_rouge += 3
                        else :
                            compteur_rouge += key_knowledge[row,col,0,0].getValue()
                        if key_knowledge[row,col,0,1].getValue() >=3 :
                            compteur_bleu += 3
                        else :
                            compteur_bleu += key_knowledge[row,col,0,1].getValue()
                        if key_knowledge[row,col,0,1].getValue()>=3 and key_knowledge[row,col,0,0].getValue()>=3:
                            compteur_violet += 3
                        if key_knowledge[row,col,0,1].getValue()==2 and key_knowledge[row,col,0,0].getValue()==2:
                            compteur_violet += 2
                        if key_knowledge[row,col,0,1].getValue()==1 and key_knowledge[row,col,0,0].getValue()==1:
                            compteur_violet += 1

        affichage_grille(key_M, key_0, key_1, key_2, liste_X, liste_Y, liste_Z,Liste_X_diff, Liste_Y_diff)
        print("attaque differential MITM")
        print("nombre de tours : ")
        print(total_round)
        print("nombre de tours de la structure: ")
        print(structure_round)
        print("nombre de tours de la MITM up: ")
        print(MITM_up_round)
        print("nombre de tours de la differentielle: ")
        print(differential_round)
        print("nombre de tours de la MITM down: ")
        print(MITM_down_round)

        
        print('Nombre de bleu guess : ')
        print(compteur_bleu, z*compteur_bleu)
        print('Nombre de rouge guess : ')
        print(compteur_rouge, z*compteur_rouge)
        print('coup de la differentielle : ')
        print(compteur_differentielle, z*compteur_differentielle)
        print('nombre de F : ')
        print(compteur_fix, z*compteur_fix)
        print("differentielle tronque, taille entre et sortie")
        print(start_diff, end_diff)
        print("complexite")
        print(probability_diff + z*compteur_bleu)
        print(probability_diff + z*compteur_rouge + end_diff - start_diff)
        print(probability_diff + z*(16-compteur_fix)+ z*compteur_bleu + z*compteur_rouge -z*compteur_violet - z*compteur_fix + end_diff)
    else :
        print("UNFAISABLE")









