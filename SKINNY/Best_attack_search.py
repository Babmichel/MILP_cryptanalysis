#search for the optimal attack with various parameters
import numpy as np
import sys
import MILP_trunc_diff_MITM
import Differential_MITM_MILP

type_of_attack = int(sys.argv[1])
attack_size_min = int(sys.argv[2])
attack_size_max = int(sys.argv[3])
complexity_max = int(sys.argv[4])
word_size = int(sys.argv[5])


def recherche_attaque(mim_round, max_round, complexity, word_size):
    z = word_size
    Valid_matrix = np.zeros([9,12,13,11])
    Complexite_matrix = np.zeros([9,12,13,11])
    for structure_round in range(2,3):
        for MITM_up_round in range(6,7):
            for diff_round in range(9,10):
                for MITM_down_round in range(6,7):
                    if (structure_round+MITM_up_round+diff_round+MITM_down_round >= mim_round) and (structure_round+MITM_up_round+diff_round+MITM_down_round <= max_round):
                        print("###########################################")
                        print("tentative :", structure_round, MITM_up_round, diff_round, MITM_down_round )
                        if type_of_attack == 0:
                            attaque = MILP_trunc_diff_MITM.attack(structure_round, MITM_up_round, diff_round+1, MITM_down_round-1,3)
                        elif type_of_attack == 1:
                            attaque = Differential_MITM_MILP.attack(structure_round, MITM_up_round, diff_round, MITM_down_round,3)
                        if attaque[0]:
                            complexite_bleu = attaque[21]
                            complexite_rouge = attaque[22]
                            complexite_MATCH = attaque[23]
                            Valid_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] = 1
                            Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] = z*np.max([complexite_bleu, complexite_rouge, complexite_MATCH])
    for structure_round in range(9):
        for MITM_up_round in range(12):
            for diff_round in range(11):
                for MITM_down_round in range(9):
                    if Valid_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] == 1 and Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] <= complexity :
                        print("-------------------------------------------")
                        print("valid attack on ",structure_round + MITM_up_round+ diff_round+ MITM_down_round, " round, with complexity ", Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] )
                        print("parameters: ", structure_round, MITM_up_round, diff_round, MITM_down_round)

recherche_attaque(attack_size_min, attack_size_max, complexity_max, word_size)