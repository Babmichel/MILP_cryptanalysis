#MILPTEST
import gurobipy as gp
from gurobipy import GRB
import itertools
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

def affichage_grille(key, x_list, y_list, z_list):
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
    list_key = []
    for _ in range(len(x_list)):
        list_key.append(key)
        key = tweakey(key)
    for i in range(len(x_list)):
        print("TOUR", i)
        print("  _ _X_ _    _ _Y_ _    _ _Z_ _      _K_E_Y_ ")
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
                elif list_key[i][ligne, colonne] == 7:
                    print("\033[93m ■", end="")
                elif list_key[i][ligne, colonne] == 11:
                    print("\033[96m ■", end="")
                else:
                    print("\033[90m ■", end="")
            print("\033[90m|")
        print("  ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾      ‾ ‾ ‾ ‾ \n \n")

def structure(nombre_tour, imported_key):
    options = {
        "WLSACCESSID" : "bb41a17b-b3b2-40d7-8c1c-01d90a2e2170",
        "WLSSECRET" : "4db1c96a-1e47-4fc9-83eb-28a57d08879f",
        "LICENSEID" : 2534357
    }

    with gp.Env(params=options) as env, gp.Model(env=env) as model:
        print(("Structure sur 6 tours, avec deux clés bleus et une clés rouge"))

        state = np.zeros((nombre_tour, 3, 4, 4, 4), dtype=object)
        key = np.zeros((nombre_tour, 4, 4, 3), dtype=object)

        #DECISION VARIABLES
        for tour in range(nombre_tour):
            for index in range(3):
                for row in range(4):
                    for col in range(4):
                        for indice in range(4):
                            state[tour, index, row, col, indice] = model.addVar(vtype=GRB.BINARY, name=f'state_tour :{tour} etape :{index} ligne :{row} colonne :{col} couleur :{indice}')

        for tour in range(nombre_tour):
            for row in range(4):
                for col in range(4):
                    for indice in range(3):
                        key[tour, row, col, indice] = model.addVar(vtype=GRB.BINARY, name=f'key_tour:{tour}_ligne:{row}_colonne:{col}_couleur:{indice}')

        model.update()

        #OBJECTIVE FUNCTION
        objective = gp.quicksum(state[tour, index, row, col ,3] for tour in range(nombre_tour) for index in range(3) for row in range(4) for col in range(4)) # operating cost
        model.setObjective(objective, sense=GRB.MINIMIZE)

        #CONSTRAINTS 

        #key constraints

        #Initial key
        
        model.addConstr(key[0, 0, 0, imported_key[0,0]] == 1)
        model.addConstr(key[0, 0, 1, imported_key[0,1]] == 1)
        model.addConstr(key[0, 0, 2, imported_key[0,2]] == 1)
        model.addConstr(key[0, 0, 3, imported_key[0,3]] == 1)

        model.addConstr(key[0, 1, 0, imported_key[1,0]] == 1)
        model.addConstr(key[0, 1, 1, imported_key[1,1]] == 1)
        model.addConstr(key[0, 1, 2, imported_key[1,2]] == 1)
        model.addConstr(key[0, 1, 3, imported_key[1,3]] == 1) 

        model.addConstr(key[0, 2, 0, imported_key[2,0]] == 1) 
        model.addConstr(key[0, 2, 1, imported_key[2,1]] == 1)
        model.addConstr(key[0, 2, 2, imported_key[2,2]] == 1)
        model.addConstr(key[0, 2, 3, imported_key[2,3]] == 1) 

        model.addConstr(key[0, 3, 0, imported_key[3,0]] == 1)
        model.addConstr(key[0, 3, 1, imported_key[3,1]] == 1) 
        model.addConstr(key[0, 3, 2, imported_key[3,2]] == 1) 
        model.addConstr(key[0, 3, 3, imported_key[3,3]] == 1) 

        #Generate all the key 
        for tour in range(0,nombre_tour-1):
            for row in range(4):
                for col in range(4):
                    for i in range(3):
                        model.addConstr(key[tour+1, 0, 0, i] == key[tour, 2, 1, i]) 
                        model.addConstr(key[tour+1, 0, 1, i] == key[tour, 3, 3, i]) 
                        model.addConstr(key[tour+1, 0, 2, i] == key[tour, 2, 0, i]) 
                        model.addConstr(key[tour+1, 0, 3, i] == key[tour, 3, 1, i]) 
                        model.addConstr(key[tour+1, 1, 0, i] == key[tour, 2, 2, i]) 
                        model.addConstr(key[tour+1, 1, 1, i] == key[tour, 3, 2, i]) 
                        model.addConstr(key[tour+1, 1, 2, i] == key[tour, 3, 0, i]) 
                        model.addConstr(key[tour+1, 1, 3, i] == key[tour, 2, 3, i]) 
                        model.addConstr(key[tour+1, 2, 0, i] == key[tour, 0, 0, i]) 
                        model.addConstr(key[tour+1, 2, 1, i] == key[tour, 0, 1, i]) 
                        model.addConstr(key[tour+1, 2, 2, i] == key[tour, 0, 2, i]) 
                        model.addConstr(key[tour+1, 2, 3, i] == key[tour, 0, 3, i]) 
                        model.addConstr(key[tour+1, 3, 0, i] == key[tour, 1, 0, i]) 
                        model.addConstr(key[tour+1, 3, 1, i] == key[tour, 1, 1, i]) 
                        model.addConstr(key[tour+1, 3, 2, i] == key[tour, 1, 2, i]) 
                        model.addConstr(key[tour+1, 3, 3, i] == key[tour, 1, 3, i]) 

        #Starting constraint
        for row in range(4):
            for col in range(4):
                model.addConstr(state[0,0,row,col,1] == 0) #premier état sans mot connu que de bleu
                model.addConstr(state[0,0,row,col,2] == 0) #premier état sans mot violet 
                model.addConstr(state[nombre_tour-1,2,row,col,0] == 0) # dernier état sans mot connu que de rouge 
        
        #state constraint : un état ne peux être que bleu rouge violet ou fixe 
        for tour in range(nombre_tour):
            for index in range(3):
                for row in range(4):
                    for col in range(4):
                        model.addConstr((state[tour,index,row,col,0] == 1) >> (state[tour,index,row,col,1] == 0))
                        model.addConstr((state[tour,index,row,col,0] == 1) >> (state[tour,index,row,col,2] == 0))
                        model.addConstr((state[tour,index,row,col,0] == 1) >> (state[tour,index,row,col,3] == 0))
                        
                        model.addConstr((state[tour,index,row,col,1] == 1) >> (state[tour,index,row,col,0] == 0))
                        model.addConstr((state[tour,index,row,col,1] == 1) >> (state[tour,index,row,col,2] == 0))
                        model.addConstr((state[tour,index,row,col,1] == 1) >> (state[tour,index,row,col,3] == 0))

                        model.addConstr((state[tour,index,row,col,2] == 1) >> (state[tour,index,row,col,1] == 0))
                        model.addConstr((state[tour,index,row,col,2] == 1) >> (state[tour,index,row,col,0] == 0))
                        model.addConstr((state[tour,index,row,col,2] == 1) >> (state[tour,index,row,col,3] == 0))

                        model.addConstr((state[tour,index,row,col,3] == 1) >> (state[tour,index,row,col,1] == 0))
                        model.addConstr((state[tour,index,row,col,3] == 1) >> (state[tour,index,row,col,2] == 0))
                        model.addConstr((state[tour,index,row,col,3] == 1) >> (state[tour,index,row,col,0] == 0))

                        model.addConstr((gp.quicksum(state[tour,index,row,col,i] for i in range(4)) == 1))

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

                    model.addConstr(state[tour,1, row, col, 1] == gp.or_(state[tour,0,row,col,1],key[tour,row,col,1])) #Bleu a droite que si on au moins un bleu dans la clé ou l'état d'aprés
                    model.addConstr(state[tour,0, row, col, 0] == gp.or_(state[tour,1,row,col,0],key[tour,row,col,0])) #Rouge a gauche que si on a un rouge dans la clé ou a droite

            for row in range(2,4): #Partie inférieur de la clé ne modifie pas (sauf fixe qui devient violet)
                for col in range(4):
                    model.addConstr((state[tour,0, row, col, 0] == 1) >> (state[tour,1, row, col, 0] == 1))
                    model.addConstr((state[tour,0, row, col, 1] == 1) >> (state[tour,1, row, col, 1] == 1))
                    model.addConstr((state[tour,0, row, col, 2] == 1) >> (state[tour,1, row, col, 2] == 1))
                    model.addConstr((state[tour,0, row, col, 3] == 1) >> (state[tour,1, row, col, 2] == 1))

        #Contrainte de la permutation :
        for tour in range(nombre_tour):
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
                
                #Skinny TRICK ?
                
        #model.computeIIS() 
        model.optimize()
        if model.Status == GRB.OPTIMAL:
            compteur_fix=0
            liste_X=[np.zeros((4,4)) for i in range(6)]
            liste_Y=[np.zeros((4,4)) for i in range(6)]
            liste_Z=[np.zeros((4,4)) for i in range(6)]
            for i in range(6):
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
            
            key_M=np.zeros((4,4))
            for row in range(4):
                for col in range(4):
                    if key[0,row,col,0].X==1.0:
                        key_M[row,col]=2
                    if key[0,row,col,1].X==1.0:
                        key_M[row,col]=3
                    if key[0,row,col,2].X==1.0:
                        key_M[row,col]=5

            return(True, compteur_fix, liste_X, liste_Y, liste_Z)
        elif model.Status == GRB.INFEASIBLE:
            return (False, 1000,np.zeros((nombre_tour,4,4)),np.zeros((nombre_tour,4,4)),np.zeros((nombre_tour,4,4)))
    
