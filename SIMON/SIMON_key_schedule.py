import copy

rounds= 30
key_size = 64
state_size = 32
subkey_quantity = int((key_size/state_size)*2)
subkey_size = int(state_size/2)


connu = []
for j in range(subkey_size):
    connu.append(f'k0_{j}')
for j in [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 15]:
    connu.append(f'k1_{j}')
for j in [0, 1, 2, 3, 5, 9, 10, 12, 15]:
    connu.append(f'k2_{j}')
for j in [1, 4]:
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
            for element in K[i-1][(j-3)%subkey_size]:
                if element in K[i][j]:
                    K[i][j].remove(element)
                else : 
                     K[i][j].append(element)
            for element in K[i-1][(j-4)%subkey_size]:
                if element in K[i][j]:
                    K[i][j].remove(element)
                else :
                    K[i][j].append(element)
            for element in K[i-3][j]:
                if element in K[i][j]:
                    K[i][j].remove(element)
                else :
                    K[i][j].append(element)
            for element in K[i-3][(j-1)%subkey_size]:
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

K_copy_up = copy.deepcopy(K)
K_copy_down = copy.deepcopy(K)
K_prime_up =[[[] for j in range(subkey_size)] for i in range(rounds)]
K_prime_down = [[[] for j in range(subkey_size)] for i in range(rounds)]

for j in range(subkey_size):
    K_prime_up[1][j] = K_copy_up[1][j]
for i in range(2, 5):
    for j in range(subkey_size):
        K_prime_up[i][j]=K_copy_up[i][j]
        for element in K_prime_up[i-1][(j-2)%16]:
            if element in K_prime_up[i][j] :
                K_prime_up[i][j].remove(element)
            else : 
                K_prime_up[i][j].append(element)

for j in range(subkey_size):
    K_prime_down[22] = K_copy_down[23]
for i in range(21, 19, -1):
    for j in range(subkey_size):
        K_prime_down[i][j]=K_copy_down[i][j]
        for element in K_prime_down[i+1][(j-2)%16]:
            if element in K_prime_down[i][j] :
                K_prime_down[i][j].remove(element)


print(K[4][0])
print(K_prime_up[4][0])
print(K_prime_down[22][0])



