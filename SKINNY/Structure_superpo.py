#### Recherche de structure avec superposition des etats
# Intuition, on recherche la propagation des rouges et bleus independament, seul les fix entre chaque propagation doit etre identique
import numpy as np
import gurobipy as gp
from gurobipy import GRB
from tqdm import tqdm
from itertools import product
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

def structure(structure_size, MITM_up_size, distinguisher_size, MITM_down_size, key_size):
    options = {
            "WLSACCESSID" : "ffd7aab1-ddce-4db1-b37a-cf70288fb87c",
            "WLSSECRET" : "1746d0d5-a916-47fb-b0aa-9f67cb800c57",
            "LICENSEID" : 2602460 }
    
    with gp.Env(params=options) as env, gp.Model(env=env) as model:
        if key_size not in [1, 2, 3]:
            print("Specified key size is not possible")
            return([False])
        if MITM_up_size <= 2:
            print("Specified MITM up size is not possible")
            return([False])
        if MITM_down_size <= 2:
            print("Specified key size is not possible")
            return([False])
        if distinguisher_size <= 0:
            print("Specified key size is not possible")
            return([False])
        
        distinguisher_size+=1
        MITM_down_size-=1

        total_round = structure_size+MITM_up_size+distinguisher_size+MITM_down_size
        #Key material
        key_index_0 = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]])

        key_index_copy = key_index_0.copy()
        list_of_key_index = np.zeros((total_round,4,4))
        for index in range(total_round):
            list_of_key_index[index, :, :] = key_index_copy
            key_index_copy = tweakey(key_index_copy)

        #Variable creation
        key = np.zeros((total_round, 4, 4, 4), dtype=object) #[round, row, col, color(unknow = 0, red = 1, blue = 2, purple = 3)]

        key_knowledge = np.zeros((4, 4, 2), dtype = object) #[row, col, color (0 = red, 1 = blue)]

        binary_bound_key_knowledge = np.zeros((4, 4, 2, 2), dtype = object) #[row, col, color (0 = red, 1 = blue), bin (0 = key word not guess for all the key, 1 = key word guess for all the key)]

        blue_structure_state = np.zeros((structure_size, 4, 4, 4, 3), dtype=object) #[round, step, row, col, color (0 = unknow, 1 = know, 2 = fix)]

        red_structure_state = np.zeros((structure_size, 4, 4, 4, 3), dtype=object) #[round, step, row, col, color (0 = unknow, 1 = know, 2 = fix)]

        MITM_up_state = np.zeros((MITM_up_size, 4, 4, 4, 3), dtype = object) #[round, step, row, col, color (0 = unknow, 1 = know, 2 = state_tested)]

        MITM_up_difference = np.zeros((MITM_up_size, 4, 4, 4, 4), dtype = object) #[round, step, row, col, color (0 = unknow, 1 = know, 2 = probabilist annulation, 3= free annulation)]

        distinguisher = np.zeros((distinguisher_size, 4, 4, 4, 4), dtype = object) #[round, step, row, col, color (0 = null, 1 = active, 2 = canceled, 3= free annulation)]

        MITM_down_state = np.zeros((MITM_up_size, 4, 4, 4, 3), dtype = object) #[round, step, row, col, color (0 = unknow, 1 = know, 2 = state_tested)]

        MITM_down_difference = np.zeros((MITM_up_size, 4, 4, 4, 4), dtype = object) #[round, step, row, col, color (0 = unknow, 1 = know, 2 = probabilist annulation)]

        #Gurobi variable initialisation
        for step, row, col, color in product(range(4), range(4), range(4), range(3)):
            for round in range(structure_size):
                blue_structure_state[round, step, col, row, color] = model.addVar(vtype = GRB.BINARY, name = f'blue_structure_state {round} {step} {col} {row} {color}')
                red_structure_state[round, step, col, row, color] = model.addVar(vtype = GRB.BINARY, name = f'red_structure_state {round} {step} {col} {row} {color}')
            
            for round in range(MITM_up_size):
                MITM_up_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f'MITM_up_state {round} {step} {col} {row} {color}' )
                
            for round in range(MITM_down_size):
                MITM_down_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f'MITM_up_state {round} {step} {col} {row} {color}' )
        
        for step, row, col, color in product(range(4), range(4), range(4), range(4)):
                for round in range(distinguisher_size):
                    distinguisher[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f'distinguisher {round} {step} {col} {row} {color}')

                for round in range(MITM_up_size):
                    MITM_up_difference[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f'MITM_up_difference {round} {step} {col} {row} {color}')

                for round in range(MITM_down_size):
                    MITM_down_difference[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f'MITM_up_difference {round} {step} {col} {row} {color}')
            
        for round, row, col, color in product(range(total_round), range(4), range(4), range(4)):
            key[round, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f'key {round} {col} {row} {color}')
        
        for row, col, color in product(range(4), range(4), range(2)):
            key_knowledge[row, col, color] = model.addVar(lb = 0.0, ub = total_round - distinguisher_size, vtype = GRB.INTEGER, name = f'key_knowledge {row}, {col}, {color}')
            for bin in range(2):
                binary_bound_key_knowledge[row, col, color, bin] = model.addVar(vtype = GRB.INTEGER, name = f'binary bound for key knowledge {row} {col} {color} {bin}')

        complexity = model.addVar(lb = 0.0, ub = 60.0,vtype= GRB.INTEGER, name = "complexite")

        #Objective : minimize the needed key
         #count of the state test
        state_test_up = gp.quicksum(MITM_up_state[round, 0, row, col, 2] for round in range(MITM_up_size) for row in range(4) for col in range(4))
        state_test_down = gp.quicksum(MITM_down_state[round, 0, row, col, 2] for round in range(MITM_down_size) for row in range(4) for col in range(4))
        
        #Probabilistic key recovery 
        MITM_up_guess = gp.quicksum(MITM_up_difference[round, 1, row, col, 2] for round in range(MITM_up_size) for row in range(4) for col in range(4))
        MITM_down_guess = gp.quicksum(MITM_down_difference[round, 0, row, col, 2] for round in range(MITM_down_size) for row in range(4) for col in range(4))
       
        #count of the fix in structure
        fix_number = gp.quicksum(red_structure_state[round, step, row, col, 2] for round, step, row, col in product(range(structure_size), range(4), range(4), range(4)))

        #count of the cost of the differential
        cost_differential = gp.quicksum(distinguisher[round, 0, row, col, 2] for round in range(distinguisher_size) for row in range(4) for col in range(4))
        objective_differential_end = gp.quicksum(distinguisher[distinguisher_size-1, 1, row, col, 0] for row in range(4) for col in range(4))

        #size of the start and the end of the differential
        end_differential = gp.quicksum(distinguisher[distinguisher_size-1, 1, row, col, 1] for row in range(4) for col in range(4))
        start_differential = gp.quicksum(distinguisher[0, 0, row, col, 1] for row in range(4) for col in range(4))
        
        #mombre de bleu et rouge guess
        count_blue = gp.quicksum(binary_bound_key_knowledge[row, col, 1, 1]*key_knowledge[row, col, 1] for row in range(4) for col in range(4)) + (key_size)*gp.quicksum(binary_bound_key_knowledge[row, col, 1, 0] for row in range(4) for col in range(4))
        count_red = gp.quicksum(binary_bound_key_knowledge[row, col, 0, 1]*key_knowledge[row, col, 0] for row in range(4) for col in range(4)) + (key_size)*gp.quicksum(binary_bound_key_knowledge[row, col, 0, 0] for row in range(4) for col in range(4))

        #complexity constraints
        
        blue_complexity = cost_differential + count_blue + MITM_down_guess + state_test_up
        red_complexity = cost_differential + count_red + MITM_up_guess + state_test_down + end_differential - start_differential

        model.addConstr(blue_complexity <= complexity)
        model.addConstr(red_complexity <= complexity)

        model.setObjectiveN(complexity, 0, 100)
        #model.setObjectiveN(-1*fix_number, 1 , 25)

        #We need less text generated by the structure than the one needed at the start of the distinguisher
        model.addConstr(16 - fix_number <= cost_differential - start_differential + MITM_up_guess + MITM_down_guess)

        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### KEY constraints ###:
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #Key can be only in one state : unknow, blue ,red or purple :
        for round, col, row in product(range(total_round), range(4), range(4)): 
            model.addConstr(gp.quicksum(key[round, row, col, color] for color in range(4)) == 1)

        #Key schedule
        for row, col, color in product(range(4), range(4), range(2)): 
            model.addConstr(key_knowledge[row,col,color] == gp.quicksum(key[round, np.where(list_of_key_index[round] == key_index_0[row,col])[0][0], np.where(list_of_key_index[round] == key_index_0[row,col])[1][0], key_color] for round in range(total_round) for key_color in [color+1,3]))
            model.addConstr(binary_bound_key_knowledge[row, col, color, 1] + binary_bound_key_knowledge[row, col, color, 0] == 1)
            model.addGenConstrIndicator(binary_bound_key_knowledge[row, col, color, 1], True, key_knowledge[row, col, color], gp.GRB.GREATER_EQUAL, (total_round-distinguisher_size)) 
            model.addGenConstrIndicator(binary_bound_key_knowledge[row, col, color, 0], True, key_knowledge[row, col, color], gp.GRB.LESS_EQUAL, key_size-1)
        
        #Never guess completly the key
        for color in range(2):
            model.addConstr(gp.quicksum(key_knowledge[row, col, color] for row in range(4) for col in range(4)) <= key_size*(total_round-distinguisher_size))

        #Key is not used in distinguisher(objetive is to decrease number of variables possibilities)
        for round, row, col in product(range(structure_size+MITM_up_size, structure_size + MITM_up_size + distinguisher_size), range(4), range(4)):
            model.addConstr(key[round, row, col, 0] == 1)

        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### STRUCTURE constraints ###
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        # To decrease the number of variables, fix can be done only around MC
        for round, row, col in product(range(structure_size), range(4), range(4)):
            model.addConstr(red_structure_state[round, 1, row, col, 2] == 0)
            model.addConstr(blue_structure_state[round, 1, row, col, 2] == 0)
            model.addConstr(red_structure_state[round, 2, row, col, 2] == 0)
            model.addConstr(blue_structure_state[round, 2, row, col, 2] == 0)

        #maximum of 16 fix elements
        model.addConstr(fix_number <= 16)
        #at least one fix element :
        model.addConstr(fix_number >= 1)

        #Red and blue propagation must have the same fix elements
        for round, step, col, row in product(range(structure_size), range(4), range(4), range(4)):
            model.addConstr(blue_structure_state[round, step, row, col, 2] == red_structure_state[round, step, row, col, 2])

        #Red need to know F element at the end of the structure
        model.addConstr(gp.quicksum(red_structure_state[structure_size-1,3,row,col,color] for row in range(4) for col in range(4) for color in[1,2]) == fix_number)

        #Red are not knowing elements at the start of the structure
        for row, col in product(range(4), range(4)):
            model.addConstr(red_structure_state[0,0,row,col,1] == 0)

        #Blue need to know F element at the begining of the structure
        model.addConstr(gp.quicksum(blue_structure_state[0,0,row,col,color] for row in range(4) for col in range(4) for color in [1, 2]) == fix_number)
        
        #Blue are not knowing elements at the end of the structure
        for row, col in product(range(4), range(4)):
            model.addConstr(blue_structure_state[structure_size-1,3,row,col,1] == 0)

        ### REAL CASE VERIFICATION : limit the number of guess in a round
        for round in range(structure_size):
            model.addConstr(gp.quicksum(blue_structure_state[round, step, row, col, 2] for step, row, col in product(range(4), range(4), range(4))) <= 15)

        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### Propagation of the red elements in the STRUCTURE
        for round, step, row, col in product(range(structure_size), range(4), range(4), range(4)):
            model.addConstr(gp.quicksum(red_structure_state[round, step, row, col, color] for color in range(3)) == 1)
                                            
        #SB
        for round, row, col in product(range(structure_size), range(4), range(4)):
            model.addConstr((red_structure_state[round, 0, row, col, 0] == 1) >> (red_structure_state[round, 1, row, col, 1] == 0))
            model.addConstr((red_structure_state[round, 0, row, col, 1] == 1) >> (red_structure_state[round, 1, row, col, 1] == 1))
            model.addConstr((red_structure_state[round, 0, row, col, 2] == 1) >> (red_structure_state[round, 1, row, col, 1] == 1))
    
        #AK
        for round, row, col in product(range(structure_size), range(2), range(4)):
            model.addConstr((red_structure_state[round, 2, row, col, 1]==1) >> (red_structure_state[round, 1, row, col, 0] + key[round, row, col, 0] + key[round, row, col, 2] == 0))
            model.addConstr((red_structure_state[round, 2, row+2, col, 1] == 1) >> (red_structure_state[round, 1, row+2, col, 0] == 0))

        #Permutation
        for round, row, col in product(range(structure_size), range(4), range(4)):
            model.addConstr((red_structure_state[round, 3, row, col, 1] == 1) >> (red_structure_state[round, 2, row, (col-row)%4, 1] == 1))
    
        #Mixcolumn
        for round, col in product(range(structure_size-1), range(4)):
            #First line 'a+c+d' specific case when you fix 'a+c'
            model.addConstr((red_structure_state[round+1, 0, 0, col, 1] == 1) >> (red_structure_state[round, 3, 0, col, 2] + red_structure_state[round, 3, 0, col, 1] + red_structure_state[round, 3, 2, col, 2] + red_structure_state[round, 3, 2, col, 1] + 3*red_structure_state[round, 3, 3, col, 1] + 3*red_structure_state[round, 3, 3, col, 2] + 2*red_structure_state[round+1, 0, 3, col, 2] >= 5))

            #Second line 'a'
            model.addConstr((red_structure_state[round+1, 0, 1, col, 1] == 1) >> (red_structure_state[round, 3, 0, col, 0] == 0))   

            #Third line 'b+c'
            model.addConstr((red_structure_state[round+1, 0, 2, col, 1] == 1) >> (gp.quicksum(red_structure_state[round, 3, row, col, color] for row in [1, 2] for color in [1,2]) >= 2))

            #Fourth line 'a+c'
            model.addConstr((red_structure_state[round+1, 0, 3, col, 1] == 1) >> (gp.quicksum(red_structure_state[round, 3, row, col, color] for row in [0, 2] for color in [1,2]) >= 2))

        ### Propagation of the blue elements in the STRUCTURE
        for round, step, row, col in product(range(structure_size), range(4), range(4), range(4)):
            model.addConstr(gp.quicksum(blue_structure_state[round, step, row, col, color] for color in range(3)) == 1)
                                            
        #SB
        for round, row, col in product(range(structure_size), range(4), range(4)):
            model.addConstr((blue_structure_state[round, 1, row, col, 0] == 1) >> (blue_structure_state[round, 0, row, col, 1] == 0))
            model.addConstr((blue_structure_state[round, 1, row, col, 1] == 1) >> (blue_structure_state[round, 0, row, col, 1] == 1))
            model.addConstr((blue_structure_state[round, 1, row, col, 2] == 1) >> (blue_structure_state[round, 0, row, col, 1] == 1))
    
        #AK
        for round, row, col in product(range(structure_size), range(2), range(4)):
            model.addConstr((blue_structure_state[round,1,row,col,1]==1) >> (blue_structure_state[round, 2, row, col, 0]+key[round, row, col, 0] + key[round, row, col, 1] == 0))
            model.addConstr((blue_structure_state[round, 1, row+2, col, 1]==1) >> (blue_structure_state[round, 2, row+2, col, 0]==0))
        
        #Permutation
        for round, row, col in product(range(structure_size), range(4), range(4)):
            model.addConstr((blue_structure_state[round, 2, row, col, 1] == 1) >> (blue_structure_state[round, 3, row, (col+row)%4, 1] + blue_structure_state[round, 3, row, (col+row)%4, 2] >= 1))

        #Mixcolumn
        for round, col in product(range(1,structure_size), range(4)):
            #First line 'b' 
            model.addConstr((blue_structure_state[round-1, 3, 0, col, 1] == 1) >> (blue_structure_state[round, 0, 1, col, 0]==0))

            #Second line 'b+c+d'
            model.addConstr((blue_structure_state[round-1, 3, 1, col, 1] == 1) >> (blue_structure_state[round, 0, 1, col, 1] + blue_structure_state[round, 0, 1, col, 2] + 3*blue_structure_state[round, 0, 2, col, 1] + 3*blue_structure_state[round, 0, 2, col, 2] + blue_structure_state[round, 0, 3, col, 1] + blue_structure_state[round, 0, 3, col, 2] + 2*blue_structure_state[round-1, 0, 2, col, 2] >= 5))

            #Third line 'b+d'
            model.addConstr((blue_structure_state[round-1, 3, 2, col, 1] == 1) >> (gp.quicksum(blue_structure_state[round, 0, row, col, color] for row in [1, 3] for color in [1,2]) >= 2))

            #Fourth line 'a+d'
            model.addConstr((blue_structure_state[round-1, 3, 3, col, 1] == 1) >> (gp.quicksum(blue_structure_state[round, 0, row, col, color] for row in [0, 3] for color in [1,2]) >= 2))
        
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### MITM up ###
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### Forward propagation of the state 
        #Color Constraints
        for round, step, row, col in product(range(MITM_up_size), range(4), range(4), range(4)):
            model.addConstr(gp.quicksum(MITM_up_state[round, step, row, col, color] for color in range(3)) == 1) #state can be only unknow, blue or state tested

        #state test is performed just after MC
        for round, step, row, col in product(range(MITM_up_size), range(1,4), range(4), range(4)):
            model.addConstr(MITM_up_state[round, step, row, col, 2] == 0)
        
        #state test is performed only where the difference is known
        for round, row, col in product(range(MITM_up_size), range(4), range(4)):
            model.addConstr((MITM_up_difference[round, 0, row, col, 0] == 1) >> (MITM_up_state[round, 0, row, col, 2] == 0))
        
        #state tests are necessarly useless in the first two round of MITM
        for row, col in product(range(4), range(4)):
            model.addConstr(MITM_up_state[0, 0, row, col, 2] == 0)
            model.addConstr(MITM_up_state[1, 0, row, col, 2] == 0)
        
        #state test are made only if at least one difference in the link differences before MC are zero (if not, state test is useless)
        for round, col in product(range(1, MITM_up_size), range(4)):
            model.addConstr((MITM_up_state[round, 0, 0, col, 2] == 1) >> (gp.quicksum(MITM_up_difference[round-1, 3, row_diff, col, 0] for row_diff in [0,2,3]) >= 1))
            model.addConstr((MITM_up_state[round, 0, 1, col, 2] == 1) >> (gp.quicksum(MITM_up_difference[round-1, 3, row_diff, col, 0] for row_diff in [1]) >= 1))
            model.addConstr((MITM_up_state[round, 0, 2, col, 2] == 1) >> (gp.quicksum(MITM_up_difference[round-1, 3, row_diff, col, 0] for row_diff in [1,2]) >= 1))
            model.addConstr((MITM_up_state[round, 0, 3, col, 2] == 1) >> (gp.quicksum(MITM_up_difference[round-1, 3, row_diff, col, 0] for row_diff in [0,2]) >= 1))
        
        #to ensure state test to be usefull, they need to make us win at least two key
        for round, row, col, in product(range(2, MITM_up_size), range(4), range(4)):
            model.addConstr((MITM_up_state[round, 0, row, col, 2] == 1) >> (gp.quicksum(MITM_up_state[round-2, 2, row_2, col_2, 0] for row_2 in range(2) for col_2 in range(4)) >= 2))
        
        #SB
        for round, row, col in product(range(MITM_up_size), range(4), range(4)):
            model.addConstr((MITM_up_state[round, 0, row, col, 0] == 1)>>(MITM_up_state[round, 1, row, col, 0] == 1))
            model.addConstr((MITM_up_state[round, 0, row, col, 1] == 1)>>(MITM_up_state[round, 1, row, col, 1] == 1))
            model.addConstr((MITM_up_state[round, 0, row, col, 2] == 1)>>(MITM_up_state[round, 1, row, col, 1] == 1))

        #AK
        for round, row, col in product(range(MITM_up_size), range(2), range(4)):
            #state is unknow if the key is red or unknow or if the state before key addition is unknow
            model.addConstr(MITM_up_state[round, 0, row, col, 0] == gp.or_(MITM_up_state[round, 1, row, col, 0], key[round + structure_size, row, col, 0], key[round + structure_size, row, col, 1])) 
            #AK is not made on the two last rows
            model.addConstr(MITM_up_state[round, 0, row+2, col, 0] == MITM_up_state[round, 1, row+2, col, 0])

        #permutation
        for round, row, col in product(range(MITM_up_size), range(4), range(4)):
            model.addConstr((MITM_up_state[round, 2, row, col, 1] == 1) >> (MITM_up_state[round, 3, row, (col+row) % 4, 1] == 1))
            model.addConstr((MITM_up_state[round, 2, row, col, 0] == 1) >> (MITM_up_state[round, 3, row, (col+row) % 4, 0] == 1))
        
        #MC
        for round, col in product(range(MITM_up_size-1), range(4)):
            model.addConstr((MITM_up_state[round+1, 0, 0, col, 1] == gp.and_(MITM_up_state[round, 3, row, col, 1] for row in [0, 2, 3])))
            model.addConstr((MITM_up_state[round+1, 0, 1, col, 1] == gp.and_(MITM_up_state[round, 3, row, col, 1] for row in [0])))
            model.addConstr((MITM_up_state[round+1, 0, 2, col, 1] == gp.and_(MITM_up_state[round, 3, row, col, 1] for row in [1, 2])))
            model.addConstr((MITM_up_state[round+1, 0, 3, col, 1] == gp.and_(MITM_up_state[round, 3, row, col, 1] for row in [0, 2])))

        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### Differential backward propagation of the differences

        #Color Constraints
        for round, step, row, col in product(range(MITM_up_size), range(4), range(4), range(4)):
            model.addConstr(gp.quicksum(MITM_up_difference[round, step, row, col, color] for color in range(4)) == 1) #state can only be unknown, blue, guess or cancel by guessing
        
        #probabilist key recovery only made through MC
        for round, step, row, col in product(range(MITM_up_size), range(3), range(4), range(4)):
            model.addConstr(MITM_up_difference[round, step, row, col, 2] == 0)
            model.addConstr(MITM_up_difference[round, step, row, col, 3] == 0)
            model.addConstr(MITM_up_difference[MITM_up_size-1, 3, row, col, 2] == 0)
            model.addConstr(MITM_up_difference[MITM_up_size-1, 3, row, col, 3] == 0)
       
        #MC-1
        for round, col in product(range(MITM_up_size-1), range(4)):
            model.addConstr(MITM_up_difference[round, 3, 0, col, 0] == gp.and_(MITM_up_difference[round + 1, 0, row, col, 0] for row in [1]))
            model.addConstr(MITM_up_difference[round, 3, 1, col, 0] == gp.and_(MITM_up_difference[round + 1, 0, row, col, 0]for row in [1,2,3]))
            model.addConstr(MITM_up_difference[round, 3, 2, col, 0] == gp.and_(MITM_up_difference[round + 1, 0, row, col, 0] for row in [1,3]))
            model.addConstr(MITM_up_difference[round, 3, 3, col, 0] == gp.and_(MITM_up_difference[round + 1, 0, row, col, 0] for row in [0,3]))
                
            model.addConstr(MITM_up_difference[round, 3, 0, col, 2] == 0)
            model.addConstr((MITM_up_difference[round, 3, 1, col, 2] == 1) >> (MITM_up_difference[round + 1, 0, 1, col, 1]+ MITM_up_difference[round + 1, 0, 3, col, 1]  + MITM_up_difference[round + 1, 0, 2, col, 1] >= 2))
            model.addConstr((MITM_up_difference[round, 3, 2, col, 2] == 1) >> (MITM_up_difference[round + 1, 0, 1, col, 1]+ MITM_up_difference[round + 1, 0, 3, col, 1] == 2))
            model.addConstr((MITM_up_difference[round, 3, 3, col, 2] == 1) >> (MITM_up_difference[round + 1, 0, 0, col, 1]+ MITM_up_difference[round + 1, 0, 3, col, 1] == 2))

            model.addConstr(MITM_up_difference[round, 3, 0, col, 3] == 0)
            model.addConstr(MITM_up_difference[round, 3, 1, col, 3] == gp.and_(MITM_up_difference[round, 3, 2, col, 2], MITM_up_difference[round + 1, 0, 2, col, 0]))
            model.addConstr(MITM_up_difference[round, 3, 2, col, 3] == gp.and_(MITM_up_difference[round, 3, 1, col, 2], MITM_up_difference[round + 1, 0, 2, col, 0]))
            model.addConstr(MITM_up_difference[round, 3, 3, col, 3] == 0)

        #permutation-1
        for round, col in product(range(MITM_up_size), range(4)):
                model.addConstr(MITM_up_difference[round, 3, row, col, 1] == MITM_up_difference[round, 1, 2, (col+row)%4, 1])

        #AK-1 (no impacted by the key)
        for round, row, col, color in product(range(MITM_up_size), range(4), range(4), range(2)):
            model.addConstr(MITM_up_difference[round, 2, row, col, color] == MITM_up_difference[round, 1, row, col, color])

        #SB-1 (propagation with proba 1 because the state is know)
        for round, row, col, color in product(range(MITM_up_size), range(4), range(4), range(2)):
            model.addConstr(MITM_up_difference[round, 1, row, col, color] == MITM_up_difference[round, 0, row, col, color])

        #differential need to be known after SB by value (MITM)
        for round, row, col in product(range(MITM_up_size), range(4), range(4)):
            model.addConstr((MITM_up_difference[round, 0, row, col, 1] == 1) >> (MITM_up_state[round, 0, row, col, 0] == 0))
        
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### TRUNCATED DISTINGUISHER ####
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #Color constraints
        for round, step, row, col in product(range(distinguisher_size), range(4), range(4), range(4)):
            model.addConstr(gp.quicksum(distinguisher[round, step, row, col, color] for color in range(4)) == 1 )

        #Annulation can only be made after MC in the distinguisher
        for row, col in product(range(4), range(4)):
            model.addConstr(distinguisher[0, 0, row, col, 2] == 0)
            model.addConstr(distinguisher[0, 0, row, col, 3] == 0)
        for round, step, row, col in product(range(distinguisher_size), range(3), range(4), range(4)):
            model.addConstr(distinguisher[round, step+1, row, col, 2] == 0)
            model.addConstr(distinguisher[round, step+1, row, col, 3] == 0)
        
        #SB
        for round, row, col in product(range(distinguisher_size), range(4), range(4)):
            model.addConstr((distinguisher[round, 0, row, col, 0] == 1) >> (distinguisher[round, 1, row, col, 0] == 1))
            model.addConstr((distinguisher[round, 0, row, col, 1] == 1) >> (distinguisher[round, 1, row, col, 1] == 1))
            model.addConstr((distinguisher[round, 0, row, col, 2] == 1) >> (distinguisher[round, 1, row, col, 1] == 1))
            model.addConstr((distinguisher[round, 0, row, col, 3] == 1) >> (distinguisher[round, 1, row, col, 1] == 1))
        
        #AK
        for round, row, col, color in product(range(distinguisher_size), range(4), range(4), range(2)):
            model.addConstr(distinguisher[round, 1, row, col, color] == distinguisher[round, 2, row, col, color])
        
        #SR
        for round, row, col, color in product(range(distinguisher_size), range(4), range(4), range(2)):
            model.addConstr(distinguisher[round, 2, row, col, color] == distinguisher[round, 3, row, (col+row)%4, color])

        #MC
        for round, col in product(range(distinguisher_size-1), range(4)):
            #First line 'a+c+d' specific case when you fix 'a+c'
            model.addConstr((distinguisher[round+1, 0, 0, col, 0] == gp.and_(distinguisher[round, 3, row, col, 0] for row in [0, 2, 3])))
            model.addConstr((distinguisher[round+1, 0, 0, col, 2] == 1) >> (distinguisher[round, 3, 0, col, 1] + distinguisher[round, 3,  2, col, 1] + distinguisher[round, 3, 3, col, 1] >= 2))
            model.addConstr(distinguisher[round+1, 0, 0, col, 3] == gp.and_((distinguisher[round+1, 0, row, col, 2] for row in [3]),(distinguisher[round, 3, row, col, 0] for row in [3])))

            #Second line
            model.addConstr((distinguisher[round+1, 0, 1, col, 0] == gp.and_(distinguisher[round, 3, row, col, 0] for row in [0])))
            model.addConstr((distinguisher[round+1, 0, 1, col, 2] == 0))
            model.addConstr((distinguisher[round+1, 0, 1, col, 3] == 0))

            #Third Line
            model.addConstr((distinguisher[round+1, 0, 2, col, 0] == gp.and_(distinguisher[round, 3, row, col, 0] for row in [1, 2])))
            model.addConstr((distinguisher[round+1, 0, 2, col, 2] == 1) >> (distinguisher[round, 3, 1, col, 1] + distinguisher[round, 3, 2, col, 1] == 2))
            model.addConstr((distinguisher[round+1, 0, 2, col, 3] == 0))

            #Fourth Line 
            model.addConstr((distinguisher[round+1, 0, 3, col, 0] == gp.and_(distinguisher[round, 3, row, col, 0] for row in [0, 2])))
            model.addConstr((distinguisher[round+1, 0, 3, col, 2] == 1) >> (distinguisher[round, 3, 0, col, 1] + distinguisher[round, 3, 2, col, 1] == 2))
            model.addConstr((distinguisher[round+1, 0, 3, col, 3] == 0))

        #States can never be fully known or unknown to be a valid disintguisher
        for round, step in product(range(distinguisher_size), range(4)):
            model.addConstr(gp.quicksum(distinguisher[round, step, row, col, 0] for row, col in product(range(4), range(4))) <= 15 )
            model.addConstr(gp.quicksum(distinguisher[round, step, row, col, 0] for row, col in product(range(4), range(4))) >= 1 )
            model.addConstr(gp.quicksum(distinguisher[round, step, row, col, 1] for row, col in product(range(4), range(4))) <= 15 )

        #Validity condition of truncated
        model.addConstr(objective_differential_end >= cost_differential+1)

        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### MITM Down Constraints ####
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### Differential forward propagation
        
        #Color Constraints
        for round, step, row, col in product(range(MITM_down_size), range(4), range(4), range(4)):
            model.addConstr(gp.quicksum(MITM_down_difference[round, step, row, col, color] for color in range(4)) == 1) 
        
        #probabilist key recovery only through MC
        for round, step, row, col in product(range(MITM_down_size), range(1, 4), range(4), range(4)):
            model.addConstr(MITM_down_difference[round, step, row, col, 2] == 0)
            model.addConstr(MITM_down_difference[round, step, row, col, 3] == 0)
            model.addConstr(MITM_down_difference[0, 0, row, col, 2] == 0)
            model.addConstr(MITM_down_difference[0, 0, row, col, 3] == 0)

        #MC
        for round, col in product(range(MITM_down_size-1), range(4)):
            model.addConstr(MITM_down_difference[round + 1, 0, 0, col, 0] == gp.and_(MITM_down_difference[round, 3, row, col, 0] for row in [0, 2, 3]))
            model.addConstr(MITM_down_difference[round + 1, 0, 1, col, 0] == gp.and_(MITM_down_difference[round, 3, 0, col, 0] ))
            model.addConstr(MITM_down_difference[round + 1, 0, 2, col, 0] == gp.and_(MITM_down_difference[round, 3, row, col, 0] for row in [1, 2]))
            model.addConstr(MITM_down_difference[round + 1, 0, 3, col, 0] == gp.and_(MITM_down_difference[round, 3, row, col, 0] for row in [0, 2]))
                
            model.addConstr(MITM_down_difference[round + 1, 0, 0, col, 3] == gp.and_(MITM_down_difference[round + 1, 0, 3, col, 2], MITM_down_difference[round, 3, 3, col, 0]))
            model.addConstr(MITM_down_difference[round + 1, 0, 1, col, 3] == 0)
            model.addConstr(MITM_down_difference[round + 1, 0, 2, col, 3] == 0)
            model.addConstr(MITM_down_difference[round + 1, 0, 3, col, 3] == gp.and_(MITM_down_difference[round + 1, 0, 0, col, 2], MITM_down_difference[round, 3, 3, col, 0]))
                                                                
            model.addConstr((MITM_down_difference[round + 1, 0, 3, col, 2] == 1) >> (MITM_down_difference[round, 3, 0, col, 1] + MITM_down_difference[round, 3, 2, col, 1] == 2 ))
            model.addConstr((MITM_down_difference[round + 1, 0, 2, col, 2] == 1) >> (MITM_down_difference[round, 3, 1, col, 1] + MITM_down_difference[round, 3, 2, col, 1] == 2 ))
            model.addConstr((MITM_down_difference[round + 1, 0, 0, col, 2] == 1) >> (MITM_down_difference[round, 3, 0, col, 1] + MITM_down_difference[round, 3, 2, col, 1] + MITM_down_difference[round, 3, 3, col, 1] >= 2 ))
            model.addConstr((MITM_down_difference[round + 1, 0, 1, col, 2]) == 0)

        #permutation
        for round, row, col in product(range(MITM_down_size), range(4), range(4)):
            model.addConstr(MITM_down_difference[round, 2, row, col, 1] == MITM_down_difference[round, 3, 0, (col+row) % 4, 1])
        
        #AK
        for round, row, col, color in product(range(MITM_down_size), range(4), range(4), range(2)):
            model.addConstr(MITM_down_difference[round, 2, row, col, color] == MITM_down_difference[round, 1, row, col, color])

        #SB
        for round, row, col in product(range(MITM_down_size), range(4), range(4)):
            model.addConstr((MITM_down_difference[round, 2, row, col, 0] == 1) >> (MITM_down_difference[round, 1, row, col, 0] == 1))
            model.addConstr((MITM_down_difference[round, 2, row, col, 1] == 1) >> (MITM_down_difference[round, 1, row, col, 1] == 1))
            model.addConstr((MITM_down_difference[round, 2, row, col, 2] == 1) >> (MITM_down_difference[round, 1, row, col, 1] == 1))

        #Link between MITM down and differential down
        for round, row, col in product(range(MITM_down_size), range(4), range(4)):
            model.addConstr((MITM_down_difference[round, 0, row, col, 1] == 1) >> (MITM_down_state[round, 0, row, col, 0] == 0))
        
        #------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        ### MITM Backward Propagation of the state

        #color constraints
        for round, step, row, col in product(range(MITM_down_size), range(4), range(4), range(4)):
            model.addConstr(gp.quicksum(MITM_down_state[round, step, row, col, color] for color in range(3)) == 1) 
        
        #state test is performed only after MC (before M-1)
        for round, step, row, col in product(range(MITM_down_size), range(1, 4), range(4), range(4)):
            model.addConstr(MITM_down_state[round, step, row, col, 2] == 0)
        
        #state test is performed only where the difference is known
        for round, row, col in product(range(MITM_down_size), range(4), range(4)):
            model.addConstr((MITM_down_difference[round, 0, row, col, 0] == 1) >> (MITM_down_state[round, 0, row, col, 2] == 0))
        
        #state test are necesserly useless in the last round of the MITM
        for row, col in product(range(4), range(4)):
            model.addConstr((MITM_down_state[MITM_down_size-1, 0, row, col, 2] == 0))
        
        #state test are made only if some differences are zero in the next round (if not state test are non sense)
        for round, col in product(range(0,MITM_down_size-1), range(4)):
            model.addConstr((MITM_down_state[round, 0, 0, col, 2] == 1) >> (gp.quicksum(MITM_down_difference[round+1, 0, row_diff, (col+1)%4, 0] for row_diff in [1]) >= 1))
            model.addConstr((MITM_down_state[round, 0, 1, col, 2] == 1) >> (gp.quicksum(MITM_down_difference[round+1, 0, row_diff, (col +row_diff)%4, 0] for row_diff in [1,2,3]) >= 1))
            model.addConstr((MITM_down_state[round, 0, 2, col, 2] == 1) >> (gp.quicksum(MITM_down_difference[round+1, 0, row_diff, (col +row_diff)%4, 0] for row_diff in [1,3]) >= 1))
            model.addConstr((MITM_down_state[round, 0, 3, col, 2] == 1) >> (gp.quicksum(MITM_down_difference[round+1, 0, row_diff, (col +row_diff)%4, 0] for row_diff in [0,3]) >= 1))
        
        #to ensure state test to be usefull, they need to make us win at least two key
        for round, row, col in product(range(MITM_down_size-1), range(4), range(4)):
            model.addConstr((MITM_down_state[round, 0, row, col, 2] == 1) >> (gp.quicksum(MITM_down_state[round+1, 1, row_2, col_2, 0] for row_2 in range(2) for col_2 in range(4)) >= 1))
        
        #MC
        for round, col in product(range(MITM_down_size - 1), range(4)):
                model.addConstr((MITM_down_state[round, 3, 0, col, 0] == gp.or_(MITM_down_state[round + 1, 0, row, col, 0] for row in [1])))
                model.addConstr((MITM_down_state[round, 3, 1, col, 0] == gp.or_(MITM_down_state[round + 1, 0, row, col, 0] for row in [1, 2, 3])))
                model.addConstr((MITM_down_state[round, 3, 2, col, 0] == gp.or_(MITM_down_state[round + 1, 0, row, col, 0] for row in [1, 3])))
                model.addConstr((MITM_down_state[round, 3, 3, col, 0] == gp.or_(MITM_down_state[round + 1, 0, row, col, 0] for row in [0, 3])))

        #permutation
        for round, row, col in product(range(MITM_down_size), range(4), range(4)):
            for col in range(4):
                model.addConstr((MITM_down_state[round, 1, row, col, 1] == 1) >> (MITM_down_state[round, 2, row, (col+row)%4, 1] == 1))
                model.addConstr((MITM_down_state[round, 1, row, col, 0] == 1) >> (MITM_down_state[round, 2, row, (col+row)%4, 1] == 0))
        
        #key_add
        for round, row, col in product(range(MITM_down_size), range(2), range(4)):
                    model.addConstr((key[round + structure_size + MITM_up_size + distinguisher_size, row, col, 2] == 1) >> (MITM_down_state[round, 1, row, col, 1] == 0))
                    model.addConstr((key[round + structure_size + MITM_up_size + distinguisher_size, row, col, 0] == 1) >> (MITM_down_state[round, 1, row, col, 1] == 0))
                    
                    model.addConstr((MITM_down_state[round, 1, row, col, 2] == 1) >> (key[round + structure_size + MITM_up_size + distinguisher_size, row, col, 1] + MITM_down_state[round, 2, row, col, 1] <= 1))
                    model.addConstr((MITM_down_state[round, 1, row, col, 2] == 1) >> (key[round + structure_size + MITM_up_size + distinguisher_size, row, col, 3] + MITM_down_state[round, 2, row, col, 1] <= 1))
                    model.addConstr((MITM_down_state[round, 1, row, col, 0] == 1) >> (key[round + structure_size + MITM_up_size + distinguisher_size, row, col, 1] + MITM_down_state[round, 2, row, col, 1] <= 1))
                    model.addConstr((MITM_down_state[round, 1, row, col, 0] == 1) >> (key[round + structure_size + MITM_up_size + distinguisher_size, row, col, 3] + MITM_down_state[round, 2, row, col, 1] <= 1))
                    
                    model.addConstr((MITM_down_state[round, 2, row, col, 0] == 1) >> (MITM_down_state[round, 1, row, col, 1] == 0))

                    model.addConstr(MITM_down_state[round, 1, row+2, col, 0] == MITM_down_state[round, 2, row+2, col, 0])
        
        #SB
        for round, row, col in product(range(MITM_down_size), range(4), range(4)):
            model.addConstr(MITM_down_state[round, 0, row, col, 1] == MITM_down_state[round, 1, row, col, 1])

        model.optimize() 

        if model.Status == GRB.OPTIMAL:
            print(count_blue.getValue())
            print(fix_number.getValue())

            fix = fix_number.getValue()
            blue = count_blue.getValue()
            red = count_red.getValue()

            left_side = np.zeros((total_round, 4, 4, 4))
            right_side = np.zeros((total_round, 4, 4, 4))
            key_state = np.zeros((total_round, 4, 4))

            for step, row, col, in product(range(4), range(4), range(4)):
                for round in range(structure_size):
                    if blue_structure_state[round, step, row, col, 1].X == 1:
                        left_side[round, step, row, col] = 2 
                    if blue_structure_state[round, step, row, col, 2].X == 1:
                        left_side[round, step, row, col] = 3 
                
                for round in range(MITM_up_size):
                    if MITM_up_state[round, step, row, col, 1].X == 1:
                        left_side[round + structure_size, step, row, col] = 1 
                    if MITM_up_state[round, step, row, col, 2].X == 1:
                        left_side[round + structure_size, step, row, col] = 4

                for round in range(distinguisher_size):
                    if distinguisher[round, step, row, col, 1].X == 1:
                        right_side[round + structure_size + MITM_up_size, step, row, col] = 8
                    if distinguisher[round, step, row, col, 2].X == 1:
                        right_side[round + structure_size + MITM_up_size, step, row, col] = 5
                    if distinguisher[round, step, row, col, 3].X == 1:
                        right_side[round + structure_size + MITM_up_size, step, row, col] = 6
                
                for round in range(MITM_down_size):
                    if MITM_down_state[round, step, row, col, 1].X == 1:
                        left_side[round + structure_size + MITM_up_size + distinguisher_size] = 2
                    if MITM_down_state[round, step, row, col, 2].X == 1:
                        left_side[round + structure_size + MITM_up_size + distinguisher_size] = 4


            
            for step, row, col, in product(range(4), range(4), range(4)):
                for round in range(structure_size):
                    if red_structure_state[round, step, row, col, 1].X == 1:
                        right_side[round, step, row, col] = 1 
                    if red_structure_state[round, step, row, col, 2].X == 1:
                        right_side[round, step, row, col] = 3 
                
                for round in range(MITM_up_size):
                    if MITM_up_difference[round, step, row, col, 1].X == 1:
                        right_side[round + structure_size, step, row, col] = 1
                    if MITM_up_difference[round, step, row, col, 2].X == 1:
                        right_side[round + structure_size, step, row, col] = 7
                    if MITM_up_difference[round, step, row, col, 3].X == 1:
                        right_side[round + structure_size, step, row, col] = 9
                
                for round in range(MITM_down_size):
                    if MITM_down_difference[round, step, row, col, 1].X == 1:
                        right_side[round + structure_size + MITM_up_size + distinguisher_size, step, row, col] = 2
                    if MITM_down_difference[round, step, row, col, 2].X == 1:
                        right_side[round + structure_size + MITM_up_size + distinguisher_size, step, row, col] = 7
                    if MITM_down_difference[round, step, row, col, 3].X == 1:
                        right_side[round + structure_size + MITM_up_size + distinguisher_size, step, row, col] = 9
            
            for round, row, col in product(range(total_round), range(4), range(4)):
                if key[round, row, col, 1].X == 1:
                    key_state[round, row, col] = 1
                elif key[round, row, col, 2].X == 1:
                    key_state[round, row, col] = 2
                elif key[round, row, col, 3].X == 1:
                    key_state[round, row, col] = 3
            return([True,fix, blue, red, left_side, right_side, key_state])
        
        else :
            print("INFEASIBLE")


