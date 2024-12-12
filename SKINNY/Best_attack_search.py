#search for the optimal attack with various parameters
import numpy as np
import sys
import MILP_trunc_diff_MITM
import Differential_MITM_MILP
import parameters

z = parameters["word_size"]
Valid_matrix = np.zeros([parameters["structure_max"]+1,parameters["MITM_up_max"]+1,parameters["disitnguisher_max"]+1,parameters["MITM_down_max"]+1])
Complexite_matrix = np.zeros([parameters["structure_max"]+1,parameters["MITM_up_max"]+1,parameters["disitnguisher_max"]+1,parameters["MITM_down_max"]+1])
for structure_round in range(parameters["structure_min"],parameters["structure_max"]+1):
    for MITM_up_round in range(parameters["MITM_up_min"],parameters["MITM_up_max"]+1):
        for diff_round in range(parameters["disitnguisher_min"],parameters["disitnguisher_max"]+1):
            for MITM_down_round in range(parameters["MITM_down_min"],parameters["MITM_down_max"]+1):
                if (structure_round+MITM_up_round+diff_round+MITM_down_round >= parameters["attack_size_min"]) and (structure_round+MITM_up_round+diff_round+MITM_down_round <= parameters["attack_size_max"]):
                    print("###########################################")
                    print("tentative :", structure_round, MITM_up_round, diff_round, MITM_down_round )
                    if parameters["type_of_attack"] == 0:
                        attaque = MILP_trunc_diff_MITM.attack(structure_round, MITM_up_round, diff_round+1, MITM_down_round-1,3)
                    elif parameters["type_of_attack"] == 1:
                        attaque = Differential_MITM_MILP.attack(structure_round, MITM_up_round, diff_round, MITM_down_round,3)
                    if attaque[0]:
                        complexite_bleu = attaque[21]
                        complexite_rouge = attaque[22]
                        complexite_MATCH = attaque[23]
                        Valid_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] = 1
                        Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] = z*np.max([complexite_bleu, complexite_rouge, complexite_MATCH])
for structure_round in range(parameters["structure_max"]+1):
    for MITM_up_round in range(parameters["MITM_up_max"]+1):
        for diff_round in range(parameters["disitnguisher_max"]+1):
            for MITM_down_round in range(parameters["MITM_down_max"]+1):
                if Valid_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] == 1 and Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] <= parameters["complexity_max"] :
                    print("-------------------------------------------")
                    print("valid attack on ",structure_round + MITM_up_round+ diff_round+ MITM_down_round, " round, with complexity ", Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] )
                    print("parameters: ", structure_round, MITM_up_round, diff_round, MITM_down_round)

