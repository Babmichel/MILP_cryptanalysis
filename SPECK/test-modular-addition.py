import sage.all as sage
import itertools
import numpy as np

n = 4
M=[[[]for i in range(2**n)]for i in range(2**n)]
for etat1_ in range(2**n):
    for etat1 in range(2**n):
        for etat2_ in range(2**n):
            for etat2 in range(2**n):
                diff1 = etat1_ ^ etat1
                diff2 = etat2 ^ etat2_
                etat3 = (etat1 + etat2)%(2**n)
                etat3_ = (etat1_ + etat2_)%(2**n)
                diff3 = (etat3 ^ etat3_)
                if diff3 not in M[diff1][diff2]:
                    M[diff1][diff2].append(diff3)
                #print('(',format(etat1_, f'0{n}b'),'+',format(etat2_, f'0{n}b'),')','⊕','(',format(etat1, f'0{n}b'),'+',format(etat2, f'0{n}b'),')','=',format(diff3, f'0{n}b'))
                #print('   ',format(diff1, f'0{n}b'),'    +    ',format(diff2, f'0{n}b'),'    ')
                #print('')

for i in range(n+1):
    print(' ', end="")
for diff1 in range(2**n):
    print(format(diff1, f'0{n}b'), end="")
    print(' ', end="")
print('')
for diff2 in range(2**n):
    print(format(diff2, f'0{n}b'), end="")
    print(' ', end="")
    for diff1 in range(2**n):
        for bit in range(n):
            unknow=False
            boucle=True
            while boucle :
                for i in range(len(M[diff1][diff2])):
                    for j in range(i+1, len(M[diff1][diff2])):
                        if(format(M[diff1][diff2][i], f'0{n}b')[bit] != format(M[diff1][diff2][j], f'0{n}b')[bit]):
                            unknow=True
                            boucle=False
                boucle=False        
            if unknow:
                print('?', end="")
            elif format(M[diff1][diff2][0], f'0{n}b')[bit]=='0':
                print('0',end="")
            else :
                print('1', end="")
        print(' ' , end="")
    print('')