def affichage(f,b,r,B,R,K):
    for round in range(len(B)):
        print("TOUR", round)
        print("\033[90m  _ _X_ _   _ _Y_ _   _ _Z_ _   _ _W_ _       _ _K_ _       _ _X_ _  _ _Y_ _  _ _Z_ _  _ _W_ _")
        for row in range(len(B[0][0])):
            for step in range(len(B[0])):
                print("\033[90m|", end="")
                for col in range(len(B[0][0][0])):
                    if B[round][step][row][col] == 0 :
                        print("\033[90m ■", end="")
                    elif B[round][step][row][col] == 1 :
                        print("\033[91m ■", end="")
                    elif B[round][step][row][col] == 2 :
                        print("\033[94m ■", end="")
                    elif B[round][step][row][col] == 3 :
                        print("\033[95m F", end="")
                    elif B[round][step][row][col] == 4 :
                        print("\033[95m S", end="")
                    elif B[round][step][row][col] == 5 :
                        print("\033[95m O", end="")
                    elif B[round][step][row][col] == 6 :
                        print("\033[95m 0", end="")
                    elif B[round][step][row][col] == 7 :
                        print("\033[95m P", end="")
                    elif B[round][step][row][col] == 8 :
                        print("\033[95m ■", end="")
                    elif B[round][step][row][col] == 9 :
                        print("\033[95m C", end="")

                print("\033[90m|", end="")
            print("    |", end="")
            for col in range(len(K[0][0])):
                if K[round][row][col] == 0 :
                    print("\033[90m ■", end="")
                elif K[round][row][col] == 1 :
                    print("\033[91m ■", end="")
                elif K[round][row][col] == 2 :
                    print("\033[94m ■", end="")
                elif K[round][row][col] == 3 :
                    print("\033[95m ■", end="")
            print("\033[90m|    |", end="")
            for step in range(len(R[0][0])):
                for col in range(len(R[0][0][0])):
                    if R[round][step][row][col] == 0 :
                        print("\033[90m ■", end="")
                    elif R[round][step][row][col] == 1 :
                        print("\033[91m ■", end="")
                    elif R[round][step][row][col] == 2 :
                        print("\033[94m ■", end="")
                    elif R[round][step][row][col] == 3 :
                        print("\033[95m F", end="")
                    elif R[round][step][row][col] == 4 :
                        print("\033[95m S", end="")
                    elif R[round][step][row][col] == 5 :
                        print("\033[95m O", end="")
                    elif R[round][step][row][col] == 6 :
                        print("\033[95m 0", end="")
                    elif R[round][step][row][col] == 7 :
                        print("\033[95m P", end="")
                    elif R[round][step][row][col] == 8 :
                        print("\033[95m ■", end="")
                    elif R[round][step][row][col] == 9 :
                        print("\033[95m C", end="")
                    

                print("\033[90m|", end="")
            print("")
        print("")
    print("fix number =", f)
    print("blue key =", b)
    print("red key =" , r)

attaque = structure(4, 4, 4, 4, 3)
if attaque[0]:
    affichage(attaque[1], attaque[2], attaque[3], attaque[4], attaque[5], attaque[6])      


