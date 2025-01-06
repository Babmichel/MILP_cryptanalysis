#Display the optimal attack with the given parameters

import sys
import MILP_trunc_diff_MITM
import Differential_MITM_MILP

type_of_attack = int(sys.argv[1])
structure_size = int(sys.argv[2])
MITM_up_size = int(sys.argv[3])
distinguisher_size = int(sys.argv[4])
MITM_down_size = int(sys.argv[5])
key_space_size = int(sys.argv[6])

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
                elif Liste_X_diff[i][ligne, colonne] == 5:
                    print("\033[95m ■", end="")
                elif Liste_X_diff[i][ligne, colonne] == 1:
                    print("\033[90m ■", end="")
                elif Liste_X_diff[i][ligne, colonne] == -1:
                    print("\033[95m F", end="")
                else:
                    print("\033[90m ■", end="")
            print("\033[90m| |", end="")
            for colonne in range(4):
                if Liste_Y_diff[i][ligne, colonne] == 2:
                    print("\033[91m ■", end="")
                elif Liste_Y_diff[i][ligne, colonne] == 3:
                    print("\033[94m ■", end="")
                elif Liste_Y_diff[i][ligne, colonne] == 5:
                    print("\033[95m ■", end="")
                elif Liste_Y_diff[i][ligne, colonne] == 1:
                    print("\033[90m ■", end="")
                elif Liste_Y_diff[i][ligne, colonne] == -1:
                    print("\033[95m F", end="")
                else:
                    print("\033[90m X", end="")
            print("\033[90m|")
        print("  ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾      ‾ ‾ ‾ ‾      ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾      ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾\n \n")

def display_attack(structure, MITM_up, diff, MITM_down, key_space,z=4):
    if type_of_attack == 0 :
        resultat = MILP_trunc_diff_MITM.attack(structure, MITM_up, diff+1, MITM_down-1, key_space)
    elif type_of_attack == 1 :
        resultat = Differential_MITM_MILP.attack(structure, MITM_up, diff, MITM_down, key_space)
    if resultat[0] :
        key_M, key_0,key_1 ,key_2 = resultat[1], resultat[2], resultat[3], resultat[4]
        liste_X, liste_Y, liste_Z, Liste_X_diff, Liste_Y_diff = resultat[5], resultat[6], resultat[7], resultat[8], resultat[9]
        compteur_bleu, compteur_rouge, compteur_differentielle, start_diff, end_diff, compteur_fix, compteur_violet,compteur_statetest_haut, compteur_statetest_bas, compteur_probaup, compteur_probadown = resultat[10], resultat[11], resultat[12], resultat[13], resultat[14], resultat[15], resultat[16], resultat[17], resultat[18], resultat[19], resultat[20]
        Cblue, Cred, Cmatch = resultat[21], resultat[22], resultat[23]
        affichage_grille(key_M, key_0, key_1, key_2, liste_X, liste_Y, liste_Z,Liste_X_diff, Liste_Y_diff)
        print("attaque differential MITM")
        print("nombre de tours : ")
        print(structure + MITM_up + diff + MITM_down)
        print("parametre attaque : ")
        print(structure, MITM_up, diff, MITM_down)
        print('Nombre de bleu guess : ')
        print(compteur_bleu, z*compteur_bleu)
        print('Nombre de rouge guess : ')
        print(compteur_rouge, z*compteur_rouge)
        print('Nombre de violet guess : ')
        print(compteur_violet, z*compteur_violet)
        print('coup de la differentielle : ')
        print(compteur_differentielle, z*compteur_differentielle)
        print('nombre de F : ')
        print(compteur_fix, z*compteur_fix)
        print("differentielle tronque, taille entre et sortie")
        print(start_diff, end_diff, z*start_diff, z*end_diff)
        print("state tests haut et bas")
        print(compteur_statetest_haut, compteur_statetest_bas)
        print("Probabilist key recovery haut et bas")
        print(compteur_probaup, compteur_probadown)
        print("complexite")
        print("generation des bleus :", z*Cblue)
        print("generation des rouges :", z*Cred)
        print("MATCH ?", z*Cmatch)
    else :
        print("attaque differential MITM")
        print("nombre de tours : ")
        print(structure + MITM_up + diff + MITM_down)
        print("nombre de tours de la structure: ")
        print(structure)
        print("nombre de tours de la MITM up: ")
        print(MITM_up)
        print("nombre de tours de la differentielle: ")
        print(diff)
        print("nombre de tours de la MITM down: ")
        print(MITM_down)
        print("INFEASABLE")
    
display_attack(structure_size, MITM_up_size, distinguisher_size, MITM_down_size, key_space_size)

