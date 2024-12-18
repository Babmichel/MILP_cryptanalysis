#display-attack
import sys
import MILP_trunc_diff_MITM
import numpy as np

structure_size = int(sys.argv[1])
MITM_up_size = int(sys.argv[2])
distinguisher_size = int(sys.argv[3])
MITM_down_size = int(sys.argv[4])

def affichage_grille(state, differences, key):
    total_round = np.shape(key)[0]
    for round in range(total_round):
        print("TOUR", round)
        print("  _ _W_ _    _ _X_ _    _ _Y_ _    _ _Z_ _     _D_W_ _    _D_X_ _    _D_Y_ _    _D_Z_ _     _ _K_ _ ")
        for ligne in range(4):
            print("\033[90m ", end="")
            for step in range(4):
                for colonne in range(4):
                    if state[round, step, ligne, colonne] == 1:
                        print("\033[91m ■", end="")
                    elif state[round, step, ligne, colonne] == 0:
                        print("\033[90m ■", end="")    
                    elif state[round, step, ligne, colonne] == 2:
                        print("\033[94m ■", end="")
                    elif state[round, step, ligne, colonne] == 3:
                        print("\033[95m ■", end="")
                    elif state[round, step, ligne, colonne] == -1:
                        print("\033[95m F", end="")
                    else:
                        print("\033[99m X", end="")
                print("\033[90m| |", end="")
            print("\033[90m ", end="")
            for step in range(4):
                for colonne in range(4):
                    if differences[round, step, ligne, colonne] == 0:
                        print("\033[90m ■", end="")
                    elif differences[round, step, ligne, colonne] == 1:
                        print("\033[91m ■", end="")
                    elif differences[round, step, ligne, colonne] == 2:
                        print("\033[94m ■", end="")
                    elif differences[round, step, ligne, colonne] == 3:
                        print("\033[95m ■", end="")
                    elif differences[round, step, ligne, colonne] == -1:
                        print("\033[95m F", end="")
                    else:
                        print("\033[99m X", end="")
                print("\033[90m| |", end="")
            print("\033[90m ", end="")
            for colonne in range(4):
                if key[round, ligne, colonne] == 0:
                    print("\033[90m ■", end="")
                elif key[round, ligne, colonne] == 1:
                    print("\033[91m ■", end="")
                elif key[round, ligne, colonne] == 2:
                    print("\033[94m ■", end="")
                elif key[round, ligne, colonne] == 3:
                    print("\033[95m ■", end="")
                else:
                    print("\033[99m X", end="")
            print("\033[90m|\n", end="")
        print("  ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾     ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾    ‾ ‾ ‾ ‾     ‾ ‾ ‾ ‾ \n \n")  


resultat = MILP_trunc_diff_MITM.attack(structure_size, MITM_up_size, distinguisher_size, MITM_down_size)
if resultat[0] == True:
    affichage_grille(resultat[1], resultat[2], resultat[3])
    print("attaque differential MITM")
    print("nombre de tours : ")
    print(structure_size+ MITM_up_size+ distinguisher_size+ MITM_down_size)
    print("parametre attaque : ")
    print(structure_size, MITM_up_size, distinguisher_size, MITM_down_size)
    print('Nombre de bleu guess : ')
    print(resultat[4])
    print('Nombre de rouge guess : ')
    print(resultat[5])
    print('Nombre de violet guess : ')
    print(resultat[6])
    print('coup de la differentielle : ')
    print(resultat[11])
    print('nombre de F : ')
    print(resultat[15])
    print("differentielle tronque, taille entre et sortie")
    print(resultat[16], resultat[17])
    print("state tests haut et bas")
    print(resultat[7], resultat[8])
    print("Probabilist key recovery haut et bas")
    print(resultat[9], resultat[10])
    print("complexite")
    print("generation des bleus :", 4*resultat[13])
    print("generation des rouges :", 4*resultat[12])
    print("MATCH ?", 4*resultat[14])

