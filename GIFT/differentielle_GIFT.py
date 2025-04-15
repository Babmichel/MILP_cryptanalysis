import numpy as np
import gurobipy as gp
from gurobipy import GRB
from tqdm import tqdm
from itertools import product

def diff_gift(round_number):
    options = {
            "WLSACCESSID" : "ffd7aab1-ddce-4db1-b37a-cf70288fb87c",
            "WLSSECRET" : "1746d0d5-a916-47fb-b0aa-9f67cb800c57",
            "LICENSEID" : 2602460 }
    
    with gp.Env(params=options) as env, gp.Model(env=env) as model:
        AK_bit_list_0 = [2,3, 6,7, 10,11, 14,15, 18,19, 22,23, 26,27, 30,31]
        AK_bit_list_1 = [34,35, 38,39, 42,43, 46,47, 50,51, 54,55, 58,59, 62,63]
        AK_bit_list_2 = [0,1,4,5,8,9,12,13,16,17,20,21,24,25,28,29,32,33,36,37,40,41,44,45,48,49,52,53,56,57,60,61]

        #$# initialisation numpy #$#
        state = np.zeros((round_number, 3, 64), dtype=object)
        state_not = np.zeros((round_number, 3, 64), dtype=object)

        key = np.zeros((8,16), dtype=object)

        sbox_layer = np.zeros((round_number-1, 16, 4), dtype=object)

        and_sbox_6 = np.zeros((round_number, 16, 2), dtype=object)

        and_sbox_4 = np.zeros((round_number, 16, 12), dtype=object)

        #$# intialisation gurobi #$#
        for round, step, bit in product(range(round_number), range(3), range(64)):
            state[round, step, bit] = model.addVar(vtype = GRB.BINARY, name = f'state {round} {step} {bit}')
            state_not[round, step, bit] = model.addVar(vtype = GRB.BINARY, name = f'state not {round} {step} {bit}')
        
        for k, index in product(range(8), range(16)):
            key[k, index] = model.addVar(vtype = GRB.BINARY, name = f'key {bit}')

        for round, sbox, proba in product(range(round_number-1), range(16), range(4)):
            sbox_layer[round, sbox, proba] = model.addVar(vtype = GRB.BINARY, name = f'sbox_layer {round} {sbox} {bit}')
        
        for round, sbox, constr in product(range(round_number), range(16), range(2)):
            and_sbox_6[round, sbox, constr] = model.addVar(vtype=GRB.BINARY, name=f"sbox 6_{constr}")
        
        for round, sbox, constr in product(range(round_number), range(16), range(12)):
            and_sbox_4[round, sbox, constr] = model.addVar(vtype=GRB.BINARY, name=f"sbox 6_{constr}")

        #$# Contraintes #$#
        for round, step, bit in product(range(round_number), range(3), range(64)):
            model.addConstr(state[round, step, bit] == 1 - state_not[round, step, bit])
        
        
        #Permutation
        P=[0, 17, 34, 51, 48, 1, 18, 35, 32, 49, 2, 19, 16, 33, 50, 3, 4, 21, 38, 55, 52, 5, 22, 39, 36, 53, 6, 23, 20, 37, 54, 7, 8, 25, 42, 59, 56, 9, 26, 43, 40, 57, 10, 27, 24, 41, 58, 11, 12, 29, 46, 63, 60, 13, 30, 47, 44, 61, 14, 31, 28, 45, 62, 15]
        for round, bit in product(range(round_number), range(63,-1,-1)):
            model.addConstr(state[round, 0, bit] == state[round, 1, P[bit]])

        #Key addition
        for round in range(round_number):
            for bit in AK_bit_list_0: 
                model.addConstr((state[round, 2, bit] == 1) >> (state[round, 1, bit] + key[2*(round % 4), ((bit//2 - 1+bit%2) + 12*(round//4))%16] == 1))
                model.addConstr((state[round, 2, bit] == 0) >> (state[round, 1, bit] + key[2*(round % 4), ((bit//2 - 1+bit%2) + 12*(round//4))%16] == 0))
            for bit in AK_bit_list_1:
                model.addConstr((state[round, 2, bit] == 1) >> (state[round, 1, bit] + key[2*(round % 4) + 1, ((bit//2 - 1+bit%2) + 2*(round//4))%16] == 1))
                model.addConstr((state[round, 2, bit] == 0) >> (state[round, 1, bit] + key[2*(round % 4) + 1, ((bit//2 - 1+bit%2) + 2*(round//4))%16] == 0))
            for bit in AK_bit_list_2:
                model.addConstr((state[round, 2, bit] == state[round, 1, bit]))

        #SBox

        for round, sbox in product(range(round_number-1), range(16)):
            
            model.addConstr(gp.quicksum(sbox_layer[round, sbox, proba] for proba in range(4)) == 1)

            bit_0_in, bit_1_in, bit_2_in, bit_3_in = state[round, 2, 4*sbox+3], state[round, 2, 4*sbox+2], state[round, 2, 4*sbox+1], state[round, 2, 4*sbox]
            not_bit_0_in, not_bit_1_in, not_bit_2_in, not_bit_3_in = state_not[round, 2, 4*sbox+3], state_not[round, 2, 4*sbox+2], state_not[round, 2, 4*sbox+1], state_not[round, 2, 4*sbox]

            bit_0_out, bit_1_out, bit_2_out, bit_3_out = state[round+1, 0, 4*sbox+3], state[round+1, 0, 4*sbox+2], state[round+1, 0, 4*sbox+1], state[round+1, 0, 4*sbox]
            not_bit_0_out, not_bit_1_out, not_bit_2_out, not_bit_3_out = state_not[round+1, 0, 4*sbox+3], state_not[round+1, 0, 4*sbox+2], state_not[round+1, 0, 4*sbox+1], state_not[round+1, 0, 4*sbox]

            input_bit = [bit_0_in, bit_1_in, bit_2_in, bit_3_in]
            output_bit = [bit_0_out, bit_1_out, bit_2_out, bit_3_out]
            all_bit = input_bit + output_bit
            
            #equations
            model.addConstr(4*bit_0_in + 6*bit_0_out + 1*bit_1_in + -5*bit_1_out - 5*bit_2_in + 6*bit_2_out + 3*bit_3_in - 2*bit_3_out >= -6)
        
            model.addConstr(5*bit_0_in + 6*bit_0_out + 2*bit_1_in + 4*bit_1_out + 3*bit_2_in - 3*bit_2_out - 1*bit_3_in - 3*bit_3_out >= -1)
            model.addConstr(6*bit_0_in - 3*bit_0_out - 3*bit_1_in - 4*bit_1_out - 3*bit_2_in - 6*bit_2_out + 1*bit_3_in - 2*bit_3_out >= -15)
            model.addConstr(3*bit_0_in - 6*bit_0_out + 3*bit_1_in + 1*bit_1_out + 5*bit_2_in + 4*bit_2_out + 2*bit_3_in + 3*bit_3_out >= 0)
        
            model.addConstr(3*bit_0_in - 2*bit_0_out + 6*bit_1_in + 4*bit_1_out - 6*bit_2_in - 6*bit_2_out - 1*bit_3_in + 3*bit_3_out >= -9)
            model.addConstr(2*bit_0_in + 1*bit_0_out - 6*bit_1_in + 3*bit_1_out + 3*bit_2_in + 5*bit_2_out + 3*bit_3_in + 4*bit_3_out >= 0)
            model.addConstr(-6*bit_0_in + 2*bit_0_out - 6*bit_1_in - 6*bit_1_out + 6*bit_2_in + 5*bit_2_out - 1*bit_3_in - 6*bit_3_out >= -19)
            model.addConstr(5*bit_0_in + 6*bit_0_out + 6*bit_1_in + 3*bit_1_out - 3*bit_2_in + 3*bit_2_out - 2*bit_3_in - 1*bit_3_out >= 0)

            model.addConstr(4*bit_0_in - 6*bit_0_out - 6*bit_1_in + 6*bit_1_out - 5*bit_2_in + 1*bit_2_out - 2*bit_3_in - 5*bit_3_out >= -18)
            model.addConstr(-3*bit_0_in + 1*bit_0_out - 6*bit_1_in - 3*bit_1_out - 2*bit_2_in - 4*bit_2_out - 4*bit_3_in + 6*bit_3_out >= -16)
            model.addConstr(-3*bit_0_in - 2*bit_0_out - 1*bit_1_in - 6*bit_1_out - 6*bit_2_in + 5*bit_2_out - 6*bit_3_in + 4*bit_3_out >= -18)
            model.addConstr(-2*bit_0_in - 3*bit_0_out + 6*bit_1_in - 1*bit_1_out + 6*bit_2_in - 3*bit_2_out + 6*bit_3_in + 4*bit_3_out >= -3)

            model.addConstr(2*bit_0_in + 1*bit_0_out + 6*bit_1_in - 3*bit_1_out + 3*bit_2_in + 5*bit_2_out - 3*bit_3_in + 4*bit_3_out >= -0)
            model.addConstr(-3*bit_0_in - 3*bit_0_out + 3*bit_1_in + 6*bit_1_out - 2*bit_2_in + 1*bit_2_out + 6*bit_3_in + 5*bit_3_out >= -2)
            model.addConstr(-6*bit_0_in - 1*bit_0_out - 6*bit_1_in - 6*bit_1_out + 6*bit_2_in + 5*bit_2_out + 4*bit_3_in - 2*bit_3_out >= -15)
            model.addConstr(-3*bit_0_in - 1*bit_0_out - 6*bit_1_in + 2*bit_1_out + 3*bit_2_in - 4*bit_2_out - 6*bit_3_in + 5*bit_3_out >= -14)

            model.addConstr(-6*bit_0_in + 2*bit_0_out + 6*bit_1_in - 6*bit_1_out - 5*bit_2_in - 6*bit_2_out - 1*bit_3_in - 6*bit_3_out >= -24)
            model.addConstr(-5*bit_0_in + 6*bit_0_out - 6*bit_1_in + 6*bit_1_out - 5*bit_2_in - 2*bit_2_out + 6*bit_3_in - 1*bit_3_out >= -13)

            #type sbox
            for bit in all_bit :
                model.addConstr((bit == 1) >> (sbox_layer[round, sbox, 0] == 0))
            for bit in input_bit:
                model.addConstr((bit == 1) >> (gp.quicksum(bits for bits in output_bit) >= 1))
            for bit in output_bit:
                model.addConstr((bit == 1) >> (gp.quicksum(bits for bits in input_bit) >= 1))

            
            model.addGenConstrAnd(and_sbox_6[round, sbox, 0], [not_bit_0_in, bit_1_in, not_bit_2_in, not_bit_3_in,   not_bit_0_out, bit_1_out, bit_2_out, bit_3_out])
            model.addGenConstrAnd(and_sbox_6[round, sbox, 1], [not_bit_0_in, bit_1_in, bit_2_in, not_bit_3_in,   not_bit_0_out, not_bit_1_out, bit_2_out, bit_3_out])
            
            model.addGenConstrAnd(and_sbox_4[round, sbox, 0], [not_bit_0_in, not_bit_1_in, bit_2_in, not_bit_3_in,   not_bit_0_out, bit_1_out, not_bit_2_out, bit_3_out])
            model.addGenConstrAnd(and_sbox_4[round, sbox, 1], [not_bit_0_in, not_bit_1_in, bit_2_in, not_bit_3_in,   not_bit_0_out, bit_1_out, bit_2_out, not_bit_3_out])
            model.addGenConstrAnd(and_sbox_4[round, sbox, 2], [not_bit_0_in, not_bit_1_in, bit_2_in, not_bit_3_in,   not_bit_0_out, bit_1_out, not_bit_2_out, bit_3_out])
            model.addGenConstrAnd(and_sbox_4[round, sbox, 3], [not_bit_0_in, bit_1_in, not_bit_2_in, not_bit_3_in,   not_bit_0_out, bit_1_out, not_bit_2_out, bit_3_out])

            model.addGenConstrAnd(and_sbox_4[round, sbox, 4], [not_bit_0_in, bit_1_in, bit_2_in, not_bit_3_in,   not_bit_0_out, not_bit_1_out, bit_2_out, not_bit_3_out])
            model.addGenConstrAnd(and_sbox_4[round, sbox, 5], [not_bit_0_in, bit_1_in, bit_2_in, bit_3_in,   bit_0_out, not_bit_1_out, bit_2_out, bit_3_out])
            model.addGenConstrAnd(and_sbox_4[round, sbox, 6], [bit_0_in, not_bit_1_in, not_bit_2_in, not_bit_3_in,   not_bit_0_out, not_bit_1_out, bit_2_out, bit_3_out])

            model.addGenConstrAnd(and_sbox_4[round, sbox, 7], [bit_0_in, not_bit_1_in, bit_2_in, not_bit_3_in,   not_bit_0_out, bit_1_out, bit_2_out, not_bit_3_out])
            model.addGenConstrAnd(and_sbox_4[round, sbox, 8], [bit_0_in, bit_1_in, not_bit_2_in, not_bit_3_in,   not_bit_0_out, not_bit_1_out, bit_2_out, not_bit_3_out])
            model.addGenConstrAnd(and_sbox_4[round, sbox, 9], [bit_0_in, bit_1_in, bit_2_in, not_bit_3_in,   not_bit_0_out, not_bit_1_out, not_bit_2_out, bit_3_out])

            model.addGenConstrAnd(and_sbox_4[round, sbox, 10], [bit_0_in, not_bit_1_in, not_bit_2_in, not_bit_3_in])
            model.addGenConstrAnd(and_sbox_4[round, sbox, 11], [not_bit_0_out, bit_1_out, not_bit_2_out, not_bit_3_out])

            
            model.addGenConstrOr(sbox_layer[round, sbox,  3], [and_sbox_6[round, sbox, constr] for constr in range(2)])
            model.addGenConstrOr(sbox_layer[round, sbox,  2], [and_sbox_4[round, sbox, constr] for constr in range(12)])
            

        #start constraints
        
        start = [9, 10, 12, 28, 29, 40, 45, 46, 56, 57]
        for bit in range(64) :
            if bit in start :
                model.addConstr(state[0, 0, bit] == 1)
            else :
                model.addConstr(state[0, 0, bit] == 0)
        
        
        end = [0, 1, 2, 3, 4, 5, 6, 7, 8, 32, 33, 34, 35, 36, 37, 38, 39]
        for bit in range(64) :
            if bit in end:
                model.addConstr(state[round_number - 1, 2, bit] == 1)
            else :
                model.addConstr(state[round_number - 1, 2, bit] == 0)
        

        key_diff_count = gp.quicksum(key[k, index] for k in range(8) for index in range(16))
        active_sbox_2 = gp.quicksum(sbox_layer[round, sbox, 1] for round in range(round_number-1) for sbox in range(16))
        active_sbox_4 = gp.quicksum(sbox_layer[round, sbox, 2] for round in range(round_number-1) for sbox in range(16))
        active_sbox_6 = gp.quicksum(sbox_layer[round, sbox, 3] for round in range(round_number-1) for sbox in range(16))
        active_sbox = 3*active_sbox_2 + 2*active_sbox_4 + 1.415*active_sbox_6


        model.setObjective(5*active_sbox + key_diff_count, GRB.MINIMIZE)

        model.optimize()

        if model.Status == GRB.OPTIMAL:
            state_to_display = np.zeros((round_number, 3, 64), dtype=int)

            key_to_display = np.zeros((8, 16), dtype=int)

            sbox_to_display = np.zeros((round_number, 16), dtype=int)

            for round, step, bit in product(range(round_number), range(3), range(64)):
                if state[round, step, bit].X == 1 :
                    state_to_display[round, step, bit] = int(1)

            for k, index in product(range(8), range(16)):
                if key[k, index].X == 1:
                    key_to_display[k, index] = 1
            
            for round, sbox in product(range(round_number-1), range(16)):
                if sbox_layer[round, sbox, 1].X == 1:
                    sbox_to_display[round, sbox] = 2
                elif sbox_layer[round, sbox, 2].X == 1:
                    sbox_to_display[round, sbox] = 4
                elif sbox_layer[round, sbox, 3].X == 1:
                    sbox_to_display[round, sbox] = 6

            return([True, state_to_display, key_to_display, sbox_to_display, active_sbox.getValue()])

        else :
            model.computeIIS()
            model.write("model_infeasible.ilp")
            return([False])

attaque = diff_gift(8)
if attaque[0]:
    print("63 62 61 60  59 58 57 56  55 54 53 52  51 50 49 48  47 46 45 44  43 42 41 40  39 38 37 36  35 34 33 32  31 30 29 28  27 26 25 24  23 22 21 20  19 18 17 16  15 14 13 12  11 10  9  8   7  6  5  4   3  2  1  0\n")
    r = 0
    for round in attaque[1]:
        c = 0
        for step in round:
            b=0
            for bit in step:
                if bit == 1:
                    print(f"\033[94m {bit} ", end="")
                else :
                    print(f"\033[90m {bit} ", end="")
                b+=1
                if b==4:
                    print("|", end="")
                    b=0
            if c == 1 :
                print("")
                for index in range(8):
                    print("      ", end="")
                    if attaque[2][2*(r%4)][(2*index+12*(r//4))%16] == 1:
                        print("\033[91m 1 ", end="")
                    else :
                        print("\033[90m 0 ", end="")
                    if attaque[2][2*(r%4)][(2*index+1+12*(r//4))%16] == 1:
                        print("\033[91m 1 ", end="")
                    else :
                        print("\033[90m 0 ", end="")
                    print("|", end="")
                for index in range(8):
                    print("      ", end="")
                    if attaque[2][2*(r%4)+1][(2*index+2*(r//4))%16] == 1:
                        print("\033[91m 1 ", end="")
                    else :
                            print("\033[90m 0 ", end="")
                    if attaque[2][2*(r%4)+1][(2*index+1+2*(r//4))%16] == 1:
                            print("\033[91m 1 ", end="")
                    else :
                        print("\033[90m 0 ", end="")
                    print("|", end="")
                print (f"  {r}", end="")
                
            print("")
            c+=1
        print("")
        for element in attaque[3][r]:
            if element == 2:
                print(f"\033[97msbox p={element}/16 |", end="")
            if element == 4:
                print(f"\033[91msbox p={element}/16 |", end="")
            if element == 6:
                print(f"\033[95msbox p={element}/16 |", end="")
            if element == 0:
                print(f"\033[90msbox   p=1  |", end="")
        print("\n") 
        r +=1 

    print(attaque[2])
    print(f"Probabilité du distingueur : {attaque[4]}")
