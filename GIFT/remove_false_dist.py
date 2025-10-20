import os
import shutil
import sys
from itertools import product
import numpy as np
import filecmp

DDT = [['0'],
       ['5','6','8','9','a','b','c','f'], #1
       ['5','6','9','a','d','e'], #2
       ['5','6','8','b','c','d','e''f'], #3
       ['3','5','7','9','d'], #4
       ['2','5','8','c','d','e','f'],#5
       ['2','3','7','a','e'],#6
       ['2','5','8','9','a','b','c',],#7
       ['3','7','b','f'],#8
       ['1','3','6','7','8','a','c','d'],#9
       ['1','6','9','a','d','e'],#a
       ['1', '3', '6', '7', '8', '9', 'c', 'e'],#b
       ['2', '4', '8', 'a', 'c', 'e'],#c
       ['1', '2', '4', 'a', 'b', 'd', 'f'], #d
       ['1', '4', '8', '9', 'c', 'd'], #e
       ['1', '2', '4', '9', 'b', 'e', 'f']#f
       ]

def delete_fake_distinguisher(chemin_dossier):
    for fichier in os.listdir(chemin_dossier):
        chemin_fichier = os.path.join(chemin_dossier, fichier)
        if os.path.isfile(chemin_fichier):
            with open(chemin_fichier, 'r') as file :
                lignes = file.readlines()

            effacer_fichier = False
            for indice_ligne in range(0, len(lignes)-1, 3):
                ligne = lignes[indice_ligne]
                index_decalage = 0
                while True:
                    position = ligne.find('x', index_decalage)
                    if position == -1:
                        break
                    valeur = int(f'0x{lignes[indice_ligne][position+1]}',16)
                    if lignes[indice_ligne+1][position+1] not in DDT[valeur]:
                        effacer_fichier = True
                        break
                    index_decalage = position + 1
                if effacer_fichier :
                    break
            if effacer_fichier:
                os.remove(chemin_fichier)
                print(f"Fichier supprimé, distingueur faux : {fichier}")

def remove_same_distinguisher(chemin_dossier):
    fichiers = sorted(os.listdir(chemin_dossier))
    fichiers_uniques = set()

    for indice_fichier, fichier in enumerate(fichiers):
        chemin_fichier = os.path.join(chemin_dossier, fichier)
        if not os.path.isfile(chemin_fichier):
            continue
        est_un_doublon = False
        
        for fichier_a_verifier in list(fichiers_uniques):
            chemin_fichier_a_verifier = os.path.join(chemin_dossier, fichier_a_verifier)
            if filecmp.cmp(chemin_fichier, chemin_fichier_a_verifier, shallow=False):
                est_un_doublon = True
        if est_un_doublon:
            os.remove(chemin_fichier)
            print("fichier supprimé car distingueur déja existant")
        else :
            fichiers_uniques.add(fichier)

delete_fake_distinguisher('/home/bamichel/Downloads/DistingueursGIFT')
remove_same_distinguisher('/home/bamichel/Downloads/DistingueursGIFT')