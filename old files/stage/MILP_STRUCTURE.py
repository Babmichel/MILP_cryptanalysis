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

def affichage_grille(key, key0, key1, key2, x_list, y_list, z_list):
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
    list_key0 = key0
    list_key1 = key1
    list_key2 = key2

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
"WLSACCESSID" : "bb41a17b-b3b2-40d7-8c1c-01d90a2e2170",
"WLSSECRET" : "4db1c96a-1e47-4fc9-83eb-28a57d08879f",
"LICENSEID" : 2534357
}

with gp.Env(params=options) as env, gp.Model(env=env) as model:
    print(("Structure sur 6 tours, avec deux clés bleus et une clés rouge"))
    
    nombre_tour = 6
    nombre_tour_total = 6
    nombre_tour_MITM = nombre_tour_total - nombre_tour
    size_key_space = 3

    key_index_2 = np.array([[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,14,15]])
    key_matrix=np.zeros((nombre_tour_total,4,4))
    for index in range(nombre_tour_total):
        key_matrix[index,:,:] = key_index_2
        key_index_2 = tweakey(key_index_2)
    key_index = np.array([[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,14,15]])

    state = np.zeros((nombre_tour_total, 3, 4, 4, 4), dtype=object)

    inter_key = np.zeros((nombre_tour_total,size_key_space, 4, 4, 3), dtype=object)
    key = np.zeros((nombre_tour_total, 4, 4, 3), dtype=object)

    red_key_knowledge = np.zeros((4,4), dtype=object)
    blue_key_knowledge = np.zeros((4,4), dtype=object)


    red_binary_bound = np.zeros((4,4,2), dtype= object)
    blue_binary_bound = np.zeros((4,4,2), dtype= object)


    #DECISION VARIABLES
    for tour in range(nombre_tour_total):
        for index in range(3):
            for row in range(4):
                for col in range(4):
                    for indice in range(4):
                        state[tour, index, row, col, indice] = model.addVar(vtype=GRB.BINARY, name=f'state_tour :{tour} etape :{index} ligne :{row} colonne :{col} couleur :{indice}')
    

    for tour in range(nombre_tour_total):
        for index in range(size_key_space):
            for row in range(4):
                for col in range(4):
                    for indice in range(3):
                        inter_key[tour, index, row, col, indice] = model.addVar(vtype=GRB.BINARY, name=f'key_inter :{tour} etape :{index} ligne :{row} colonne :{col} couleur :{indice}')

    for tour in range(nombre_tour_total):
        for row in range(4):
            for col in range(4):
                for indice in range(3):
                    key[tour, row, col, indice] = model.addVar(vtype=GRB.BINARY, name=f'key_tour:{tour}_ligne:{row}_colonne:{col}_couleur:{indice}')
    
    for row in range(4):
        for col in range(4):
            red_key_knowledge[row, col] = model.addVar(vtype=GRB.INTEGER, name=f'red_keyknowledge{row} {col}')
            blue_key_knowledge[row, col] = model.addVar(vtype=GRB.INTEGER, name=f'red_keyknowledge{row} {col}')
    

    for row in range(4):
        for col in range(4):
            red_binary_bound[row,col,0] = model.addVar(vtype=GRB.BINARY, name=f'binary_bound0{index}{row}{col}')
            red_binary_bound[row,col,1] = model.addVar(vtype=GRB.BINARY, name=f'binary_bound1{index}{row}{col}')
            blue_binary_bound[row,col,0] = model.addVar(vtype=GRB.BINARY, name=f'binary_bound0{index}{row}{col}')
            blue_binary_bound[row,col,1] = model.addVar(vtype=GRB.BINARY, name=f'binary_bound1{index}{row}{col}')
    

    nombre_rouge_0=gp.quicksum(inter_key[tour,0,row,col,0] for tour in range(nombre_tour_total) for row in range(4) for col in range(4))
    nombre_bleu_0=gp.quicksum(inter_key[tour,0,row,col,1] for tour in range(nombre_tour_total) for row in range(4) for col in range(4))
    if size_key_space >=2 :
        nombre_rouge_1=gp.quicksum(inter_key[tour,1,row,col,0] for tour in range(nombre_tour_total) for row in range(4) for col in range(4))
        nombre_bleu_1=gp.quicksum(inter_key[tour,1,row,col,1] for tour in range(nombre_tour_total) for row in range(4) for col in range(4))
    else :
        nombre_rouge_1 = 0
        nombre_bleu_1 = 0
    if size_key_space >=3 :
        nombre_rouge_2=gp.quicksum(inter_key[tour,2,row,col,0] for tour in range(nombre_tour_total) for row in range(4) for col in range(4))
        nombre_bleu_2=gp.quicksum(inter_key[tour,2,row,col,1] for tour in range(nombre_tour_total) for row in range(4) for col in range(4))
    else :
        nombre_rouge_2 = 0
        nombre_bleu_2 = 0

    model.update()

    
    #OBJECTIVE FUNCTION
    nombre_fixe = gp.quicksum(state[tour, index, row, col ,3] for tour in range(nombre_tour) for index in range(3) for row in range(4) for col in range(4)) # operating cost
    objective = red_key_knowledge.sum() + blue_key_knowledge.sum()
    model.setObjective(objective, sense=GRB.MINIMIZE)


    #CONSTRAINTS 

    #key constraints
    model.addConstr(gp.quicksum(state[tour, index, row, col ,3] for tour in range(nombre_tour) for index in range(3) for row in range(4) for col in range(4)) <= 16)
    #Initial key
    #les sous clé ne peuvent pas connaitre toute la clé
    for tour in range(nombre_tour_total):
        model.addConstr(gp.quicksum(inter_key[tour,0,row,col,0]for row in range(4) for col in range(4)) >= 1)
        model.addConstr(gp.quicksum(inter_key[tour,0,row,col,1]for row in range(4) for col in range(4)) >= 1)
        if size_key_space >=2:
            model.addConstr(gp.quicksum(inter_key[tour,1,row,col,0]for row in range(4) for col in range(4)) >= 1)
            model.addConstr(gp.quicksum(inter_key[tour,1,row,col,1]for row in range(4) for col in range(4)) >= 1)
        if size_key_space >= 3:
            model.addConstr(gp.quicksum(inter_key[tour,2,row,col,0]for row in range(4) for col in range(4)) >= 1)
            model.addConstr(gp.quicksum(inter_key[tour,2,row,col,1]for row in range(4) for col in range(4)) >= 1)

    #les sous clés sont soit bleu soit rouge soit violette
    for tour in range(nombre_tour_total):
        for index in range(size_key_space):
            for row in range(4):
                for col in range(4):
                    model.addConstr((gp.quicksum(inter_key[tour,index,row,col,i] for i in range(3)) == 1))
    
    #key schedule
    for row in range(4):
        for col in range(4):
            red_key_knowledge[row,col] = gp.quicksum(inter_key[tour,index,np.where(key_matrix[tour] == key_index[row,col])[0][0], np.where(key_matrix[tour] == key_index[row,col])[1][0],i] for tour in range(nombre_tour_total) for index in range(size_key_space) for i in [0,2] )
            blue_key_knowledge[row,col] = gp.quicksum(inter_key[tour,index,np.where(key_matrix[tour] == key_index[row,col])[0][0], np.where(key_matrix[tour] == key_index[row,col])[1][0],i] for tour in range(nombre_tour_total) for index in range(size_key_space) for i in [1,2] )

    for row in range(4):
        for col in range(4):
            model.addConstr(red_binary_bound[row, col, 0] + red_binary_bound[row, col, 1] == 1)
            model.addGenConstrIndicator(red_binary_bound[row, col, 0], True, red_key_knowledge[row,col], gp.GRB.GREATER_EQUAL, 3*nombre_tour_total) 
            model.addGenConstrIndicator(red_binary_bound[row, col, 1], True, red_key_knowledge[row,col], gp.GRB.LESS_EQUAL, 2)

    for row in range(4):
        for col in range(4):
            model.addConstr(blue_binary_bound[row, col, 0] + blue_binary_bound[row, col, 1] == 1)
            model.addGenConstrIndicator(blue_binary_bound[row, col, 0], True, blue_key_knowledge[row,col], gp.GRB.GREATER_EQUAL, 3*nombre_tour_total) 
            model.addGenConstrIndicator(blue_binary_bound[row, col, 1], True, blue_key_knowledge[row,col], gp.GRB.LESS_EQUAL, 2)

    #Si un mot des clés intermédiaire est bleu ou rouge la clé est donc bleu ou rouge
    for tour in range(nombre_tour_total) :
        for index in range(size_key_space):
            for row in range(4):
                for col in range(4):
                    model.addConstr((inter_key[tour,index,row,col,0]==1) >> (key[tour,row,col,0]==1))
                    model.addConstr((inter_key[tour,index,row,col,0]==1) >> (key[tour,row,col,1]==0))
                    model.addConstr((inter_key[tour,index,row,col,0]==1) >> (key[tour,row,col,2]==0))
                    model.addConstr((inter_key[tour,index,row,col,1]==1) >> (key[tour,row,col,1]==1))
                    model.addConstr((inter_key[tour,index,row,col,1]==1) >> (key[tour,row,col,0]==0))
                    model.addConstr((inter_key[tour,index,row,col,1]==1) >> (key[tour,row,col,2]==0))
    
    #si les trois mots sont violets la clé est violette
    for tour in range(nombre_tour_total):
        for row in range(4):
            for col in range(4):
                model.addConstr(key[tour,row,col,2] == gp.and_([inter_key[tour,index,row,col,2] for index in range(size_key_space)]))

    #les mots de clé sont forcéments bleu rouge ou violet
    for tour in range(nombre_tour_total):
        for row in range(4):
            for col in range(4):
                model.addConstr((key[tour,row,col,0] == 1) >> (key[tour,row,col,1] == 0))
                model.addConstr((key[tour,row,col,0] == 1) >> (key[tour,row,col,2] == 0))
                model.addConstr((key[tour,row,col,1] == 1) >> (key[tour,row,col,0] == 0))
                model.addConstr((key[tour,row,col,1] == 1) >> (key[tour,row,col,2] == 0))
                model.addConstr((key[tour,row,col,2] == 1) >> (key[tour,row,col,0] == 0))
                model.addConstr((key[tour,row,col,2] == 1) >> (key[tour,row,col,1] == 0))
                model.addConstr((gp.quicksum(key[tour,row,col,i] for i in range(3)) == 1))


    #Starting constraint
    for row in range(4):
        for col in range(4):
            model.addConstr(state[0,0,row,col,1] == 0) #premier état sans mot connu que de bleu
            model.addConstr(state[0,0,row,col,2] == 0) #premier état sans mot violet(que fixe autorisés)
            model.addConstr(state[nombre_tour-1,2,row,col,0] == 0) # dernier état sans mot connu que de rouge 

    #state constraint : un état ne peux être que bleu rouge violet ou fixe 
    for tour in range(nombre_tour):
        for index in range(3):
            for row in range(4):
                for col in range(4):
                    model.addConstr((gp.quicksum(state[tour,index,row,col,i] for i in range(4)) == 1))

    #contraintes de la clé sur l'état
    for tour in range(nombre_tour):
        for row in range(2):
            for col in range(4):
                model.addConstr((key[tour, row, col, 0] == 1) >> (state[tour, 0, row, col, 1] == 0)) #si clé rouge on ne peut avoir état bleu
                model.addConstr((key[tour, row, col, 1] == 1) >> (state[tour, 0, row, col, 0] == 0)) #si clé bleu on ne peut avoir état rouge

                model.addConstr((state[tour,1,row,col,0] == 1) >>  (key[tour,row,col,1] == 0)) #etat droite rouge, clé ne peut être bleu
                model.addConstr((state[tour,1,row,col,0] == 1) >>  (state[tour,0,row,col,1] == 0)) #etat droite rouge, état gauche ne peut être bleu

                model.addConstr((state[tour,1,row,col,1] == 1) >>  (key[tour,row,col,0] == 0)) #etat droite bleu, clé ne peut être rouge
                model.addConstr((state[tour,1,row,col,1] == 1) >>  (state[tour,0,row,col,0] == 0)) #etat droite bleu, état gauche ne peut être rouge

                model.addConstr((state[tour,1,row,col,2] == 1) >>  (key[tour,row,col,0] == 0)) #etat droite violet, clé ne peut être rouge
                model.addConstr((state[tour,1,row,col,2] == 1) >>  (state[tour,0,row,col,0] == 0)) #etat droite violet, état gauche ne peut être rouge

                model.addConstr((state[tour,1,row,col,2] == 1) >>  (key[tour,row,col,1] == 0)) #etat droite violet, clé ne peut être rouge
                model.addConstr((state[tour,1,row,col,2] == 1) >>  (state[tour,0,row,col,1] == 0)) #etat droite rouge, état gauche ne peut être rouge 

                model.addConstr((key[tour, row, col, 1] == 1) >> (state[tour, 1, row, col, 1] == 1)) # blue key -> next state is blue
                model.addConstr((key[tour, row, col, 0] == 1) >> (state[tour, 0, row, col, 0] == 1)) #red key -> previous state is red

                model.addConstr(state[tour,1, row, col, 1] == gp.or_(state[tour,0,row,col,1],key[tour,row,col,1])) #Bleu a droite que si on au moins un bleu dans la clé ou l'état d'avant
                model.addConstr(state[tour,0, row, col, 0] == gp.or_(state[tour,1,row,col,0],key[tour,row,col,0])) #Rouge a gauche que si on a un rouge dans la clé ou a droite

        for row in range(2,4): #Partie inférieur de la clé ne modifie pas (sauf fixe qui devient violet)
            for col in range(4):
                model.addConstr((state[tour,0, row, col, 0] == 1) >> (state[tour,1, row, col, 0] == 1))
                model.addConstr((state[tour,0, row, col, 1] == 1) >> (state[tour,1, row, col, 1] == 1))
                model.addConstr((state[tour,0, row, col, 2] == 1) >> (state[tour,1, row, col, 2] == 1))
                model.addConstr((state[tour,0, row, col, 3] == 1) >> (state[tour,1, row, col, 2] == 1))

    #Contrainte de la permutation :
    for tour in range(nombre_tour_total):
            for col in range(4):
                for indice in range(3):
                    model.addConstr((state[tour,1,0,col,indice] == 1) >> (state[tour,2,0,col,indice] == 1))
                    model.addConstr((state[tour,1,1,col,indice] == 1) >> (state[tour,2,1,(col+1)%4,indice] == 1))
                    model.addConstr((state[tour,1,2,col,indice] == 1) >> (state[tour,2,2,(col+2)%4,indice] == 1))
                    model.addConstr((state[tour,1,3,col,indice] == 1) >> (state[tour,2,3,(col+3)%4,indice] == 1))
                model.addConstr((state[tour,1,0,col,3] == 1) >> (state[tour,2,0,col,2] == 1))
                model.addConstr((state[tour,1,1,col,3] == 1) >> (state[tour,2,1,(col+1)%4,2] == 1))
                model.addConstr((state[tour,1,2,col,3] == 1) >> (state[tour,2,2,(col+2)%4,2] == 1))
                model.addConstr((state[tour,1,3,col,3] == 1) >> (state[tour,2,3,(col+3)%4,2] == 1))

    #Contrainte du MC :
    for tour in range(nombre_tour-1):
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
            #si on a un mot rouge à droite sur la premiére ligne 
            # on ne peux pas avoir un état tout violet, fix compris
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((state[tour+1, 0, 0, col, 0] == 1) >> (state[tour, 2, 0, col, 2+i] + state[tour, 2, 2, col, 2+j] + state[tour, 2, 3, col, 2+k] <= 2))
            #on ne peux pas avoir de bleu dans l'état précédent
            model.addConstr((state[tour+1, 0, 0, col, 0] == 1) >> (state[tour,2,0,col,1] == 0))
            model.addConstr((state[tour+1, 0, 0, col, 0] == 1) >> (state[tour,2,2,col,1] == 0))
            model.addConstr((state[tour+1, 0, 0, col, 0] == 1) >> (state[tour,2,3,col,1] == 0))

            #idem en bleu, on ne peux avoir que des violets ou fix avant 
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((state[tour+1, 0, 0, col, 1] == 1) >> (state[tour, 2, 0, col, 2+i] + state[tour, 2, 2, col, 2+j] + state[tour, 2, 3, col, 2+k] <= 2))
            #on ne peux pas avoir de rouge dans l'état précédent
            model.addConstr((state[tour+1, 0, 0, col, 1] == 1) >> (state[tour,2,0,col,0] == 0))
            model.addConstr((state[tour+1, 0, 0, col, 1] == 1) >> (state[tour,2,2,col,0] == 0))
            model.addConstr((state[tour+1, 0, 0, col, 1] == 1) >> (state[tour,2,3,col,0] == 0))

            #si on a un mot violet on ne peux avoir que des mots violet avant (pas de rouge ou bleus)
            model.addConstr((state[tour+1, 0, 0, col, 2] == 1) >> (state[tour, 2, 0, col, 0] == 0))
            model.addConstr((state[tour+1, 0, 0, col, 2] == 1) >> (state[tour, 2, 2, col, 0] == 0))
            model.addConstr((state[tour+1, 0, 0, col, 2] == 1) >> (state[tour, 2, 3, col, 0] == 0))

            model.addConstr((state[tour+1, 0, 0, col, 2] == 1) >> (state[tour, 2, 0, col, 1] == 0))
            model.addConstr((state[tour+1, 0, 0, col, 2] == 1) >> (state[tour, 2, 2, col, 1] == 0))
            model.addConstr((state[tour+1, 0, 0, col, 2] == 1) >> (state[tour, 2, 3, col, 1] == 0))

            #DEUXIEME ligne
            #plus simple car une seul valeur
            #si on a une couleur a droite on doit avoir la meme a gauche
            for indice in range(3):
                model.addConstr((state[tour, 2, 0, col, indice] == 1) >> (state[tour+1, 0, 1, col, indice] == 1))
            #si on a un fixe a gauche il faut un violet a droite par propagation direct
            model.addConstr((state[tour, 2, 0, col, 3] == 1) >> (state[tour+1, 0, 1, col, 2] == 1))
        
            #TROISIEME LIGNE
            #si on a un rouge
            #on ne peux pas avoir que des violets/Fix
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((state[tour+1, 0, 2, col, 0] == 1) >> (state[tour, 2, 1, col, 2+i] + state[tour, 2, 2, col, 2+j] <= 1))
            #on ne peux pas avoir de bleu dans l'état précédent
            model.addConstr((state[tour+1, 0, 2, col, 0] == 1) >> (state[tour,2,1,col,1] == 0))
            model.addConstr((state[tour+1, 0, 2, col, 0] == 1) >> (state[tour,2,2,col,1] == 0))

            #si on a un bleu 
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((state[tour+1, 0, 2, col, 1] == 1) >> (state[tour, 2, 1, col, 2+i] + state[tour, 2, 2, col, 2+j] <= 1))
            #on ne peux pas avoir de rouges dans l'état précédent
            model.addConstr((state[tour+1, 0, 2, col, 1] == 1) >> (state[tour,2,1,col,0] == 0))
            model.addConstr((state[tour+1, 0, 2, col, 1] == 1) >> (state[tour,2,2,col,0] == 0))

            #si on a un violet, les états précédents concernés ne peuvent être bleu ou rouge
            model.addConstr((state[tour+1, 0, 2, col, 2] == 1) >> (state[tour, 2, 1, col, 0] == 0))
            model.addConstr((state[tour+1, 0, 2, col, 2] == 1) >> (state[tour, 2, 2, col, 0] == 0))

            model.addConstr((state[tour+1, 0, 2, col, 2] == 1) >> (state[tour, 2, 1, col, 1] == 0))
            model.addConstr((state[tour+1, 0, 2, col, 2] == 1) >> (state[tour, 2, 2, col, 1] == 0))

            #QUATRIEME LIGNE
            #si on a un rouge
            #on ne peux pas avoir que des violets/Fix
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((state[tour+1, 0, 3, col, 0] == 1) >> (state[tour, 2, 0, col, 2+i] + state[tour, 2, 2, col, 2+j] <= 1))
            #on ne peux pas avoir de bleus dans l'état précédent 
            model.addConstr((state[tour+1, 0, 3, col, 0] == 1) >> (state[tour,2,0,col,1] == 0))
            model.addConstr((state[tour+1, 0, 3, col, 0] == 1) >> (state[tour,2,2,col,1] == 0))

            #si on a un bleu
            #on ne peux pas avoir que des violets/Fix
            for i in range(2):
                for j in range(2):
                    for k in range(2): 
                        model.addConstr((state[tour+1, 0, 3, col, 1] == 1) >> (state[tour, 2, 0, col, 2+i] + state[tour, 2, 2, col, 2+j] <= 1))
            #on ne peux pas avoir de bleus dans l'état précédent 
            model.addConstr((state[tour+1, 0, 3, col, 1] == 1) >> (state[tour,2,0,col,0] == 0))
            model.addConstr((state[tour+1, 0, 3, col, 1] == 1) >> (state[tour,2,2,col,0] == 0))

            #si on a un violet, les états précédents concernés ne peuvent être bleu ou rouge
            model.addConstr((state[tour+1, 0, 3, col, 2] == 1) >> (state[tour, 2, 0, col, 0] == 0))
            model.addConstr((state[tour+1, 0, 3, col, 2] == 1) >> (state[tour, 2, 2, col, 0] == 0))

            model.addConstr((state[tour+1, 0, 3, col, 2] == 1) >> (state[tour, 2, 0, col, 1] == 0))
            model.addConstr((state[tour+1, 0, 3, col, 2] == 1) >> (state[tour, 2, 2, col, 1] == 0))

    
    #propagation arriere
    """
    for tour in range(nombre_tour+1,nombre_tour_total):
            for col in range(4):
                for indice in range(3):
                    model.addConstr((state[tour,2,0,col,indice] == 1) >> (state[tour,1,0,col,indice] == 1))
                    model.addConstr((state[tour,2,1,col,indice] == 1) >> (state[tour,1,1,(col+3)%4,indice] == 1))
                    model.addConstr((state[tour,2,2,col,indice] == 1) >> (state[tour,1,2,(col+2)%4,indice] == 1))
                    model.addConstr((state[tour,2,3,col,indice] == 1) >> (state[tour,1,3,(col+1)%4,indice] == 1))
    """       
    #model.computeIIS() 
    model.optimize()
    
    #SI on a trouvé une solution on formate le résultat et on l'affiche avec la fonction d'affichage
    if model.Status == GRB.OPTIMAL:
        compteur_fix=0
        liste_X=[np.zeros((4,4)) for i in range(nombre_tour_total)]
        liste_Y=[np.zeros((4,4)) for i in range(nombre_tour_total)]
        liste_Z=[np.zeros((4,4)) for i in range(nombre_tour_total)]
        for i in range(nombre_tour):
            for row in range(4):
                for col in range(4):
                    if state[i,0,row,col,0].X==1.0:
                        liste_X[i][row,col] = 2
                    if state[i,0,row,col,1].X==1.0:
                        liste_X[i][row,col] = 3
                    if state[i,0,row,col,2].X==1.0:
                        liste_X[i][row,col] = 5
                    if state[i,0,row,col,3].X==1.0:
                        liste_X[i][row,col] = -1
                        compteur_fix += 1
            for row in range(4):
                for col in range(4):
                    if state[i,1,row,col,0].X==1.0:
                        liste_Y[i][row,col] = 2
                    if state[i,1,row,col,1].X==1.0:
                        liste_Y[i][row,col] = 3
                    if state[i,1,row,col,2].X==1.0:
                        liste_Y[i][row,col] = 5
                    if state[i,1,row,col,3].X==1.0:
                        liste_Y[i][row,col] = -1
                        compteur_fix += 1
            for row in range(4):
                for col in range(4):
                    if state[i,2,row,col,0].X==1.0:
                        liste_Z[i][row,col] = 2
                    if state[i,2,row,col,1].X==1.0:
                        liste_Z[i][row,col] = 3
                    if state[i,2,row,col,2].X==1.0:
                        liste_Z[i][row,col] = 5
                    if state[i,2,row,col,3].X==1.0:
                        liste_Z[i][row,col] = -1
                        compteur_fix += 1
        for i in range(nombre_tour,nombre_tour_total):
                for row in range(4):
                    for col in range(4):
                        if state[i,0,row,col,0].X==1.0:
                            liste_X[i][row,col] = 2
                        if state[i,0,row,col,1].X==1.0:
                            liste_X[i][row,col] = 3
                        if state[i,0,row,col,2].X==1.0:
                            liste_X[i][row,col] = 1
                        if state[i,0,row,col,3].X==1.0:
                            liste_X[i][row,col] = -1
                            compteur_fix += 1
                for row in range(4):
                    for col in range(4):
                        if state[i,1,row,col,0].X==1.0:
                            liste_Y[i][row,col] = 2
                        if state[i,1,row,col,1].X==1.0:
                            liste_Y[i][row,col] = 3
                        if state[i,1,row,col,2].X==1.0:
                            liste_Y[i][row,col] = 1
                        if state[i,1,row,col,3].X==1.0:
                            liste_Y[i][row,col] = -1
                            compteur_fix += 1
                for row in range(4):
                    for col in range(4):
                        if state[i,2,row,col,0].X==1.0:
                            liste_Z[i][row,col] = 2
                        if state[i,2,row,col,1].X==1.0:
                            liste_Z[i][row,col] = 3
                        if state[i,2,row,col,2].X==1.0:
                            liste_Z[i][row,col] = 1
                        if state[i,2,row,col,3].X==1.0:
                            liste_Z[i][row,col] = -1
                            compteur_fix += 1
        
        key_M=np.zeros((nombre_tour_total,4,4))
        for tour in range(nombre_tour_total):
            for row in range(4):
                for col in range(4):
                    if key[tour,row,col,0].X==1.0:
                        key_M[tour,row,col]=2
                    if key[tour,row,col,1].X==1.0:
                        key_M[tour,row,col]=3
                    if key[tour,row,col,2].X==1.0:
                        key_M[tour,row,col]=5

        key_0=np.zeros((nombre_tour_total,4,4))
        for tour in range(nombre_tour_total):
            for row in range(4):
                for col in range(4):
                    if inter_key[tour,0,row,col,0].X==1.0:
                        key_0[tour,row,col]=2
                    if inter_key[tour,0,row,col,1].X==1.0:
                        key_0[tour,row,col]=3
                    if inter_key[tour,0,row,col,2].X==1.0:
                        key_0[tour,row,col]=5
        key_1=np.zeros((nombre_tour_total,4,4))
        if size_key_space >= 2:
            for tour in range(nombre_tour_total):
                for row in range(4):
                    for col in range(4):
                        if inter_key[tour,1,row,col,0].X==1.0:
                            key_1[tour,row,col]=2
                        if inter_key[tour,1,row,col,1].X==1.0:
                            key_1[tour,row,col]=3
                        if inter_key[tour,1,row,col,2].X==1.0:
                            key_1[tour,row,col]=5
        key_2=np.zeros((nombre_tour_total,4,4))
        if size_key_space == 3:
            for tour in range(nombre_tour_total):
                for row in range(4):
                    for col in range(4):
                        if inter_key[tour,2,row,col,0].X==1.0:
                            key_2[tour,row,col]=2
                        if inter_key[tour,2,row,col,1].X==1.0:
                            key_2[tour,row,col]=3
                        if inter_key[tour,2,row,col,2].X==1.0:
                            key_2[tour,row,col]=5

        affichage_grille(key_M,key_0,key_1,key_2,liste_X,liste_Y,liste_Z)
    else :
        print("UNFAISABLE")

    

    