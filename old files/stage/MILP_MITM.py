#MILP_STRUCTURE
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

def affichage_grille(key, key_0, key_1, key_2, x_list, y_list, z_list):
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
        print("  _ _X_ _    _ _Y_ _    _ _Z_ _      _K_E_Y_      _K_E_Y_0   _K_E_Y_1   _K_E_Y_2")
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
            print("\033[90m|")
        print("  ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾      ‾ ‾ ‾ ‾      ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾\n \n")

options = {
"WLSACCESSID" : "105deaf2-be7c-48e6-8994-7ada7350ab7a",
	"WLSSECRET" : "6eb5112f-6d6c-471f-9931-c633dc77c9b4",
	"LICENSEID" : 2534357
}

with gp.Env(params=options) as env, gp.Model(env=env) as model:
    print(("Structure sur 6 tours, MITM sur 17 tours"))
    
    #ATTACK PARAMETERS
    structure_round = 6
    MITM_round = 8
    total_round = structure_round + MITM_round

    key_space_size = 3  

    #KEY MATERIAL
    key_index_0 = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]])

    key_index_copy = key_index_0.copy()
    list_of_key_index = np.zeros((total_round,4,4))
    for index in range(total_round):
        list_of_key_index[index, :, :] = key_index_copy
        key_index_copy = tweakey(key_index_copy)

    #GUROBI Variables initalization
    state = np.zeros((total_round, 3, 4, 4, 4), dtype = object) #[round, (X Y or Z), row, column, colour (0=red, 1=blue, 2=purple, 3=Fix)]

    inter_key = np.zeros((total_round,key_space_size, 4, 4, 3), dtype = object) #[round, inter key index, row, column, colour (0=red, 1=blue, 2=purple)]

    key = np.zeros((total_round, 4, 4, 3), dtype = object) #[round, row, column, colour (0=red, 1=blue, 2=purple)]

    key_knowledge = np.zeros((4,4,2), dtype = object) #the total amount of red and blue guess for each key element [row,column,colour (0=red, 1=blue)]

    binary_bound_for_key_knowledge = np.zeros((4,4,2,2), dtype = object) #binary variable to constraint the key knowledge following the key schedule(if three or more word of the same key element are guess, all the corresponding element are guessed)

    MITM_binary_bound_for_key_knowledge = np.zeros((4,4,2,2), dtype = object) #binary variable to constraint the key knowledge during the MITM step (make some possible guess of the key)

    blue_MITM_state = np.zeros((MITM_round, 3, 4, 4, 2), dtype = object) #[round, (X,Y, or Z), row, column, colour(0=unkown, 1=blue)]
 
    red_MITM_state = np.zeros((MITM_round, 3, 4, 4, 2), dtype = object)  #[round, (X,Y, or Z), row, column, colour(0=unkown, 1=red)]

    MITM_key_knowledge = np.zeros((4, 4, 3), dtype = object ) #the total amount of red and blue guess for each key element during the MITM step [row,column,colour (0=red, 1=blue)]

    MITM_inter_key = np.zeros((MITM_round, key_space_size+1, 4, 4, 3), dtype = object ) #[round, key_index, row, column, colour (0=red, 1=blue, 2=purple)]

    binary_match = np.zeros((MITM_round-1,2,4,4), dtype = object) #for each word on the right and left side of MC, 1 means we can process the MITM match

    binary_trick = np.zeros((structure_round-1,4,4,4,4), dtype = object)

    #GUROBI variable creation
    
    for round in range(structure_round - 1):
        for row in range(4):
            for col in range(4):
                for color in range(4):
                    for i in range(4):
                        binary_trick[round,row,col,color,i] = model.addVar(vtype = GRB.BINARY, name = f'name')
    

    #binary_trick[:,:,:,:,:] = model.addVar(vtype = GRB.BINARY, name = f'name')
    for round in range(total_round):
        for key_index in range(key_space_size):
            for row in range(4):
                for col in range(4):
                    for state_colour in range(4):
                        state[round, key_index, row, col, state_colour] = model.addVar(vtype = GRB.BINARY, name = f'state_tour :{round} etape :{index} ligne :{row} colonne :{col} couleur :{state_colour}')

                    for key_color in range(3):
                        inter_key[round, key_index, row, col, key_color] = model.addVar(vtype = GRB.BINARY, name = f'key_inter :{round} etape :{index} ligne :{row} colonne :{col} couleur :{key_color}')
                        key[round, row, col, key_color] = model.addVar(vtype=GRB.BINARY, name = f'key_tour:{round}_ligne:{row}_colonne:{col}_couleur:{key_color}')

                    for knowledge_colour in range(2):
                        key_knowledge[row, col, knowledge_colour] = model.addVar(lb = 0.0,ub = key_space_size*total_round, vtype = GRB.INTEGER, name=f'red_keyknowledge{row} {col} {knowledge_colour}')

                        for binary in range(2):
                            binary_bound_for_key_knowledge[row, col, knowledge_colour, binary] = model.addVar(vtype = GRB.BINARY, name=f'binary_bound_for_key_knowledge {row} {col} {knowledge_colour} {binary}' )
                            MITM_binary_bound_for_key_knowledge[row, col, knowledge_colour, binary] = model.addVar(vtype = GRB.BINARY, name=f'binary_bound_for_key_knowledge {row} {col} {knowledge_colour} {binary}' )
                            
    
    for round in range(MITM_round):
        for step in range(3):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        red_MITM_state[round, step, row,col,color] = model.addVar(vtype = GRB.BINARY, name = f'redMITMround :{round} etape{step} row{row} col{col} {color}')
                        blue_MITM_state[round, step, row,col,color] = model.addVar(vtype = GRB.BINARY, name = f'redMITMround :{round} etape{step} row{row} col{col} {color}')
                    for colour in range(3):                
                        MITM_key_knowledge[row,col,colour] = model.addVar(vtype = GRB.INTEGER)
        for index in range(key_space_size + 1):
            for row in range(4):
                for col in range(4):
                    for color in range(3):
                        MITM_inter_key[round, index, row, col, color] = model.addVar(vtype = GRB.BINARY)
        
    for round in range(MITM_round - 1):
        for side in range(2):
            for row in range(4):
                for col in range(4):
                    binary_match[round, side, row, col] = model.addVar(vtype = GRB.BINARY)
 
    model.update()

    #OBJECTIVE FUNCTION : Minimizing the quantity of key guess to minimize the time complexity of the attack

    objective = gp.quicksum(MITM_inter_key[round, key_index, np.where(list_of_key_index[round + structure_round] == key_index_0[row, col])[0][0], np.where(list_of_key_index[round + structure_round] == key_index_0[row, col])[1][0], 2] for round in range(MITM_round) for key_index in range(key_space_size + 1) for row in range(4) for col in range(4))
    objective2 = gp.quicksum(state[0, 0, row, col, 3] for row in range(4) for col in range(4)) #maximizing fix number in the first state to decrease data complexity
    model.setObjective(objective - objective2, sense = GRB.MINIMIZE)

    #GENERAL KEY CONSTRAINTS

    for round in range(total_round):
        #Each inter key cannot know the full key (i.e each inter key must have at least on non red and one non blue element)
        model.addConstr(gp.quicksum(inter_key[round, 0, row, col, 0]for row in range(4) for col in range(4)) >= 1)
        model.addConstr(gp.quicksum(inter_key[round, 0, row, col, 1]for row in range(4) for col in range(4)) >= 1)

        if key_space_size >= 2:
            model.addConstr(gp.quicksum(inter_key[round, 1, row, col, 0]for row in range(4) for col in range(4)) >= 1)
            model.addConstr(gp.quicksum(inter_key[round, 1, row, col, 1]for row in range(4) for col in range(4)) >= 1)

        if key_space_size >= 3:
            model.addConstr(gp.quicksum(inter_key[round, 2, row, col, 0]for row in range(4) for col in range(4)) >= 1)
            model.addConstr(gp.quicksum(inter_key[round, 2, row, col, 1]for row in range(4) for col in range(4)) >= 1)
        
        for key_index in range(key_space_size):
            for row in range(4):
                for col in range(4):
                    #Inter key and key must be red,bleu or purple
                    model.addConstr((gp.quicksum(inter_key[round, key_index, row, col, i] for i in range(3)) == 1))
                    model.addConstr(gp.quicksum(key[round, row, col, i] for i in range(3)) == 1)

                    #Final key is the XOR of the inter key (i.e if one word of the inter key is blue/red the key is blue/red, the key word can be purple only if the three corresponding word are purple)
                    model.addConstr((inter_key[round, key_index, row, col, 0] == 1) >> (key[round, row, col, 0] == 1))
                    model.addConstr((inter_key[round, key_index, row, col, 0] == 1) >> (key[round, row, col, 1] == 0))
                    model.addConstr((inter_key[round, key_index, row, col, 0] == 1) >> (key[round, row, col, 2] == 0))
                    model.addConstr((inter_key[round, key_index, row, col, 1] == 1) >> (key[round, row, col, 1] == 1))
                    model.addConstr((inter_key[round, key_index, row, col, 1] == 1) >> (key[round, row, col, 0] == 0))
                    model.addConstr((inter_key[round, key_index, row, col, 1] == 1) >> (key[round, row, col, 2] == 0))

                    model.addConstr(key[round, row, col, 2] == gp.and_([inter_key[round, index, row, col, 2] for index in range(key_space_size)]))
    
    #Key schedule :  if we guess more than two time a key word, we guessed it for all the others
    for row in range(4):
        for col in range(4):
            for colour in range(2):
                key_knowledge[row,col,colour] = gp.quicksum(inter_key[round, key_index, np.where(list_of_key_index[round] == key_index_0[row,col])[0][0], np.where(list_of_key_index[round] == key_index_0[row,col])[1][0], key_color] for round in range(total_round) for key_index in range(key_space_size) for key_color in [colour,2] )
                model.addConstr(binary_bound_for_key_knowledge[row, col, colour,0] + binary_bound_for_key_knowledge[row, col,colour, 1] == 1)
                model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col,colour, 0], True, key_knowledge[row,col,colour], gp.GRB.GREATER_EQUAL, key_space_size*total_round) 
                model.addGenConstrIndicator(binary_bound_for_key_knowledge[row, col,colour, 1], True, key_knowledge[row,col,colour], gp.GRB.LESS_EQUAL, 2.0)

    #MITM key 
    for round in range(MITM_round):
        for index in range(key_space_size+1):
            for row in range(4):
                for col in range(4):
                    #MITM key must be red blue or purple
                    model.addConstr(gp.quicksum(MITM_inter_key[round, index, row, col, i] for i in range(3)) == 1)
                    #Purple element of the key during the structure step are necesserly purple during the MITM step
                    model.addConstr((key[round + structure_round, row, col, 2] == 1) >> (MITM_inter_key[round, 0, row, col, 2] == 1))

    for row in range(4):
        for col in range(4):
            for colour in range(2):
                #for each key element, for the blue and red side, if we guess the key or subkey same word more then two time, the full key word is know. 
                MITM_key_knowledge[row,col,colour] = gp.quicksum(MITM_inter_key[round,key_index,np.where(list_of_key_index[round+structure_round] == key_index_0[row,col])[0][0], np.where(list_of_key_index[round+structure_round] == key_index_0[row,col])[1][0], key_color] for round in range(MITM_round) for key_index in range(key_space_size+1) for key_color in [colour,2])
                model.addConstr(MITM_binary_bound_for_key_knowledge[row, col, colour,0] + MITM_binary_bound_for_key_knowledge[row, col,colour, 1] == 1)
                model.addGenConstrIndicator(MITM_binary_bound_for_key_knowledge[row, col,colour, 0], True, MITM_key_knowledge[row,col,colour], gp.GRB.GREATER_EQUAL, (key_space_size+1)*MITM_round) 
                model.addGenConstrIndicator(MITM_binary_bound_for_key_knowledge[row, col,colour, 1], True, MITM_key_knowledge[row,col,colour], gp.GRB.LESS_EQUAL, 2.0)

    for round in range(MITM_round):
        for index in range(1,key_space_size+1):
            for row in range(4):
                for col in range(4):
                    #if the subkey is red/blue the full key cannot be red or blue
                    model.addConstr((MITM_inter_key[round, index, row, col, 0] == 1) >> (MITM_inter_key[round, 0, row, col, 1] == 0))
                    model.addConstr((MITM_inter_key[round, index, row, col, 1] == 1) >> (MITM_inter_key[round, 0, row, col, 0] == 0))
                    for color in range(2):
                        model.addConstr(inter_key[round + structure_round, index - 1, row, col, color] == MITM_inter_key[round, index, row, col, color]) #inter key are the same, we only guess key word
    
                    
    #STATE CONSTRAINTS IN THE STRUCTURE

    #On ne peux utiliser plus de 16 fixs
    model.addConstr(gp.quicksum(state[tour, index, row, col ,3] for tour in range(structure_round) for index in range(3) for row in range(4) for col in range(4)) <= 16)

     #Starting constraint
    for row in range(4):
        for col in range(4):
            model.addConstr(state[0, 0, row, col, 1] == 0) # premier état sans mot connu que de bleu
            model.addConstr(state[0, 0, row, col, 2] == 0) # premier état sans mot violet(que fixe autorisés)
            model.addConstr(state[structure_round-1, 2, row, col, 0] == 0) # dernier état sans mot connu que de rouge 

    #state constraint : un état ne peux être que bleu rouge violet ou fixe 
    for tour in range(structure_round):
        for index in range(3):
            for row in range(4):
                for col in range(4):
                    model.addConstr((gp.quicksum(state[tour, index, row, col, i] for i in range(4)) == 1))

    #contraintes de la clé sur l'état
    for tour in range(structure_round):
        for row in range(2):
            for col in range(4):
                #model.addConstr((key[tour, row, col, 0] == 1) >> (state[tour, 0, row, col, 1] == 0)) #si clé rouge on ne peut avoir état bleu
                #model.addConstr((key[tour, row, col, 1] == 1) >> (state[tour, 0, row, col, 0] == 0)) #si clé bleu on ne peut avoir état rouge

                model.addConstr((state[tour,1,row,col,0] == 1) >>  (key[tour,row,col,1] == 0)) #etat droite rouge, clé ne peut être bleu
                model.addConstr((state[tour,1,row,col,0] == 1) >>  (state[tour,0,row,col,1] == 0)) #etat droite rouge, état gauche ne peut être bleu

                model.addConstr((state[tour,1,row,col,1] == 1) >>  (key[tour,row,col,0] == 0)) #etat droite bleu, clé ne peut être rouge
                model.addConstr((state[tour,1,row,col,1] == 1) >>  (state[tour,0,row,col,0] == 0)) #etat droite bleu, état gauche ne peut être rouge

                #model.addConstr((state[tour,0,row,col,3] == 1) >> (state[tour,1,row,col,0] == key[tour,row,col,0]))
                #model.addConstr((state[tour,0,row,col,3] == 1) >> (state[tour,1,row,col,1] == key[tour,row,col,1]))
                #model.addConstr((state[tour,0,row,col,3] == 1) >> (state[tour,1,row,col,2] == key[tour,row,col,2]))

                model.addConstr((state[tour,1,row,col,2] == 1) >>  (key[tour,row,col,0] == 0)) #etat droite violet, clé ne peut être rouge
                model.addConstr((state[tour,1,row,col,2] == 1) >>  (state[tour,0,row,col,0] == 0)) #etat droite violet, état gauche ne peut être rouge

                model.addConstr((state[tour,1,row,col,2] == 1) >>  (key[tour,row,col,1] == 0)) #etat droite violet, clé ne peut être rouge
                model.addConstr((state[tour,1,row,col,2] == 1) >>  (state[tour,0,row,col,1] == 0)) #etat droite rouge, état gauche ne peut être rouge 

                #model.addConstr((key[tour, row, col, 1] == 1) >> (state[tour, 1, row, col, 1] == 1)) # blue key -> next state is blue
                #model.addConstr((key[tour, row, col, 0] == 1) >> (state[tour, 0, row, col, 0] == 1)) #red key -> previous state is red

                model.addConstr(state[tour,1, row, col, 1] == gp.or_(state[tour,0,row,col,1],key[tour,row,col,1])) #Bleu a droite que si on au moins un bleu dans la clé ou l'état d'avant
                model.addConstr(state[tour,0, row, col, 0] == gp.or_(state[tour,1,row,col,0],key[tour,row,col,0])) #Rouge a gauche que si on a un rouge dans la clé ou a droite

        for row in range(2,4): #Partie inférieur de la clé ne modifie pas (sauf fixe qui devient violet)
            for col in range(4):
                model.addConstr((state[tour,0, row, col, 0] == 1) >> (state[tour,1, row, col, 0] == 1))
                model.addConstr((state[tour,0, row, col, 1] == 1) >> (state[tour,1, row, col, 1] == 1))
                model.addConstr((state[tour,0, row, col, 2] == 1) >> (state[tour,1, row, col, 2] == 1))
                model.addConstr((state[tour,0, row, col, 3] == 1) >> (state[tour,1, row, col, 2] == 1))

    #Contrainte de la permutation :
    for tour in range(structure_round):
        for col in range(4):
            for indice in range(3):
                model.addConstr((state[tour, 1, 0, col, indice] == 1) >> (state[tour, 2, 0, col, indice] == 1))
                model.addConstr((state[tour, 1, 1, col, indice] == 1) >> (state[tour, 2, 1, (col + 1) % 4, indice] == 1))
                model.addConstr((state[tour, 1, 2, col, indice] == 1) >> (state[tour, 2, 2, (col + 2) % 4, indice] == 1))
                model.addConstr((state[tour, 1, 3, col, indice] == 1) >> (state[tour, 2, 3, (col + 3) % 4, indice] == 1))
            model.addConstr((state[tour, 1, 0, col, 3] == 1) >> (state[tour, 2, 0, col, 2] == 1))
            model.addConstr((state[tour, 1, 1, col, 3] == 1) >> (state[tour, 2, 1, (col + 1) % 4, 2] == 1))
            model.addConstr((state[tour, 1, 2, col, 3] == 1) >> (state[tour, 2, 2, (col + 2) % 4, 2] == 1))
            model.addConstr((state[tour, 1, 3, col, 3] == 1) >> (state[tour, 2, 3, (col + 3) % 4, 2] == 1))

    #Contrainte du MC :
    for tour in range(structure_round-1):
        for col in range(4):
            #si un mot est rouge il ne peux être multiplier par un mot bleu et inversement
            model.addConstr((state[tour, 2, 0, col, 0] == 1) >> (state[tour, 2, 2, col, 1] == 0)) 
            model.addConstr((state[tour, 2, 0, col, 0] == 1) >> (state[tour, 2, 3, col, 1] == 0))

            model.addConstr((state[tour, 2, 1, col, 0] == 1) >> (state[tour, 2, 2, col, 1] == 0)) 

            model.addConstr((state[tour, 2, 2, col, 0] == 1) >> (state[tour, 2, 0, col, 1] == 0)) 
            model.addConstr((state[tour, 2, 2, col, 0] == 1) >> (state[tour, 2, 1, col, 1] == 0))
            model.addConstr((state[tour, 2, 2, col, 0] == 1) >> (state[tour, 2, 3, col, 1] == 0))

            model.addConstr((state[tour, 2, 3, col, 0] == 1) >> (state[tour, 2, 0, col, 1] == 0)) 
            model.addConstr((state[tour, 2, 3, col, 0] == 1) >> (state[tour, 2, 2, col, 1] == 0)) 

            model.addConstr((state[tour, 2, 0, col, 1] == 1) >> (state[tour, 2, 2, col, 0] == 0)) 
            model.addConstr((state[tour, 2, 0, col, 1] == 1) >> (state[tour, 2, 3, col, 0] == 0))

            model.addConstr((state[tour, 2, 1, col, 1] == 1) >> (state[tour, 2, 2, col, 0] == 0)) 

            model.addConstr((state[tour, 2, 2, col, 1] == 1) >> (state[tour, 2, 0, col, 0] == 0)) 
            model.addConstr((state[tour, 2, 2, col, 1] == 1) >> (state[tour, 2, 1, col, 0] == 0))
            model.addConstr((state[tour, 2, 2, col, 1] == 1) >> (state[tour, 2, 3, col, 0] == 0))

            model.addConstr((state[tour, 2, 3, col, 1] == 1) >> (state[tour, 2, 0, col, 0] == 0)) 
            model.addConstr((state[tour, 2, 3, col, 1] == 1) >> (state[tour, 2, 2, col, 0] == 0)) 
            #PREMIERE LIGNE
            model.addConstr(binary_trick[tour, 0, col, 2, 0] + binary_trick[tour, 0, col, 2, 1] + binary_trick[tour, 0, col, 3, 0] + binary_trick[tour, 0, col, 1, 0] + binary_trick[tour, 0, col, 0, 0] == 1)
            
            model.addConstr((binary_trick[tour, 0, col, 2, 0] == 1) >> (state[tour+1, 0, 0, col, 2] == 1))#violet et pas fixe
            #model.addConstr((binary_trick[tour, 0, col, 2, 0] == 1) >> (state[tour+1, 0, 3, col, 3] == 0))#violet et pas fixe
            model.addConstr((binary_trick[tour, 0, col, 2, 1] == 1) >> (state[tour+1, 0, 0, col, 2] + state[tour+1, 0, 3, col, 3] == 2)) #violet et fixe
            model.addConstr((binary_trick[tour, 0, col, 2, 2] == 1))
            model.addConstr((binary_trick[tour, 0, col, 3, 0] == 1) >> (state[tour+1, 0, 0, col, 3] == 1)) #fixe
            model.addConstr((binary_trick[tour, 0, col, 1, 0] == 1) >> (state[tour+1, 0, 0, col, 1] == 1)) #bleu
            model.addConstr((binary_trick[tour, 0, col, 0, 0] == 1) >> (state[tour+1, 0, 0, col, 0] == 1)) #rouge
            for i in [1,2,3]:
                model.addConstr((binary_trick[tour, 0, col, 0,i] == 0))
                model.addConstr((binary_trick[tour, 0, col, 1,i] == 0))
                model.addConstr((binary_trick[tour, 0, col, 3,i] == 0))
            #si on a un mot rouge à droite sur la premiére ligne Si 
            # on ne peux pas avoir un état tout violet, fix compris
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((binary_trick[tour, 0,col, 0, 0] == 1) >> (state[tour, 2, 0, col, 2+i] + state[tour, 2, 2, col, 2+j] + state[tour, 2, 3, col, 2+k] <= 2))
            #on ne peux pas avoir de bleu dans l'état précédent
            model.addConstr((binary_trick[tour, 0, col, 0, 0] == 1) >> (state[tour, 2, 0, col, 1] == 0))
            model.addConstr((binary_trick[tour, 0, col, 0, 0] == 1) >> (state[tour, 2, 2, col, 1] == 0))
            model.addConstr((binary_trick[tour, 0, col, 0, 0] == 1) >> (state[tour, 2, 3, col, 1] == 0))

            #idem en bleu, on ne peux avoir que des violets ou fix avant 
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((binary_trick[tour, 0, col, 1, 0] == 1) >> (state[tour, 2, 0, col, 2+i] + state[tour, 2, 2, col, 2+j] + state[tour, 2, 3, col, 2+k] <= 2))
            #on ne peux pas avoir de rouge dans l'état précédent
            model.addConstr((binary_trick[tour, 0, col, 1, 0] == 1) >> (state[tour, 2, 0, col, 0] == 0))
            model.addConstr((binary_trick[tour, 0, col, 1, 0] == 1) >> (state[tour, 2, 2, col, 0] == 0))
            model.addConstr((binary_trick[tour, 0, col, 1, 0] == 1) >> (state[tour, 2, 3, col, 0] == 0))

            #si on a un mot violet et pas de fixe en on ne peux avoir que des mots violet avant (pas de rouge ou bleus)
            model.addConstr((binary_trick[tour, 0, col, 2, 0] == 1) >> (state[tour, 2, 0, col, 0] == 0))
            model.addConstr((binary_trick[tour, 0, col, 2, 0] == 1) >> (state[tour, 2, 2, col, 0] == 0))
            model.addConstr((binary_trick[tour, 0, col, 2, 0] == 1) >> (state[tour, 2, 3, col, 0] == 0))

            model.addConstr((binary_trick[tour, 0, col, 2, 0] == 1) >> (state[tour, 2, 0, col, 1] == 0))
            model.addConstr((binary_trick[tour, 0, col, 2, 0] == 1) >> (state[tour, 2, 2, col, 1] == 0))
            model.addConstr((binary_trick[tour, 0, col, 2, 0] == 1) >> (state[tour, 2, 3, col, 1] == 0))

            #Si le mot est violet et que le dernier est fixe, le précédent dernier est violet.
            model.addConstr((binary_trick[tour, 0, col, 2, 1] == 1) >> (state[tour, 2, 3, col, 2] + state[tour, 2, 3, col, 3] == 1))

            #DEUXIEME ligne
            model.addConstr(binary_trick[tour, 1, col, 2, 0] + binary_trick[tour, 1, col, 2, 1] + binary_trick[tour, 1, col, 2, 2] + binary_trick[tour, 1, col, 3, 0] + binary_trick[tour, 1, col, 1, 0] + binary_trick[tour, 1, col, 0, 0] == 1)
            
            model.addConstr((binary_trick[tour, 1, col, 2, 0] == 1) >> (state[tour+1, 0, 1, col, 2] == 1)) #violet et pas fixe
            #model.addConstr((binary_trick[tour, 1, col, 2, 0] == 1) >> (state[tour+1, 0, 3, col, 3] == 0)) #violet et pas fixe

            model.addConstr((binary_trick[tour, 1, col, 2, 1] == 1) >> (state[tour + 1, 0, 1, col, 2] + state[tour + 1, 0, 3, col, 3] == 2)) #violet et fixe
            model.addConstr((binary_trick[tour, 1, col, 2, 1] == 1) >> (state[tour + 1, 0, 2, col, 3] == 0)) #violet et fixe

            model.addConstr((binary_trick[tour, 1, col, 2, 2] == 1) >> (state[tour + 1, 0, 1, col, 2] + state[tour + 1, 0, 3, col, 3] + state[tour + 1, 0, 2, col, 3] == 3)) #violet et 2 fixe

            model.addConstr((binary_trick[tour, 1, col, 2, 3] == 0))

            model.addConstr((binary_trick[tour, 1, col, 3, 0] == 1) >> (state[tour + 1, 0, 1, col, 3] == 1)) #fixe
            model.addConstr((binary_trick[tour, 1, col, 1, 0] == 1) >> (state[tour + 1, 0, 1, col, 1] == 1)) #bleu
            model.addConstr((binary_trick[tour, 1, col, 0, 0] == 1) >> (state[tour + 1 ,0 ,1 ,col, 0] == 1)) #rouge
            for i in [1,2,3]:
                model.addConstr((binary_trick[tour, 1, col, 0,i] == 0))
                model.addConstr((binary_trick[tour, 1, col, 1,i] == 0))
                model.addConstr((binary_trick[tour, 1, col, 3,i] == 0))
            #si on a un mot rouge :
            model.addConstr((binary_trick[tour, 1, col, 0, 0] == 1) >> (state[tour, 2, 0, col, 0] == 1))
            #si on a un mot bleu :
            model.addConstr((binary_trick[tour, 1, col, 1, 0] == 1) >> (state[tour, 2, 0, col, 1] == 1))
            #si on a un violet et pas de fixe, soit le précédent est violet soit fixe
            model.addConstr((binary_trick[tour, 1, col, 2, 0] == 1) >> (state[tour, 2, 0, col, 2]+state[tour, 2, 0, col, 3] == 1))
            #si on a un violet et un fixe en 3, TRICK
            model.addConstr((binary_trick[tour,1,col,2,1] == 1) >> (state[tour, 2, 2,col,2] + state[tour, 2, 2,col,3] == 1))
            #si on a un violet et deux fixe TRICK
            model.addConstr((binary_trick[tour, 1, col, 2, 2] == 1) >> (state[tour, 2, 2,col,2] + state[tour, 2, 2,col,3] == 1))
            model.addConstr((binary_trick[tour, 1, col, 2, 2] == 1) >> (state[tour, 2, 2,col,2] + state[tour, 2, 2,col,3] + state[tour, 2, 3,col,2] + state[tour, 2, 3,col,3] == 1))

            #TROISIEME LIGNE
            model.addConstr(binary_trick[tour, 2, col, 2, 0] + binary_trick[tour, 2, col, 2, 1] + binary_trick[tour, 2, col, 2, 2] + binary_trick[tour, 2, col, 3, 0] + binary_trick[tour, 2, col, 1, 0] + binary_trick[tour, 2, col, 0, 0] == 1)
            
            model.addConstr((binary_trick[tour, 2, col, 2, 0] == 1) >> (state[tour + 1, 0, 2, col, 2] == 1))#violet et pas fixe
            #model.addConstr((binary_trick[tour, 2, col, 2, 0] == 1) >> (state[tour + 1, 0, 1, col, 3] + state[tour + 1, 0, 3, col, 3] <= 1))#violet et pas fixe
            model.addConstr((binary_trick[tour, 2, col, 2, 1] == 1) >> (state[tour + 1, 0, 2, col, 2] + state[tour + 1, 0, 1, col, 3] + state[tour + 1 ,0, 3, col, 3] == 3)) #violet et fixe TRICK 1
            model.addConstr((binary_trick[tour, 2, col, 2, 2] == 0))
            model.addConstr((binary_trick[tour, 2, col, 2, 3] == 0))
            model.addConstr((binary_trick[tour, 2, col, 3, 0] == 1) >> (state[tour + 1, 0, 2, col, 3] == 1)) #fixe
            model.addConstr((binary_trick[tour, 2, col, 1, 0] == 1) >> (state[tour + 1, 0, 2, col, 1] == 1)) #bleu
            model.addConstr((binary_trick[tour, 2, col, 0, 0] == 1) >> (state[tour + 1, 0, 2, col, 0] == 1)) #rouge
            for i in [1,2,3]:
                model.addConstr((binary_trick[tour, 1, col, 0,i] == 0))
                model.addConstr((binary_trick[tour, 1, col, 1,i] == 0))
                model.addConstr((binary_trick[tour, 1, col, 3,i] == 0))
            #si on a un rouge
            #on ne peux pas avoir que des violets/Fix
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((binary_trick[tour, 2, col, 0, 0] == 1) >> (state[tour, 2, 1, col, 2+i] + state[tour, 2, 2, col, 2+j] <= 1))
            #on ne peux pas avoir de bleu dans l'état précédent
            model.addConstr((binary_trick[tour, 2, col, 0, 0] == 1) >> (state[tour, 2, 1, col, 1] == 0))
            model.addConstr((binary_trick[tour, 2, col, 0, 0] == 1) >> (state[tour, 2, 2, col, 1] == 0))

            #si on a un bleu 
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((binary_trick[tour, 2, col, 1, 0] == 1) >> (state[tour, 2, 1, col, 2+i] + state[tour, 2, 2, col, 2+j] <= 1))
            #on ne peux pas avoir de rouges dans l'état précédent
            model.addConstr((binary_trick[tour, 2, col, 1, 0] == 1) >> (state[tour, 2, 1, col, 0] == 0))
            model.addConstr((binary_trick[tour, 2, col, 1, 0] == 1) >> (state[tour, 2, 2, col, 0] == 0))

            #si on a un violet, les états précédents concernés ne peuvent être bleu ou rouge
            model.addConstr((binary_trick[tour, 2, col, 2, 0] == 1) >> (state[tour, 2, 1, col, 0] == 0))
            model.addConstr((binary_trick[tour, 2, col, 2, 0] == 1) >> (state[tour, 2, 2, col, 0] == 0))

            model.addConstr((binary_trick[tour, 2, col, 2, 0] == 1) >> (state[tour, 2, 1, col, 1] == 0))
            model.addConstr((binary_trick[tour, 2, col, 2, 0] == 1) >> (state[tour, 2, 2, col, 1] == 0))

            #TRICK
            model.addConstr((binary_trick[tour, 2, col, 2, 1] == 1) >> (state[tour, 2, 1, col, 2] + state[tour, 2, 1, col, 3] + state[tour, 2, 2, col, 2] + state[tour, 2, 2, col, 3] == 2))

            #QUATRIEME LIGNE
            model.addConstr(binary_trick[tour, 3, col, 2, 0] + binary_trick[tour, 3, col,2,1] + binary_trick[tour, 3, col, 2, 2] + binary_trick[tour, 3, col, 2, 3] + binary_trick[tour, 3, col, 3, 0] + binary_trick[tour, 3, col, 1, 0] + binary_trick[tour, 3, col, 0, 0] == 1)
            
            model.addConstr((binary_trick[tour, 3, col, 2, 0] == 1) >> (state[tour + 1, 0, 3, col, 2] == 1))#violet et pas fixe
            model.addConstr((binary_trick[tour, 3, col, 2, 0] == 1) >> (state[tour + 1, 0, 0, col, 3] == 0))#violet et pas fixe
            #model.addConstr((binary_trick[tour, 3, col, 2, 0] == 1) >> (state[tour + 1, 0, 1, col, 3] == 0))
            #model.addConstr((binary_trick[tour, 3, col, 2, 0] == 1) >> (state[tour + 1, 0, 2, col, 3] == 0))

            model.addConstr((binary_trick[tour, 3, col, 2, 1] == 1) >> (state[tour + 1, 0, 3, col, 2] + state[tour + 1, 0, 0, col, 3] == 2)) #violet et fixe TRICK 1
            #model.addConstr((binary_trick[tour, 3, col, 2, 1] == 1) >> (state[tour + 1, 0, 1, col, 3] + state[tour + 1, 0, 2, col, 3] <= 1))

            model.addConstr((binary_trick[tour, 3, col, 2, 2] == 1) >> (state[tour + 1, 0, 3, col, 2] + state[tour + 1, 0, 1, col, 3] == 2)) #violet et fixe TRICK 2
            #model.addConstr((binary_trick[tour, 3, col, 2, 2] == 1) >> (state[tour + 1, 0, 2, col, 3] == 0))

            model.addConstr((binary_trick[tour, 3, col, 2, 3] == 1) >> (state[tour + 1, 0, 3, col, 2] + state[tour + 1, 0, 1, col, 3] + state[tour + 1, 0, 2, col, 3] == 3)) #violet et fixe TRICK 3

            model.addConstr((binary_trick[tour, 3, col, 3, 0] == 1) >> (state[tour + 1, 0, 3, col, 3] == 1)) #fixe
            model.addConstr((binary_trick[tour, 3, col, 1, 0] == 1) >> (state[tour + 1, 0, 3, col, 1] == 1)) #bleu
            model.addConstr((binary_trick[tour, 3, col, 0, 0] == 1) >> (state[tour+1, 0, 3, col, 0] == 1)) #rouge
            for i in [1,2]:
                model.addConstr((binary_trick[tour, 3, col, 0,i] == 0))
                model.addConstr((binary_trick[tour, 3, col, 1,i] == 0))
                model.addConstr((binary_trick[tour, 3, col, 3,i] == 0))
            #si on a un rouge
            #on ne peux pas avoir que des violets/Fix
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((binary_trick[tour, 3, col, 0, 0] == 1) >> (state[tour, 2, 0, col, 2+i] + state[tour, 2, 2, col, 2+j] <= 1))
            #on ne peux pas avoir de bleus dans l'état précédent 
            model.addConstr((binary_trick[tour, 3, col, 0, 0] == 1) >> (state[tour,2,0,col,1] == 0))
            model.addConstr((binary_trick[tour, 3, col, 0, 0] == 1) >> (state[tour,2,2,col,1] == 0))

            #si on a un bleu
            #on ne peux pas avoir que des violets/Fix
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((binary_trick[tour, 1, col, 1, 0] == 1) >> (state[tour, 2, 0, col, 2+i] + state[tour, 2, 2, col, 2+j] <= 1))
            #on ne peux pas avoir de rouge dans l'état précédent 
            model.addConstr
            model.addConstr((binary_trick[tour, 3, col, 1, 0] == 1) >> (state[tour,2,0,col,0] == 0))
            model.addConstr((binary_trick[tour, 3, col, 1, 0] == 1) >> (state[tour,2,2,col,0] == 0))

            #si on a un violet, les états précédents concernés ne peuvent être bleu ou rouge
            model.addConstr((binary_trick[tour, 3, col, 2, 0] == 1) >> (state[tour, 2, 0, col, 0] == 0))
            model.addConstr((binary_trick[tour, 3, col, 2, 0] == 1) >> (state[tour, 2, 2, col, 0] == 0))

            model.addConstr((binary_trick[tour, 3, col, 2, 0] == 1) >> (state[tour, 2, 0, col, 1] == 0))
            model.addConstr((binary_trick[tour, 3, col, 2, 0] == 1) >> (state[tour, 2, 2, col, 1] == 0))

            #si on a un violet un fix en 1 on utilise le trick
            model.addConstr((binary_trick[tour, 3, col, 2, 1] == 1) >> (state[tour, 2, 3, col, 2] + state[tour, 2, 3, col, 3] == 1)) 
            model.addConstr((binary_trick[tour, 3, col, 2, 2] == 1) >> (state[tour, 2, 2, col, 2] + state[tour, 2, 2, col, 3] == 1))   
            model.addConstr((binary_trick[tour, 3, col, 2, 3] == 1) >> (state[tour, 2, 2, col, 2] + state[tour, 2, 2, col, 3] + state[tour, 2, 3, col, 2] + state[tour, 2, 3, col, 3] == 1))         

            

    
    ## MITM part
    # BLUE PART
    for row in range(4):
        for col in range(4):
                #Starting constraint
                model.addConstr(blue_MITM_state[0, 0, row, col, 1] == 1)
    
    for round in range(MITM_round):
        for step in range (3):
            for row in range(4):
                for col in range(4):
                    #only blue or unknow
                    model.addConstr((gp.quicksum(blue_MITM_state[round, step, row, col, color] for color in [0, 1])) == 1)

    for round in range(MITM_round):
        for row in range(2):
            for col in range(4):
                #AK 
                model.addConstr((blue_MITM_state[round, 1, row, col, 0] == gp.or_([MITM_inter_key[round, 0, row, col, 0], blue_MITM_state[round, 0, row, col, 0]]))) #state after AK is unkown if previous state was or if key is red
        for row in range(2,4):
            for col in range(4):
                model.addConstr((blue_MITM_state[round, 0, row, col, 0] == 1) >> (blue_MITM_state[round, 1, row, col, 0] == 1))
                model.addConstr((blue_MITM_state[round, 0, row, col, 1] == 1) >> (blue_MITM_state[round, 1, row, col, 1] == 1))

                    
    #permutation
    for round in range(MITM_round):
        for col in range(4):
            for indice in range(2):
                model.addConstr((blue_MITM_state[round, 1, 0, col, indice] == 1) >> (blue_MITM_state[round, 2, 0, col, indice] == 1))
                model.addConstr((blue_MITM_state[round, 1, 1, col, indice] == 1) >> (blue_MITM_state[round, 2, 1, (col + 1) % 4, indice] == 1))
                model.addConstr((blue_MITM_state[round, 1, 2, col, indice] == 1) >> (blue_MITM_state[round, 2, 2,(col + 2) % 4, indice] == 1))
                model.addConstr((blue_MITM_state[round, 1, 3, col, indice] == 1) >> (blue_MITM_state[round, 2, 3, (col + 3) % 4, indice] == 1))
    
    #MC          
    for round in range (MITM_round-1):
        for col in range(4):
            model.addConstr(blue_MITM_state[round + 1, 0, 0, col, 0] == gp.or_(blue_MITM_state[round, 2, 0, col, 0], blue_MITM_state[round, 2, 2, col, 0], blue_MITM_state[round, 2, 3, col, 0]))
            model.addConstr(blue_MITM_state[round+1, 0, 1, col, 0] == blue_MITM_state[round, 2, 0, col, 0])
            model.addConstr(blue_MITM_state[round+1, 0, 2, col, 0] == gp.or_(blue_MITM_state[round, 2, 1, col, 0], blue_MITM_state[round, 2, 2, col, 0]))
            model.addConstr(blue_MITM_state[round+1, 0, 3, col, 0] == gp.or_(blue_MITM_state[round, 2, 0, col,0], blue_MITM_state[round, 2, 2, col, 0]))

    #RED part
    for row in range(4):
        for col in range(4):
            model.addConstr(red_MITM_state[MITM_round - 1, 2, row, col, 1] == 1)

    for round in range(MITM_round):
        for step in range (3):
            for row in range(4):
                for col in range(4):
                    #only blue or unknow
                    model.addConstr((gp.quicksum(red_MITM_state[round, step, row, col, color] for color in [0, 1])) == 1)
    
    #permutation
    for round in range(MITM_round):
        for col in range(4):
            for indice in range(2):
                model.addConstr((red_MITM_state[round, 2, 0, col, indice] == 1) >> (red_MITM_state[round, 1, 0, col, indice] == 1))
                model.addConstr((red_MITM_state[round, 2, 1, col, indice] == 1) >> (red_MITM_state[round, 1, 1, (col + 3) % 4, indice] == 1))
                model.addConstr((red_MITM_state[round, 2, 2, col, indice] == 1) >> (red_MITM_state[round, 1, 2, (col + 2) % 4, indice] == 1))
                model.addConstr((red_MITM_state[round, 2, 3, col, indice] == 1) >> (red_MITM_state[round, 1, 3, (col + 1) % 4, indice] == 1))

    for round in range(MITM_round):
            for row in range(2):
                for col in range(4):
                    #AK 
                    model.addConstr((red_MITM_state[round, 0, row, col, 0] == gp.or_([MITM_inter_key[round, 0, row, col, 1], red_MITM_state[round, 1, row, col, 0]]))) #state after AK is unkown if previous state was or if key is red
            for row in range(2, 4):
                for col in range(4):
                    model.addConstr((red_MITM_state[round, 1, row, col, 0] == 1) >> (red_MITM_state[round, 0, row, col, 0] == 1))
                    model.addConstr((red_MITM_state[round, 1, row, col, 1] == 1) >> (red_MITM_state[round, 0, row, col, 1] == 1))
    #MC          
    for round in range (MITM_round-1):
        for col in range(4):
            model.addConstr(red_MITM_state[round, 2, 0, col, 0] == red_MITM_state[round + 1, 0, 1, col, 0])
            model.addConstr(red_MITM_state[round, 2, 1, col, 0] == gp.or_(red_MITM_state[round + 1, 0, 1, col, 0], red_MITM_state[round + 1, 0, 2, col, 0], red_MITM_state[round + 1, 0, 3, col, 0]))
            model.addConstr(red_MITM_state[round, 2, 2, col, 0] == gp.or_(red_MITM_state[round + 1, 0, 1, col, 0], red_MITM_state[round + 1, 0, 3, col, 0]))
            model.addConstr(red_MITM_state[round, 2, 3, col, 0] == gp.or_(red_MITM_state[round + 1, 0, 0, col, 0], red_MITM_state[round + 1, 0, 3, col, 0]))
    #MITM match
    for round in range(MITM_round-1):
        for side in range(2):
            for col in range(4):
                model.addConstr(binary_match[round, 0, 0, col] == gp.and_([blue_MITM_state[round, 2, 0, col, 1], red_MITM_state[round + 1, 0, 1, col, 1]])) #list of matching nibbles
                model.addConstr(binary_match[round, 0, 1, col] == gp.and_([blue_MITM_state[round, 2, 1, col, 1], red_MITM_state[round + 1, 0, 1, col, 1], red_MITM_state[round + 1, 0, 2, col, 1],red_MITM_state[round + 1, 0, 3, col , 1], blue_MITM_state[round + 1, 0, 3, col, 1]]))
                model.addConstr(binary_match[round, 0,2,col] == gp.and_([blue_MITM_state[round, 2, 2, col, 1], red_MITM_state[round + 1, 0, 1, col, 1], red_MITM_state[round + 1, 0, 3, col, 1]]))
                model.addConstr(binary_match[round,0,3,col] == gp.and_([blue_MITM_state[round, 2, 3, col, 1], red_MITM_state[round + 1, 0, 0, col, 1], red_MITM_state[round + 1, 0, 3, col, 1]]))

                model.addConstr(binary_match[round, 1, 0, col] == gp.and_([red_MITM_state[round + 1, 0, 0, col, 1], blue_MITM_state[round, 2, 0, col, 1], blue_MITM_state[round, 2, 2, col, 1] ,blue_MITM_state[round, 2, 3, col, 1]])) #list of matching nibbles
                model.addConstr(binary_match[round, 1, 1, col] == gp.and_([red_MITM_state[round + 1, 0, 1, col, 1], blue_MITM_state[round, 2, 0, col, 1]]))
                model.addConstr(binary_match[round, 1, 2, col] == gp.and_([red_MITM_state[round + 1, 0, 2, col, 1], blue_MITM_state[round, 2, 1, col, 1], blue_MITM_state[round, 2, 2, col, 1]]))
                model.addConstr(binary_match[round, 1, 3, col] == gp.and_([red_MITM_state[round + 1, 0, 3, col, 1], blue_MITM_state[round, 2, 0, col, 1], blue_MITM_state[round, 2, 2, col, 1]]))

    model.addConstr(gp.quicksum(binary_match[round, side, row, col] for round in range(MITM_round - 1) for side in range(2) for row in range(4) for col in range(4))>= 1)

    model.optimize()

    #SI on a trouvé une solution on formate le résultat et on l'affiche avec la fonction d'affichage
    if model.Status == GRB.OPTIMAL:
        compteur_fix = 0
        liste_X = [np.zeros((4, 4)) for i in range(total_round)]
        liste_Y = [np.zeros((4, 4)) for i in range(total_round)]
        liste_Z = [np.zeros((4, 4)) for i in range(total_round)]
        for i in range(structure_round):
            for row in range(4):
                for col in range(4):
                    if state[i, 0, row, col, 0].X == 1.0:
                        liste_X[i][row, col] = 2
                    if state[i, 0, row, col, 1].X == 1.0:
                        liste_X[i][row, col] = 3
                    if state[i,0, row, col, 2].X == 1.0:
                        liste_X[i][row, col] = 5
                    if state[i, 0, row, col, 3].X == 1.0:
                        liste_X[i][row, col] = -1
                        compteur_fix += 1

                    if state[i, 1, row, col, 0].X == 1.0:
                        liste_Y[i][row, col] = 2
                    if state[i, 1, row, col, 1].X == 1.0:
                        liste_Y[i][row, col] = 3
                    if state[i, 1, row, col, 2].X == 1.0:
                        liste_Y[i][row, col] = 5
                    if state[i, 1, row, col, 3].X == 1.0:
                        liste_Y[i][row, col] = -1
                        compteur_fix += 1

                    if state[i, 2, row, col, 0].X == 1.0:
                        liste_Z[i][row, col] = 2
                    if state[i, 2, row, col, 1].X == 1.0:
                        liste_Z[i][row, col] = 3
                    if state[i, 2, row, col, 2].X == 1.0:
                        liste_Z[i][row, col] = 5
                    if state[i, 2, row, col, 3].X == 1.0:
                        liste_Z[i][row, col] = -1
                        compteur_fix += 1
                
        for i in range(MITM_round):
            for row in range(4):
                for col in range(4):
                    if blue_MITM_state[i, 0, row, col, 0].X == 1.0:
                        liste_X[structure_round + i][row, col] = 1
                    if blue_MITM_state[i, 0, row, col,1].X == 1.0:
                        liste_X[structure_round + i][row, col] = 3

                    if blue_MITM_state[i, 1, row, col, 0].X == 1.0:
                        liste_Y[structure_round + i][row, col] = 1
                    if blue_MITM_state[i, 1, row, col, 1].X == 1.0:
                        liste_Y[structure_round + i][row, col] = 3

                    if blue_MITM_state[i, 2, row, col, 0].X == 1.0:
                        liste_Z[structure_round + i][row, col] = 1
                    if blue_MITM_state[i,2, row, col, 1].X == 1.0:
                        liste_Z[structure_round + i][row, col] = 3

                    if red_MITM_state[i, 0, row, col, 1].X == 1.0:
                        liste_X[structure_round + i][row, col] = 2

                    if red_MITM_state[i, 1, row, col, 1].X == 1.0:
                        liste_Y[structure_round + i][row, col] = 2

                    if red_MITM_state[i, 2, row, col, 1].X == 1.0:
                        liste_Z[structure_round + i][row, col] = 2
                    
                    if red_MITM_state[i, 0, row, col, 1].X == 1.0 and blue_MITM_state[i, 0, row, col, 1].X == 1.0:
                        liste_X[structure_round + i][row, col] = 5
                    
                    if red_MITM_state[i, 1, row, col, 1].X == 1.0 and blue_MITM_state[i, 1, row, col, 1].X == 1.0:
                        liste_Y[structure_round + i][row, col] = 5

                    if red_MITM_state[i, 2, row, col, 1].X == 1.0 and blue_MITM_state[i, 2, row, col, 1].X == 1.0:
                        liste_Z[structure_round + i][row, col] = 5
                    
        key_M=np.zeros((total_round, 4, 4))
        for tour in range(structure_round):
            for row in range(4):
                for col in range(4):
                    if key[tour, row, col, 0].X == 1.0:
                        key_M[tour, row, col] = 2
                    if key[tour, row, col, 1].X == 1.0:
                        key_M[tour, row, col] = 3
                    if key[tour, row, col, 2].X == 1.0:
                        key_M[tour, row, col] = 5
        for tour in range(MITM_round):
            for row in range(4):
                for col in range(4):
                    if MITM_inter_key[tour, 0, row, col, 0].X == 1.0:
                        key_M[tour + structure_round, row, col] = 2
                    if MITM_inter_key[tour, 0, row, col, 1].X == 1.0:
                        key_M[tour + structure_round, row, col] = 3
                    if MITM_inter_key[tour, 0, row, col, 2].X == 1.0:
                        key_M[tour + structure_round, row, col] = 5

        key_0 = np.zeros((total_round, 4, 4))
        for tour in range(total_round):
            for row in range(4):
                for col in range(4):
                    if inter_key[tour, 0, row, col, 0].X == 1.0:
                        key_0[tour, row, col] = 2
                    if inter_key[tour, 0, row, col, 1].X == 1.0:
                        key_0[tour, row, col] = 3
                    if inter_key[tour, 0, row, col, 2].X == 1.0:
                        key_0[tour, row, col] = 5
        key_1=np.zeros((total_round, 4, 4))
        if key_space_size >= 2:
            for tour in range(total_round):
                for row in range(4):
                    for col in range(4):
                        if inter_key[tour, 1, row, col, 0].X == 1.0:
                            key_1[tour, row, col] = 2
                        if inter_key[tour, 1, row, col, 1].X == 1.0:
                            key_1[tour, row, col] = 3
                        if inter_key[tour, 1, row, col, 2].X == 1.0:
                            key_1[tour, row, col] = 5
        key_2=np.zeros((total_round, 4, 4))
        if key_space_size == 3:
            for tour in range(total_round):
                for row in range(4):
                    for col in range(4):
                        if inter_key[tour, 2, row, col, 0].X == 1.0:
                            key_2[tour, row, col] = 2
                        if inter_key[tour, 2, row, col, 1].X == 1.0:
                            key_2[tour, row, col] = 3
                        if inter_key[tour, 2, row, col, 2].X == 1.0:
                            key_2[tour, row, col] = 5 

        affichage_grille(key_M, key_0, key_1, key_2, liste_X, liste_Y, liste_Z)
    else :
        print("UNFAISABLE")




    
