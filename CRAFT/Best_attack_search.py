#Best attack search

import numpy as np
import MILP_trunc_diff_MITM
import parameters as p
import multiprocessing
from multiprocessing import Pool

structure_max = p.parameters["structure_max"]
structure_min = p.parameters["structure_min"]
MITM_up_max = p.parameters["MITM_up_max"]
disitnguisher_max = p.parameters["disitnguisher_max"]+1
MITM_down_max = p.parameters["MITM_down_max"]
MITM_up_min = p.parameters["MITM_up_min"]
distinguisher_min = p.parameters["distinguisher_min"]
MITM_down_min = p.parameters["MITM_down_min"]
z = p.parameters["word_size"]
Valid_matrix = np.zeros([structure_max+1,MITM_up_max+1,disitnguisher_max+1,MITM_down_max+1])
Complexite_matrix = np.zeros([structure_max+1,MITM_up_max+1,disitnguisher_max+1,MITM_down_max+1])


def search_attack(distinguisher_max2):
    all_attaque=[]
    for structure_round in range(structure_min, structure_max+1):
        for MITM_up_round in range(MITM_up_min, MITM_up_max+1):
            for MITM_down_round in range(MITM_down_min, MITM_down_max+1):
                if (structure_round + MITM_up_round + distinguisher_max2 + MITM_down_round >= p.parameters["attack_size_min"]) and (structure_round + MITM_up_round + distinguisher_max2 + MITM_down_round <= p.parameters["attack_size_max"]):
                    print("###########################################")
                    print("tentative :", structure_round, MITM_up_round, distinguisher_max2, MITM_down_round )
                    attaque = MILP_trunc_diff_MITM.attack(structure_round, MITM_up_round, distinguisher_max2, MITM_down_round)
                    attaque.append(structure_round)
                    attaque.append(MITM_up_round)
                    attaque.append(distinguisher_max2)
                    attaque.append(MITM_down_round)
                    all_attaque.append(attaque)
    return(all_attaque)
                        
with Pool(multiprocessing.cpu_count()) as pool:
    resultat = (pool.map(search_attack, range(distinguisher_min, disitnguisher_max+1)))   
    for i in range(1,len(resultat)): 
        for j in range(0, len(resultat[i])):           
            if resultat[i][j][0]:
                complexite_bleu = resultat[i][j][13]
                complexite_rouge = resultat[i][j][12]
                complexite_MATCH = resultat[i][j][14]
                Valid_matrix[resultat[i][j][18], resultat[i][j][19], resultat[i][j][20], resultat[i][j][21]] = 1
                Complexite_matrix[resultat[i][j][18], resultat[i][j][19], resultat[i][j][20], resultat[i][j][21]] = z*np.max([complexite_bleu, complexite_rouge, complexite_MATCH])

for structure_round in range(structure_max+1):
    for MITM_up_round in range(MITM_up_max+1):
        for diff_round in range(disitnguisher_max+1):
            for MITM_down_round in range(MITM_down_max+1):
                if Valid_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] == 1 and Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] <= p.parameters["complexity_max"] :
                    print("-------------------------------------------")
                    print("valid attack on ",structure_round + MITM_up_round+ diff_round+ MITM_down_round, " round, with complexity ", Complexite_matrix[structure_round, MITM_up_round, diff_round, MITM_down_round] )
                    print("parameters: ", structure_round, MITM_up_round, diff_round, MITM_down_round)

print ("fin de recherche")
