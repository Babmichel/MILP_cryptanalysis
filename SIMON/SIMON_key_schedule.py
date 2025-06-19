rounds= 30
key_size = 64
state_size = 32
subkey_quantity = int((key_size/state_size)*2)
subkey_size = int(state_size/2)

connu = []
for j in range(subkey_size):
    connu.append(f'k0_{j}')
for j in [0, 1, 2, 3, 4, 7, 8, 9, 10, 11, 13, 14, 15]:
    connu.append(f'k1_{j}')
for j in [0, 1, 2, 9, 12, 15]:
    connu.append(f'k2_{j}')
for j in [1]:
    connu.append(f'k3_{j}')

K=[[[] for j in range(subkey_size)] for i in range(rounds)]
for j in range(subkey_size):
    for i in range(subkey_quantity):
        K[i][j].append(f'k{i}_{j}')

for i in range(subkey_quantity, rounds):
    if subkey_quantity == 4:
        for j in range(subkey_size):
            for element in K[i-4][j]:
                if element in K[i][j]:
                    K[i][j].remove(element)
                else :
                    K[i][j].append(element)
            for element in K[i-1][(j+3)%subkey_size]:
                if element in K[i][j]:
                    K[i][j].remove(element)
                else :
                    K[i][j].append(element)
            for element in K[i-1][(j+4)%subkey_size]:
                if element in K[i][j]:
                    K[i][j].remove(element)
                else :
                    K[i][j].append(element)
            for element in K[i-3][j]:
                if element in K[i][j]:
                    K[i][j].remove(element)
                else :
                    K[i][j].append(element)
            for element in K[i-3][(j+1)%subkey_size]:
                if element in K[i][j]:
                    K[i][j].remove(element)
                else :
                    K[i][j].append(element)
    else :
        print('not implemeted yet')

for i in range(rounds) :
    for j in range(subkey_size):
        for element in connu:
            if element in K[i][j] :
                K[i][j].remove(element)
        K[i][j].sort()

print(K[23][1])