red_key_quantity = 1
blue_key_quantity = 1
# Key list generations
upper_key = [0 for i in range(red_key_quantity)] +\
            [2 for i in range(8-red_key_quantity)]
all_uper_key = []
# itertools.permutation generate the permutations of a list
permutations1 = list(itertools.permutations(upper_key))
for element in permutations1:
    if element not in all_uper_key:
        all_uper_key.append(element)
lower_key = [1 for i in range(blue_key_quantity)] +\
            [2 for i in range(8-blue_key_quantity)]
all_lower_key = []
permutations2 = list(itertools.permutations(lower_key))
for element in permutations2:
    if element not in all_lower_key:
        all_lower_key.append(element)

liste_key = []
for uper_element in all_uper_key:
    for lower_element in all_lower_key:
        liste_key.append(uper_element+lower_element)

key_array = []
for i in range(len(liste_key)):
    m_key = np.zeros((4, 4), dtype=int)
    m_key[0, 0] = liste_key[i][0]
    m_key[0, 1] = liste_key[i][1]
    m_key[0, 2] = liste_key[i][2]
    m_key[0, 3] = liste_key[i][3]
    m_key[1, 0] = liste_key[i][4]
    m_key[1, 1] = liste_key[i][5]
    m_key[1, 2] = liste_key[i][6]
    m_key[1, 3] = liste_key[i][7]
    m_key[2, 0] = liste_key[i][8]
    m_key[2, 1] = liste_key[i][9]
    m_key[2, 2] = liste_key[i][10]
    m_key[2, 3] = liste_key[i][11]
    m_key[3, 0] = liste_key[i][12]
    m_key[3, 1] = liste_key[i][13]
    m_key[3, 2] = liste_key[i][14]
    m_key[3, 3] = liste_key[i][15]
    key_array.append(m_key)

candidate_key = []
liste_X_candidate = []
liste_Y_candidate = []
liste_Z_candidate = []
liste_nombre_fix = []
for element in (key_array) :
    print(element)
    solution, nombre_fix,liste_X,liste_Y,liste_Z = structure(6,element)
    if nombre_fix <= 16 and solution:
        candidate_key.append(element)
        liste_X_candidate.append(liste_X)
        liste_Y_candidate.append(liste_Y)
        liste_Z_candidate.append(liste_Z)
        liste_nombre_fix.append(nombre_fix)

for indice,element in enumerate(candidate_key):
    print("____________CANDIDATE KEY ________________")
    affichage_grille(element,liste_X_candidate[indice],liste_Y_candidate[indice],liste_Z_candidate[indice])
    print(liste_nombre_fix[indice])
    print("__________________________________________")