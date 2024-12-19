#search for the optimal attack with various parameters
import numpy as np
import MILP_trunc_diff_MITM
import Differential_MITM_MILP
import parameters as p
import multiprocessing
from multiprocessing import Pool

structure_max = p.parameters["structure_max"]
structure_min = p.parameters["structure_min"]
MITM_up_max = p.parameters["MITM_up_max"]
disitnguisher_max = p.parameters["disitnguisher_max"]
MITM_down_max = p.parameters["MITM_down_max"]
MITM_up_min = p.parameters["MITM_up_min"]
distinguisher_min = p.parameters["distinguisher_min"]
MITM_down_min = p.parameters["MITM_down_min"]


z = p.parameters["word_size"]
Valid_matrix = np.zeros([structure_max+1,MITM_up_max+1,disitnguisher_max+1,MITM_down_max+1])
Complexite_matrix = np.zeros([structure_max+1,MITM_up_max+1,disitnguisher_max+1,MITM_down_max+1])


def search_attack(MITM_up_max2):
    for structure_round in range(structure_max,structure_max+1):
        for MITM_up_round in range(MITM_up_min,MITM_up_max2+1):
            for diff_round in range(distinguisher_min,disitnguisher_max+1):
                for MITM_down_round in range(MITM_down_min,MITM_down_max+1):
                    if (structure_round+MITM_up_round+diff_round+MITM_down_round >= p.parameters["attack_size_min"]) and (structure_round+MITM_up_round+diff_round+MITM_down_round <= p.parameters["attack_size_max"]):
                        print("###########################################")
                        print("tentative :", structure_round, MITM_up_round, diff_round, MITM_down_round )
                        if p.parameters["type_of_attack"] == 0:
                            attaque = MILP_trunc_diff_MITM.attack(structure_round, MITM_up_round, diff_round, MITM_down_round,3)
                        elif p.parameters["type_of_attack"] == 1:
                            attaque = Differential_MITM_MILP.attack(structure_round, MITM_up_round, diff_round, MITM_down_round,3)
                        attaque.append([structure_round, MITM_up_round, diff_round, MITM_down_round])
                        
with Pool(multiprocessing.cpu_count()) as pool:
        attaque = (pool.map(search_attack, range(MITM_up_min, MITM_up_max+1)))                        
        if attaque[0]:
            complexite_bleu = attaque[21]
            complexite_rouge = attaque[22]
            complexite_MATCH = attaque[23]
            Valid_matrix[attaque[24], attaque[25], attaque[26], attaque[28]] = 1
            Complexite_matrix[attaque[24], attaque[25], attaque[26], attaque[28]] = z*np.max([complexite_bleu, complexite_rouge, complexite_MATCH])



for structure_round in range(p.parameters["structure_max"]+1):
    for MITM_up_round in range(p.parameters["MITM_up_max"]+1):
        for diff_round in range(p.parameters["disitnguisher_max"]+1):
            for MITM_down_round in range(p.parameters["MITM_down_max"]+1):
                if Valid_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] == 1 and Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] <= p.parameters["complexity_max"] :
                    print("-------------------------------------------")
                    print("valid attack on ",structure_round + MITM_up_round+ diff_round+ MITM_down_round, " round, with complexity ", Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] )
                    print("parameters: ", structure_round, MITM_up_round, diff_round, MITM_down_round)
