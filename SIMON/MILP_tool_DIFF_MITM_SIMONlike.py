import numpy as np
import gurobipy as gp
from gurobipy import GRB
from itertools import product
import os
import shutil
import sys
import matplotlib.pyplot as plt
from matplotlib.patches import *
from matplotlib.widgets import *
import math

def diff_mitm_SIMON():
    #Please enter you gurobi licene API key here
    options = {
            "WLSACCESSID" : "58d21f89-b596-40cf-bd3e-52b062898036",
            "WLSSECRET" : "21c59555-2f72-4b43-a903-efbf7a725c2d",
            "LICENSEID" : 2534357 }
    
    with gp.Env(params=options) as env, gp.Model(env=env) as model:
        model.params.FeasibilityTol = 1e-9
        model.params.OptimalityTol = 1e-9
        model.setParam("OutputFlag", 1) 
        model.setParam("LogToConsole", 1)

        #------------------------------------------------#
        #for the model, red represent the upper part
        #while blue represent the lower part of the attack
        #------------------------------------------------#

        #SIMON parameters :
        print('Enter the size of the state :')
        state_size = int(input())
        print('Enter the size of the key :')
        key_size = int(input())
        print('Enter the size of the differential distinguisher :')
        distinguisher_size = int(input())
        print('Enter the probability of the differential distinguisher :')
        distinguisher_proba = float(input())
        print('Enter the quantity of active bits at the start of the distinguisher :')
        distinguisher_input_quantity = int(input())
        left_active_input =[]
        right_active_input =[]
        for input_value in range(distinguisher_input_quantity) :
                print("Enter the index of an active bit you didn't enter before :")
                active_bit= int(input())
                if active_bit < int(state_size/2):
                        left_active_input.append(active_bit)
                else :
                        right_active_input.append(active_bit-int(state_size/2))

        print('Enter the quantity of active bits at the end of the distinguisher :')
        distinguisher_output_quantity = int(input())
        left_active_output =[]
        right_active_output =[]
        for input_value in range(distinguisher_output_quantity) :
                print("Enter the index of an active bit you didn't enter before :")
                active_bit= int(input())
                if active_bit < int(state_size/2):
                        left_active_output.append(active_bit)
                else :
                        right_active_output.append(active_bit-int(state_size/2))
        print('Enter the size of the structure :')
        structure_size = int(input())
        print('Enter the size of the upper part :')
        MITM_up_size = int(input())
        print('Enter the size of the lower part :')
        MITM_down_size = int(input())
        print('Enter the circular shift of the upper branch (For SIMON, it is 8, for SIMECK it is 0)')
        dec_up = int(input())
        print('Enter the circular shift of the middle branch (For SIMON, it is 1, for SIMECK it is 5)')
        dec_mid = int(input())
        print('Enter the circular shift of the lower branch (For SIMON, it is 2), for SIMECK it is 1')
        dec_down = int(input())
        print('Do you consider a linear key schedule ? type 1 for yes, 0 for no')
        key_schedule_linearity = int(input())
        print('Do you want to generate pdf figure of the attack ?')
        pdf_image = int(input())
        if pdf_image:
                print("enter a name for the pdf name")
                name = str(input())
        
        state_test = 1 #turn to 0 to prevent the model to do state tests
        proba_key_rec = 1 #turn to 0 to prevent the model to do probabilistic annulation in the key recovery

        state_size = int(state_size/2)
        subkey_size = state_size
        
        distinguisher_probability = math.ceil(distinguisher_proba)

        total_round = structure_size + MITM_up_size + distinguisher_size + MITM_down_size
        
        ### Variable Creation ###

        #Key
        key = np.zeros([total_round, subkey_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know]
        key_structure = np.zeros([structure_size, subkey_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = blue, 2=red]
        
        #structure
        structure_right1 = np.zeros([structure_size, state_size, 2, 3, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:blue/red/purple, 0:know/1:unknow]
        structure_left1 = np.zeros([structure_size, state_size, 2, 3, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:blue/red/purple, 0:know/1:unknow]
        structure_AND = np.zeros([structure_size, state_size, 2, 2, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:blue/red, 0:know/1:unknow]
        structure_right2 = np.zeros([structure_size, state_size, 2, 2, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:blue/red, 0:know/1:unknow]
        structure_left2 = np.zeros([structure_size, state_size, 2, 2, 2], dtype = object)#[round, bit index, 0:value/1:differences, 0:blue/, 0:know/1:unknow]
        filtered_difference = np.zeros([state_size, 2], dtype = object)#[bit index, 0:left state/1:right state]
        fix_state = np.zeros([state_size, 2], dtype = object)#[bit index, 0:not filtered/1:filtered]

        #up_state
        up_left_state = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
        up_right_state = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know]
        up_left_state_mid = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
        up_left_state_up = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
        up_left_state_down = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
        up_state_test_or = np.zeros([MITM_up_size, state_size, 2], dtype = object)
        
        #up_differences
        up_left_difference = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
        up_right_difference = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
        up_left_difference_AND = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no differences, 1 = unknow differences, 2 = probabilistic annulation]
        up_left_difference_XOR = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
        up_right_difference_XOR = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
        up_var_for_right_XOR_1 = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value: 1 if 1+1]
        up_var_for_right_XOR_0 = np.zeros([MITM_up_size, state_size, 2], dtype = object) #[round index, bit index, value: 0 if 0+0]

        #down_state
        down_left_state = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
        down_right_state = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know]
        down_left_state_mid = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
        down_left_state_up = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
        down_left_state_down = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value : 0 = unknow, 1 = know, 2 = state tested]
        down_state_test_or = np.zeros([MITM_down_size, state_size, 2], dtype = object)

        #down_differences
        down_left_difference = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
        down_right_difference = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
        down_left_difference_AND = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no differences, 1 = unknow differences, 2 = probabilistic annulation]
        down_left_difference_XOR = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
        down_right_difference_XOR = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round index, bit index, value : 0 = no difference, 1 = difference, 2 = unknown difference]
        down_var_for_right_XOR_1 = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value: 1 if 1+1]
        down_var_for_right_XOR_0 = np.zeros([MITM_down_size, state_size, 2], dtype = object) #[round index, bit index, value: 0 if 0+0]

        #propagation of the pseudo-linear and non linear equations in the upper part
        up_left_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        up_right_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        up_AND_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        up_right2_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        up_AND1_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        up_AND2_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        up_AND1_statetest_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        up_AND2_statetest_equation = np.zeros([MITM_up_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        
        down_left_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        down_right_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        down_AND_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        down_right2_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        down_AND_up_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        down_AND_mid_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        down_AND1_statetest_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        down_AND2_statetest_equation = np.zeros([MITM_down_size, state_size, 3], dtype = object) #[round, bit index, equation type : 0 = linear, 1 pseudo linear, 2 non linear]
        
        ### MILP Variable initialisation ###
        for round, bit, value in product(range(total_round), range(subkey_size), range(2)):
                key[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'key {round}, {bit} value ={value}')
        
        for  bit, value in product(range(state_size), range(2)):
                filtered_difference[bit, value] = model.addVar(vtype = GRB.BINARY, name = f'filtered_difference {bit} value ={value}')
                fix_state[bit, value] = model.addVar(vtype = GRB.BINARY, name = f'filtered_difference {bit} value ={value}')

        for round, bit, value in product(range(structure_size), range(subkey_size), range(3)):
                key_structure[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'key_structure {round}, {bit} value ={value}')
                
        for round, bit, state_type, activity in  product(range(structure_size), range(state_size), range(2), range(2)):
                for color in range(3):
                        structure_right1[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_right1 {round}, {bit}, state type:{state_type}, color:{color} : value = {activity}')
                        structure_left1[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_left1 {round}, {bit}state type:{state_type}, color:f{color} : value = {activity}')
                for color in range(2):
                        structure_AND[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_AND {round}, {bit}state type:{state_type}, color:{color} : value = {activity}')
                        structure_right2[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_right2 {round}, {bit}state type:{state_type}, color:{color} : value = {activity}')
                        structure_left2[round, bit, state_type, color, activity] = model.addVar(vtype = GRB.BINARY, name = f'structure_left2 {round}, {bit}state type:{state_type}, color:{color} : value = {activity}')

                
        for round, bit in product(range(MITM_down_size), range(state_size)): 
                for value in range(3):
                        down_left_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_equation{round}, {bit} : value = {value}')
                        down_right_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_right_equation{round}, {bit} : value = {value}')
                        down_AND_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND_equation{round}, {bit} : value = {value}')
                        down_right2_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_right2_equation{round}, {bit} : value = {value}')
                        down_AND_up_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND_up_equation{round}, {bit} : value = {value}')
                        down_AND_mid_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND_mid_equation{round}, {bit} : value = {value}')
                        down_AND1_statetest_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND1_statetest_equation{round}, {bit} : value = {value}')
                        down_AND2_statetest_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_AND2_statetest_equation{round}, {bit} : value = {value}')
                        
                        down_right_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_right difference {round}, {bit} : value = {value}')
                        down_left_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left difference {round}, {bit} : value = {value}')
                        down_left_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left difference_XOR {round}, {bit} : value = {value}')
                        down_right_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_right difference_XOR {round}, {bit} : value = {value}')

                        down_left_difference_AND[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left difference_AND {round}, {bit} : value = {value}')

                        down_left_state_up[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_up {round}, {bit} : value = {value}')
                        down_left_state_mid[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_mid {round}, {bit} : value = {value}')
                
                for value in range(2):
                        down_state_test_or[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_state_test_or {value} {bit} {value}')
                        down_right_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_right state {round}, {bit} : value = {value}')
                        down_left_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state {round}, {bit} : value = {value}')
                        down_left_state_down[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'down_left_state_down {round}, {bit} : value = {value}')
                        down_var_for_right_XOR_1[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_var_for_XOR_1 {round} {bit} {value}')
                        down_var_for_right_XOR_0[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'down_var_for_XOR_0 {round} {bit} {value}')
        
        for round, bit in product(range(MITM_up_size), range(state_size)): 
                for value in range(3):
                        up_left_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_equation{round}, {bit} : value = {value}')
                        up_right_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_right_equation{round}, {bit} : value = {value}')
                        up_AND_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND_equation{round}, {bit} : value = {value}')
                        up_right2_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_right2_equation{round}, {bit} : value = {value}')
                        up_AND1_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND1_equation{round}, {bit} : value = {value}')
                        up_AND2_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND2_equation{round}, {bit} : value = {value}')
                        up_AND1_statetest_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND1_statetest_equation{round}, {bit} : value = {value}')
                        up_AND2_statetest_equation[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_AND2_statetest_equation{round}, {bit} : value = {value}')
                        
                        up_right_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_right difference {round}, {bit} : value = {value}')
                        up_left_difference[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left difference {round}, {bit} : value = {value}')
                        up_left_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left difference_XOR {round}, {bit} : value = {value}')
                        up_right_difference_XOR[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_right difference_XOR {round}, {bit} : value = {value}')

                        up_left_difference_AND[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left difference_AND {round}, {bit} : value = {value}')

                        up_left_state_up[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_up {round}, {bit} : value = {value}')
                        up_left_state_mid[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_mid {round}, {bit} : value = {value}')
                
                for value in range(2):
                        up_state_test_or[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_state_test_or {round} {bit} {value}')
                        up_right_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_right state {round}, {bit} : value = {value}')
                        up_left_state[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state {round}, {bit} : value = {value}')
                        up_left_state_down[round, bit ,value] = model.addVar(vtype = GRB.BINARY, name = f'up_left_state_down {round}, {bit} : value = {value}')
                        up_var_for_right_XOR_1[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_var_for_XOR_1 {round} {bit} {value}')
                        up_var_for_right_XOR_0[round, bit, value] = model.addVar(vtype = GRB.BINARY, name = f'up_var_for_XOR_0 {round} {bit} {value}')
         

        #---------------------------------------------------------------------------------------------------------------------------------------
        #As we modelize the complexity as 2^x + 2^y 2^z, we cannot directly write it like this in MILP
        #We need to use a discret model, the following variables and constraints are used to build this discret model of the objective function 
        complexity = model.addVar(vtype= GRB.CONTINUOUS, name = "complexity")
        m_complexity = model.addVar(vtype= GRB.CONTINUOUS, name = "complexity")
        memory_complexity_up = model.addVar(lb = state_size, ub = key_size,vtype= GRB.INTEGER, name = "complexity_match")
        memory_complexity_down = model.addVar(lb = state_size, ub = key_size,vtype= GRB.INTEGER, name = "complexity_match")
        
        if state_size<=60 :
                time_complexity_up = model.addVar(lb = state_size, ub = 128,vtype= GRB.INTEGER, name = "complexity_up")
                time_complexity_down = model.addVar(lb = state_size, ub = 128,vtype= GRB.INTEGER, name = "complexity_down")
                time_complexity_match = model.addVar(lb = state_size, ub = 128,vtype= GRB.INTEGER, name = "complexity_match")
        
        else : 
                time_complexity_up = model.addVar(lb = state_size, ub = state_size*2,vtype= GRB.INTEGER, name = "complexity_up")
                time_complexity_down = model.addVar(lb = state_size, ub = state_size*2,vtype= GRB.INTEGER, name = "complexity_down")
                time_complexity_match = model.addVar(lb = state_size, ub = state_size*2,vtype= GRB.INTEGER, name = "complexity_match")

        search_domain = range(int(state_size), int(128))

        binary_time_complexity_up = {i: model.addVar(vtype=GRB.BINARY, name="binary_time_complexity_up_f{i}") for i in search_domain}
        binary_time_complexity_down = {i: model.addVar(vtype=GRB.BINARY, name="binary_time_complexity_up_f{i}") for i in search_domain}
        binary_time_complexity_match = {i: model.addVar(vtype=GRB.BINARY, name="binary_time_complexity_up_f{i}") for i in search_domain}
        binary_memory_complexity_up = {i: model.addVar(vtype=GRB.BINARY, name="binary_time_complexity_up_f{i}") for i in search_domain}
        binary_memory_complexity_down = {i: model.addVar(vtype=GRB.BINARY, name="binary_time_complexity_up_f{i}") for i in search_domain}
        #---------------------------------------------------------------------------------------------------------------------------------------
        
        #Objective function variables
        #Counting the key guessed in the attack 
        key_quantity_up = gp.quicksum(key[round, bit, 1] for round, bit in product(range(structure_size, structure_size + MITM_up_size), range(state_size))) + gp.quicksum(key_structure[round, bit, 2] for round, bit in product(range(structure_size), range(state_size)))
        key_quantity_down = gp.quicksum(key[round, bit, 1] for round, bit in product(range(structure_size + MITM_up_size + distinguisher_size, structure_size + MITM_up_size + distinguisher_size + MITM_down_size), range(state_size))) + gp.quicksum(key_structure[round, bit, 1] for round, bit in product(range(structure_size), range(state_size)))
        
        #counting the state test of the attack
        state_test_down_quantity = gp.quicksum(down_state_test_or[round, bit, 1] for round in range(MITM_down_size) for bit in range(state_size))
        state_test_up_quantity = gp.quicksum(up_state_test_or[round, bit, 1] for round in range(MITM_up_size) for bit in range(state_size))
        
        #counting the probabilist annulation of the attack
        probabilistic_key_recovery_down = gp.quicksum(down_left_difference_AND[round, bit, 2] for round, bit in product(range(MITM_down_size), range(state_size)))        
        probabilistic_key_recovery_up = gp.quicksum(up_left_difference_AND[round, bit, 2] for round, bit in product(range(MITM_up_size), range(state_size)))
        
        #counting the almost linear state test of the attack
        filtered_state_test_up = gp.quicksum(up_state_test_or[round, bit, 1]*(1-up_left_equation[round, bit, 2]) for round, bit in product(range(MITM_up_size), range(state_size)))
        filtered_state_test_down = gp.quicksum(down_state_test_or[round, bit, 1]*(1-down_right_equation[round, bit, 2]) for round, bit in product(range(MITM_down_size), range(state_size)))
        
        #Counting the filter trough the structure
        structure_fix = gp.quicksum(fix_state[bit, value] for bit in range(state_size) for value in range(2))
        structure_match_differences = gp.quicksum(filtered_difference[bit, value] for bit in range(state_size) for value in range(2)) - structure_fix
        
        if not state_test : #constraints to avoid state test
                model.addConstr(state_test_up_quantity == 0, name="State test limit")
                model.addConstr(state_test_down_quantity == 0, name="State test limit")

        if not proba_key_rec : #constraints to avoid probabilist annulation
                model.addConstr(probabilistic_key_recovery_up == 0, name = "probabilisitc key recovery limit")
                model.addConstr(probabilistic_key_recovery_down == 0, name = "probabilisitc key recovery limit")

        if key_schedule_linearity: #if the key schedule is linear we can filter the excessing key guess
                total_key_information = key_quantity_up + key_quantity_down + structure_match_differences + filtered_state_test_up + filtered_state_test_down - key_size
        else :
                total_key_information = 0 #if the key schedule is linear we cannot filter the excessing key guess and we need to ensure that we recover the full key after the attack
                key_information = key_quantity_up + key_quantity_down + structure_match_differences + filtered_state_test_up + filtered_state_test_down
                model.addConstr(key_information >= key_size)
        
        #Building the Objective function with the discrete model
        time_complexity_up =  key_quantity_up + state_test_up_quantity + probabilistic_key_recovery_down
        time_complexity_down =  key_quantity_down + state_test_down_quantity + probabilistic_key_recovery_up
        time_complexity_match =  key_quantity_up + key_quantity_down + state_test_up_quantity + state_test_down_quantity + 2*state_size -2*structure_fix- structure_match_differences - total_key_information
        
        memory_complexity_up = key_quantity_up + state_test_up_quantity - structure_fix
        memory_complexity_down = key_quantity_down + state_test_down_quantity + (state_size-structure_fix)
        
        if state_size <=60: # if state <120 we can use optimal search 
                model.addConstr(time_complexity_up == gp.quicksum(i * binary_time_complexity_up[i] for i in search_domain), name="link between binary and integer complexity up")
                model.addConstr(time_complexity_down == gp.quicksum(i * binary_time_complexity_down[i] for i in search_domain), name="link between binary and integer complexity down")
                model.addConstr(time_complexity_match == gp.quicksum(i * binary_time_complexity_match[i] for i in search_domain), name="link between binary and integer complexity match")
                model.addConstr(memory_complexity_up == gp.quicksum(i * binary_memory_complexity_up[i] for i in search_domain), name="link between binary and integer complexity match")
                model.addConstr(memory_complexity_down == gp.quicksum(i * binary_memory_complexity_down[i] for i in search_domain), name="link between binary and integer complexity match")
        
                model.addConstr(gp.quicksum(binary_time_complexity_up[i] for i in search_domain)==1, name="unique binary complexity up")
                model.addConstr(gp.quicksum(binary_time_complexity_down[i] for i in search_domain)==1, name="unique binary complexity down")
                model.addConstr(gp.quicksum(binary_time_complexity_match[i] for i in search_domain)==1, name="unique binary complexity match")
                model.addConstr(gp.quicksum(binary_memory_complexity_up[i] for i in search_domain)==1, name="unique binary complexity match")
                model.addConstr(gp.quicksum(binary_memory_complexity_down[i] for i in search_domain)==1, name="unique binary complexity match")

                model.addConstr(complexity == gp.quicksum((2**i)*(binary_time_complexity_up[i] + binary_time_complexity_down[i] + binary_time_complexity_match[i]) for i in search_domain), name="time complexity")
                model.addConstr(m_complexity <= gp.quicksum((2**i)*binary_memory_complexity_up[i] for i in search_domain), name="memory complexity up")
                model.addConstr(m_complexity <= gp.quicksum((2**i)*binary_memory_complexity_down[i] for i in search_domain), name="memory complexity down")


        else :
                model.addConstr(time_complexity_down <= complexity)
                model.addConstr(time_complexity_up <= complexity)
                model.addConstr(time_complexity_match <= complexity)
                model.addConstr(memory_complexity_up <= m_complexity)
                model.addConstr(memory_complexity_down <= m_complexity)

        #OBJECTIVE 
        model.setObjectiveN(complexity, 0, 10, abstol=1e-9)
        model.setObjectiveN(m_complexity, 1, 8, abstol=1e-9)
        #As we are not interest in doing a state that make us win only one key guess, 
        #we minimize the number of state test to ensure the model will not choose useless state test
        model.setObjectiveN(state_test_up_quantity+state_test_down_quantity,2, 5)
        
        #Constraints 

        #Global constraints
        model.addConstr(distinguisher_probability + probabilistic_key_recovery_down + probabilistic_key_recovery_up <= 2*state_size, "total probability of the attack cannot exceed the size of the state")

        ### STRUCTURE CONSTRAINTS ###
        #Structure is not considering the equivalent subkey techniques
        ### starting constraints
        for bit in range(state_size):
                #states and differences are known by blue at the start of the attack 
                model.addConstr(structure_right1[0, bit, 0, 0, 1]==1, name = "values at the start of the structure are known by the blue side")
                model.addConstr(structure_left1[0, bit, 0, 0, 1]==1, name = "values at the start of the structure are known by the blue side")
                model.addConstr(structure_right1[0, bit, 1, 0, 1]==1, name = "differences at the end of the structure are known by the red side")
                model.addConstr(structure_left1[0, bit, 1, 0, 1]==1, name = "differences at the end of the structure are known by the red side")

                #states and differences are known by red at the end of the attack 
                model.addConstr(structure_right2[structure_size-1, bit, 0, 1, 1]==1, name = "values at the end of the structure are known by the red side")
                model.addConstr(structure_left2[structure_size-1, bit, 0, 1, 1]==1, name = "values at the end of the structure are known by the red side")
                model.addConstr(structure_right2[structure_size-1, bit, 1, 1, 1]==1, name = "differences at the end of the structure are known by the red side")
                model.addConstr(structure_left2[structure_size-1, bit, 1, 1, 1]==1, name = "differences at the end of the structure are known by the red side")
        
        ### Value propagation in a round 
        for round, bit in product(range(structure_size), range(state_size)):
                #propagation of blue values (forward propagation)
                model.addConstr(structure_right2[round, bit, 0, 0, 1]==structure_left1[round, bit, 0, 0, 1], name="structure forward propagation of values inside a round")
                model.addConstr(structure_left2[round, bit, 0, 0 ,1] == gp.and_([key_structure[round, bit, 1], structure_right1[round, bit, 0, 0, 1], structure_left1[round, (bit-dec_down)%state_size, 0, 0, 1], structure_left1[round, (bit-dec_mid)%state_size, 0, 0, 1], structure_left1[round, (bit-dec_up)%state_size, 0, 0, 1]]), name="structure forward propagation of values inside a round")
                #red of red values (bacward propagation)
                model.addConstr(structure_left1[round, bit, 0, 1, 1]==structure_right2[round, bit, 0, 1, 1], name="structure backward propagation of values inside a round")
                model.addConstr(structure_right1[round, bit, 0, 1, 1]==gp.and_([key_structure[round, bit, 2], structure_left2[round, bit, 0, 1, 1], structure_right2[round, (bit-dec_down)%state_size, 0, 1, 1], structure_right2[round, (bit-dec_mid)%state_size, 0, 1, 1], structure_right2[round, (bit-dec_up)%state_size, 0, 1, 1]]), name="structure backward propagation of values inside a round")

        #State know by red and blue can be Fix, differences can be sieve
        for round, bit, state in product(range(structure_size), range(state_size), range(2)): 
                model.addConstr(structure_left1[round, bit, state, 2, 1]==gp.and_(structure_left1[round, bit, state, 1, 1], structure_left1[round, bit, state, 0, 1]), name="structure Fix bit activity")
                model.addConstr(structure_right1[round, bit, state, 2, 1]==gp.and_(structure_right1[round, bit, state, 1, 1], structure_right1[round, bit, state, 0, 1]), name="structure Fix bit activity")

        ###Difference propagation
        for round, bit in product(range(structure_size), range(state_size)):
                #propagation of blue differences (forward propagation)
                model.addConstr(structure_AND[round, bit, 1, 0, 1]==gp.and_(structure_left1[round, (bit-dec_mid)%state_size, 0, 0, 1], structure_left1[round, (bit-dec_up)%state_size, 0, 0, 1]), name="structure forward propagation of differences through AND")
                model.addConstr(structure_left2[round, bit, 1, 0, 1]==gp.and_([structure_left1[round, (bit-dec_down)%state_size, 1, 0, 1], structure_right1[round, bit, 1, 0, 1], structure_AND[round, bit, 1, 0, 1]]), name="structure forward propagation of differences through XOR")
                model.addConstr(structure_right2[round, bit, 1, 0, 1]==structure_left1[round, bit, 1, 0, 1], name="structure forward propagation of differences through XOR")
                #propagation of red differences (bacward propagation)
                model.addConstr(structure_AND[round, bit, 1, 1, 1]==gp.and_(structure_left1[round, (bit-dec_mid)%state_size, 0, 1, 1], structure_left1[round, (bit-dec_up)%state_size, 0, 1, 1]), name="structure bacward propagation of differences through AND")
                model.addConstr(structure_right1[round, bit, 1, 1, 1]==gp.and_([structure_left1[round, (bit-dec_down)%state_size, 1, 1, 1], structure_left2[round, bit, 1, 1, 1], structure_AND[round, bit, 1, 1, 1]]), name="structure backward propagation of differences through XOR")
                model.addConstr(structure_right2[round, bit, 1, 1, 1]==structure_left1[round, bit, 1, 1, 1], name="structure backward propagation of differences through XOR")
        
        #blue state and differences propagation to next rounds
        for round, bit, state, color in product(range(structure_size-1), range(state_size), range(2), range(2)):
                model.addConstr(structure_left2[round, bit, state, color, 1]==structure_left1[round+1, bit, state, color, 1], name="forward propagation between round left2 = left1")
                model.addConstr(structure_right2[round, bit, state, color, 1]==structure_right1[round+1, bit, state, color, 1], name="forward propagation between round right2 = right1")

        for bit in range(state_size):
                model.addConstr(filtered_difference[bit, 0] == gp.or_([structure_left1[round, bit, 1, 2, 1] for round in range(0, structure_size, 2)],[structure_right1[round, bit, 1, 2, 1] for round in range(1, structure_size, 2)]), name = "difference match activity left state")    
                model.addConstr(filtered_difference[bit, 1] == gp.or_([structure_right1[round, bit, 1, 2, 1] for round in range(0, structure_size, 2)],[structure_left1[round, bit, 1, 2, 1] for round in range(1, structure_size, 2)]), name = "difference match activity right state")    
                model.addConstr(fix_state[bit, 0] == gp.or_([structure_left1[round, bit, 0, 2, 1] for round in range(0, structure_size, 2)],[structure_right1[round, bit, 0, 2, 1] for round in range(1, structure_size, 2)]), name ="Fix activity left state")    
                model.addConstr(fix_state[bit, 1] == gp.or_([structure_right1[round, bit, 0, 2, 1] for round in range(0, structure_size, 2)],[structure_left1[round, bit, 0, 2, 1] for round in range(1, structure_size, 2)]), name="Fix activity right state")    

    
        ### KEY RECOVERY up ###
        #This part consider the equivalent subkey technique
        #Distinguisher input
        for bit in range(state_size):
                if bit in right_active_input:
                        model.addConstr(up_right_difference[MITM_up_size-1, bit, 1] == 1, name = f"start disting 1 right ")
                else :
                        model.addConstr(up_right_difference[MITM_up_size-1, bit, 0] == 1, name = f"start disting 0 right")
                if bit in left_active_input:
                        model.addConstr(up_left_difference[MITM_up_size-1, bit, 1] == 1, name = f"start disting 1 left ")
                else :
                        model.addConstr(up_left_difference[MITM_up_size-1, bit, 0] == 1, name = f"start disting 0 left")

        #difference backward propagation in a round
        for round, bit in product(range(MITM_up_size), range(state_size)):
                #through AND
                model.addConstr(up_left_difference_AND[round, bit, 0] == gp.and_(up_right_difference[round, (bit+dec_mid)%state_size, 0], up_right_difference[round, (bit+dec_up)%state_size, 0]), name = f"up AND")

                #through XOR left 
                model.addConstr(up_left_difference_XOR[round, bit, 2] == gp.or_(up_left_difference_AND[round, bit, 1], up_right_difference[round, (bit+dec_down)%state_size, 2]), name = f"up XOR left propagation of ?")
                model.addConstr((up_right_difference[round, bit, 1] == 1) >> (up_left_difference_XOR[round, (bit-dec_down)%state_size, 0] == 0), name = f"up 1 => not 0")
                model.addConstr((up_left_difference_XOR[round, (bit-dec_down)%state_size, 1] == 1) >> (up_right_difference[round, bit, 0] == 0), name = f"up not 0 <= 1")

                #through XOR right
                model.addConstr(up_right_difference_XOR[round, bit, 2] == gp.or_(up_left_difference[round, bit, 2], up_left_difference_XOR[round, bit, 2]), name = f"up XOR right propagation of ?")
                model.addConstr(up_var_for_right_XOR_0[round, bit, 1] == gp.and_(up_left_difference_XOR[round, bit, 0], up_left_difference[round, bit, 0]), name = f"up var spe 0")
                model.addConstr(up_var_for_right_XOR_1[round, bit, 1] == gp.and_(up_left_difference_XOR[round, bit, 1], up_left_difference[round, bit, 1]), name = f"up var spe 0")
                model.addConstr(up_right_difference_XOR[round, bit, 0] == gp.or_(up_var_for_right_XOR_0[round, bit, 1], up_var_for_right_XOR_1[round, bit, 1]), name = f"up XOR right 0 form 0+0 or 1+1")

        #difference backward propagation between rounds
        for round, bit, value in product(range(1, MITM_up_size), range(state_size), range(3)):
                model.addConstr(up_left_difference[round-1, bit, value] == up_right_difference[round, bit, value], name = f"up L-1 = R_XOR")
                model.addConstr(up_right_difference[round-1, bit, value] == up_right_difference_XOR[round, bit, value], name = f"up R-1 = L")

        #link between Differential and State
        for round, bit in product(range(MITM_up_size), range(state_size)):
                #if a difference is not null, state in this other branch is known or state tested
                model.addConstr((up_right_difference[round, bit, 1] == 1) >> (up_left_state_mid[round, (bit-dec_up)%state_size, 0] == 0), name = f"up Link state-diff mid branch")
                model.addConstr((up_right_difference[round, bit, 1] == 1) >> (up_left_state_up[round, (bit-dec_mid)%state_size, 0] == 0), name = f"up Link state-diff up branch")
                model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_mid[round, (bit-dec_up)%state_size, 0] == 0), name = f"up Link state-diff mid branch")
                model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_up[round, (bit-dec_mid)%state_size, 0] == 0), name = f"up Link state-diff up branch")
                #state test can be perform only on known differences 
                model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_mid[round, (bit-dec_mid)%state_size, 2] == 0))
                model.addConstr((up_right_difference[round, bit, 2] == 1) >> (up_left_state_up[round, (bit-dec_up)%state_size, 2] == 0))

        #Forward State propagation in a round
        for round, bit in product(range(MITM_up_size), range(state_size)):
                model.addConstr((up_left_state[round, bit, 1] == 1) >> (up_left_state_down[round, bit, 1] == 1), name = f"forward state propagation down branch")
                model.addConstr((up_left_state[round, bit, 1] == 1) >> (up_left_state_up[round, bit, 1] == 1), name = f"forward state propagation up branch")
                model.addConstr((up_left_state[round, bit, 1] == 1) >> (up_left_state_mid[round, bit, 1] == 1), name = f"forward state propagation mid branch")

                model.addConstr((up_right_state[round, bit, 1] == 1) >> (up_left_state_mid[round, (bit-dec_mid)%state_size, 1]==1), name = f"forward state propagation mid branch")
                model.addConstr((up_right_state[round, bit, 1] == 1) >> (up_left_state_down[round, (bit-dec_down)%state_size, 1]==1), name = f"forward state propagation down branch")
                model.addConstr((up_right_state[round, bit, 1] == 1) >> (up_left_state_up[round, (bit-dec_up)%state_size, 1]==1), name = f"forward state propagation up branch")

                #This constraints avoid doing the same state on the mid and up branch to be counted as two state test, but as one
                model.addConstr(up_state_test_or[round, bit, 1] == gp.or_(up_left_state_up[round, (bit-dec_up)%state_size, 2], up_left_state_mid[round, (bit-dec_mid)%state_size, 2]), name="state_test_or_up")
        
        
        for round, bit in product(range(1,MITM_up_size), range(state_size)):
                #Forward State propagation between round
                model.addConstr((up_left_state_mid[round, bit, 1] == 1) >> (up_left_state[round-1, (bit+dec_mid)%state_size, 1] == 1), name = f"up state : L=R+1 <<1")
                model.addConstr((up_left_state_down[round, bit, 1] == 1) >> (up_left_state[round-1, (bit+dec_down)%state_size, 1] == 1), name = f"up state : L=R+1 <<2")
                model.addConstr((up_left_state_up[round, bit, 1] == 1) >> (up_left_state[round-1, (bit+dec_up)%state_size, 1] == 1), name = f"up state : L=R+1 <<8")
                model.addConstr((up_left_state[round, bit, 1] == up_right_state[round-1, bit, 1]), name = f"up state : R=L-1")
                #Key addition in a round (no key in the first round because of equivalent subkey technique)
                model.addConstr((up_left_state_mid[round, bit, 1] == 1) >> (key[structure_size + round, (bit+dec_mid)%state_size, 1] == 1), name = f"up Key state implication <<1")
                model.addConstr((up_left_state_up[round, bit, 1] == 1) >> (key[structure_size + round, (bit+dec_up)%state_size, 1] == 1), name = f"up Key state implication <<1")


        ### Key recovery DOWN ###
        
        #Distinguisher output
        for bit in range(state_size):
                if bit in left_active_output:
                        model.addConstr(down_left_difference[0, bit, 1] == 1, name = f"End disting 1 Left" )
                else : 
                        model.addConstr(down_left_difference[0, bit, 0] == 1, name = f"End disting 0 Left")
                if bit in right_active_output:
                        model.addConstr(down_right_difference[0, bit, 1] == 1, name = f"End disting 1 Right")
                else : 
                        model.addConstr(down_right_difference[0, bit, 0] == 1, name = f"End disting 0 Right")

        #Differential forward propagation in a round
        for round, bit  in product(range(MITM_down_size), range(state_size)):
                #AND rule : propagate a zero only if two zero, else propagate an unknow difference or a probabilistic annulation
                model.addConstr(down_left_difference_AND[round, bit, 0] == gp.and_(down_left_difference[round, (bit+dec_up)%state_size, 0], down_left_difference[round, (bit+dec_mid)%state_size, 0]), name = f"AND rule")

                #left_XOR : 0 only if two zeros, 1 only if 0 XOR 1, else case are necessarly unknown diff
                model.addConstr(down_left_difference_XOR[round, bit, 2] == gp.or_(down_left_difference_AND[round, bit, 1], down_left_difference[round, (bit+dec_down)%state_size, 2]), name = f"Left XOR propagation of ?")
                model.addConstr((down_left_difference[round, bit, 1] == 1) >> (down_left_difference_XOR[round, (bit-dec_down)%state_size, 0] == 0), name = f"Left XOR rule : 1 => not 0")
                model.addConstr((down_left_difference_XOR[round, bit, 1] == 1) >> (down_left_difference[round, (bit+dec_down)%state_size, 0] == 0), name = f"Left XOR rule : not 0 <= 1")
                
                #right XOR : 0 if 0+0 or 1+1, 1 if 0+1 or 1+0, 2 in all the other case
                model.addConstr(down_right_difference_XOR[round, bit, 2] == gp.or_(down_right_difference[round, bit, 2], down_left_difference_XOR[round, bit, 2]),name = f"Right XOR propagation of ?" )
                model.addConstr(down_var_for_right_XOR_1[round, bit, 1] == gp.and_(down_left_difference_XOR[round, bit, 1], down_right_difference[round, bit, 1]),name = f"Difference forward propagation")
                model.addConstr(down_var_for_right_XOR_0[round, bit, 1] == gp.and_(down_left_difference_XOR[round, bit, 0], down_right_difference[round, bit, 0]),name = f"Difference forward propagation" )
                model.addConstr(down_right_difference_XOR[round, bit, 0] == gp.or_(down_var_for_right_XOR_0[round, bit, 1], down_var_for_right_XOR_1[round, bit, 1]),name = f"Difference forward propagation" )
                
        #Differential forward propagation between rounds
        for round, bit, value in product(range(MITM_down_size-1), range(state_size), range(3)):
               model.addConstr(down_left_difference[round, bit, value] == down_right_difference[round+1, bit, value], name = f"Diff L=R+1 ")
               model.addConstr(down_right_difference_XOR[round, bit, value] == down_left_difference[round+1, bit, value], name = f"Diff R=L+1")
        
        #link between Differential and State
        for round, bit in product(range(MITM_down_size), range(state_size)):
                #if a difference, state is known or state tested
                model.addConstr((down_left_difference[round, bit, 1] == 1) >> (down_left_state_mid[round, (bit-dec_up)%state_size, 0] == 0), name = f"down Link state-diff <<1")
                model.addConstr((down_left_difference[round, bit, 1] == 1) >> (down_left_state_up[round, (bit-dec_mid)%state_size, 0] == 0), name = f"down Link state-diff <<8")
                model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_mid[round, (bit-dec_up)%state_size, 0] == 0), name = f"down Link state-diff <<1")
                model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_up[round, (bit-dec_mid)%state_size, 0] == 0), name = f"down Link state-diff <<8")
                #state test can be perform only on known differences 
                model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_mid[round, (bit-dec_mid)%state_size, 2] == 0), name='state test perform only on known differences')
                model.addConstr((down_left_difference[round, bit, 2] == 1) >> (down_left_state_up[round, (bit-dec_up)%state_size, 2] == 0), name='state test perform only on known differences')
        
        #State backward propagation inside a round
        for round, bit in product(range(MITM_down_size), range(state_size)):
                model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state_mid[round, bit, 1] == 1), name = f"down state : right to left mid branch")
                model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state_down[round, bit, 1] == 1), name = f"down state : right to left down branch")
                model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state_up[round, bit, 1] == 1), name = f"down state : right to left up branch")

                model.addConstr((down_left_state[round, bit, 1] == 1) >> (down_left_state_mid[round, (bit-dec_mid)%state_size, 1]==1), name = f"down left state propa mid branc")
                model.addConstr((down_left_state[round, bit, 1] == 1) >> (down_left_state_down[round, (bit-dec_down)%state_size, 1]==1), name = f"down left state propa down branch")
                model.addConstr((down_left_state[round, bit, 1] == 1) >> (down_left_state_up[round, (bit-dec_up)%state_size, 1]==1), name = f"down left state propa up branch")

                #This constraints avoid doing the same state on the mid and up branch to be counted as two state test, but as one
                model.addConstr(down_state_test_or[round, bit, 1] == gp.or_(down_left_state_up[round, (bit-dec_up)%state_size, 2], down_left_state_mid[round, (bit-dec_mid)%state_size, 2]), name="state_test_or_down")
        
        for round, bit in product(range(MITM_down_size-1), range(state_size)):
                #State backward propagation between round
                model.addConstr((down_left_state_mid[round, bit, 1] == 1) >> (down_right_state[round+1, (bit+dec_mid)%state_size, 1] == 1), name = f"down part state : L=R+1 mid branch")
                model.addConstr((down_left_state_down[round, bit, 1] == 1) >> (down_right_state[round+1, (bit+dec_down)%state_size, 1] == 1), name = f"down part state : L=R+1 down branch")
                model.addConstr((down_left_state_up[round, bit, 1] == 1) >> (down_right_state[round+1, (bit+dec_up)%state_size, 1] == 1), name = f"down part state : L=R+1 up branch")
                model.addConstr((down_right_state[round, bit, 1] == 1) >> (down_left_state[round+1, bit, 1] == 1), name = f"down state : R=L+1")
                #Key addition inside a round (not performed in the first round because of equivalent subkey technique)
                model.addConstr((down_left_state_mid[round, bit, 1] == 1) >> (key[structure_size + MITM_up_size + distinguisher_size + round, (bit+dec_mid)%state_size, 1] == 1), name = f"down part Key state implication mid branch")
                model.addConstr((down_left_state_up[round, bit, 1] == 1) >> (key[structure_size + MITM_up_size + distinguisher_size + round, (bit+dec_up)%state_size, 1] == 1), name = f"down part Key state implication up branch")
        
        ### Propagation of equations for the state test filtering ###
        
        ### up forward propagation
        
        #starting constraints : all the bit are linear
        for bit in range(state_size):
                model.addConstr(up_left_equation[1, bit, 0]==1, name="Linear starting constraints")
                model.addConstr(up_right_equation[1, bit, 0]==1, name="Linear starting constraints")
        
        #Forward propagation rules
        for round, bit in product(range(1, MITM_up_size), range(state_size)):
                
                model.addConstr(up_AND1_equation[round, bit, 0] == gp.and_(up_left_equation[round, (bit+dec_up)%state_size, 0], key[structure_size+round, (bit+dec_up)%state_size, 1]))
                model.addConstr(up_AND1_equation[round, bit, 2]==up_left_equation[round, (bit+dec_up)%state_size, 2])

                model.addConstr(up_AND1_statetest_equation[round, bit, 0]==gp.or_(up_AND1_equation[round, bit, 0], up_left_state_up[round, bit, 2]))
                model.addConstr((up_AND1_statetest_equation[round, bit, 1]==1)>>(up_AND1_equation[round, bit, 1]==1))
                model.addConstr((up_AND1_statetest_equation[round, bit, 2]==1)>>(up_AND1_equation[round, bit, 2]==1))

                model.addConstr(up_AND2_equation[round, bit, 0] == gp.and_(up_left_equation[round, (bit+dec_mid)%state_size, 0], key[structure_size+round, (bit+dec_mid)%state_size, 1]))
                model.addConstr(up_AND2_equation[round, bit, 2]==up_left_equation[round, (bit+dec_mid)%state_size, 2])

                model.addConstr(up_AND2_statetest_equation[round, bit, 0]==gp.or_(up_AND2_equation[round, bit, 0], up_left_state_mid[round, bit, 2]))
                model.addConstr((up_AND2_statetest_equation[round, bit, 1]==1)>>(up_AND2_equation[round, bit, 1]==1))
                model.addConstr((up_AND2_statetest_equation[round, bit, 2]==1)>>(up_AND2_equation[round, bit, 2]==1))
        
                model.addConstr((up_AND_equation[round, bit, 1] == 1) >> (up_AND1_statetest_equation[round, bit, 0] + up_AND2_statetest_equation[round, bit, 0] >=1))

                model.addConstr((up_AND_equation[round, bit, 2] == 1) >> (2*up_AND1_statetest_equation[round, bit, 2] + 2*up_AND2_statetest_equation[round, bit, 2] + up_AND1_statetest_equation[round, bit, 1] + up_AND2_statetest_equation[round, bit, 1] >=2))
               
                model.addConstr((up_AND2_statetest_equation[round, bit, 2] == 1) >> (up_AND_equation[round, bit, 2] == 1))
                model.addConstr((up_AND1_statetest_equation[round, bit, 2] == 1) >> (up_AND_equation[round, bit, 2] == 1))
                
                model.addConstr(up_AND_equation[round, bit, 0]==gp.and_(up_AND1_statetest_equation[round, bit, 0], up_AND2_statetest_equation[round, bit, 0]))
                
                model.addConstr(up_right2_equation[round, bit, 2]==gp.or_(up_right_equation[round, bit, 2], up_left_equation[round, (bit+dec_down)%state_size, 2], up_AND_equation[round, bit, 2]))
                model.addConstr(up_right2_equation[round, bit, 0]==gp.and_(up_right_equation[round, bit, 0], up_left_equation[round, (bit+dec_down)%state_size, 0], up_AND_equation[round, bit, 0]))

        #Forward propagation between rounds
        for round, bit, type_equation in product(range(1, MITM_up_size), range(state_size), range(3)):
                model.addConstr(up_right_equation[round, bit, type_equation] == up_left_equation[round-1, bit, type_equation], name="forward propagation of linearity between rounds")
                model.addConstr(up_left_equation[round, bit, type_equation] == up_right2_equation[round-1, bit, type_equation], name="forward propagation of linearity between rounds")

        ### down bacward propagation 
        
        #starting constraints
        for bit in range(state_size):
                model.addConstr(down_left_equation[MITM_down_size-2, bit, 0]==1)
                model.addConstr(down_right_equation[MITM_down_size-2, bit, 0]==1)

        #backward propagation rules
        for round, bit in product(range(MITM_down_size-1), range(state_size)):
                model.addConstr(down_AND_up_equation[round, bit, 0] == gp.and_(down_right_equation[round, (bit+dec_up)%state_size, 0], key[structure_size+MITM_up_size+distinguisher_size+round, (bit+dec_up)%state_size, 1]))
                model.addConstr(down_AND_up_equation[round, bit, 2]==down_right_equation[round, (bit+dec_up)%state_size, 2])

                model.addConstr(down_AND1_statetest_equation[round, bit, 0]==gp.or_(down_AND_up_equation[round, bit, 0], down_left_state_up[round, bit, 2]))
                model.addConstr((down_AND1_statetest_equation[round, bit, 1]==1)>>(down_AND_up_equation[round, bit, 1]==1))
                model.addConstr((down_AND1_statetest_equation[round, bit, 2]==1)>>(down_AND_up_equation[round, bit, 2]==1))

                model.addConstr(down_AND_mid_equation[round, bit, 0] == gp.and_(down_right_equation[round, (bit+dec_mid)%state_size, 0], key[structure_size+MITM_up_size+distinguisher_size+round, (bit+dec_mid)%state_size, 1]))
                model.addConstr(down_AND_mid_equation[round, bit, 2]==down_right_equation[round, (bit+dec_mid)%state_size, 2])

                model.addConstr(down_AND2_statetest_equation[round, bit, 0]==gp.or_(down_AND_mid_equation[round, bit, 0], down_left_state_mid[round, bit, 2]))
                model.addConstr((down_AND2_statetest_equation[round, bit, 1]==1)>>(down_AND_mid_equation[round, bit, 1]==1))
                model.addConstr((down_AND2_statetest_equation[round, bit, 2]==1)>>(down_AND_mid_equation[round, bit, 2]==1))
                
                model.addConstr(down_AND_equation[round, bit, 0]==gp.and_(down_AND1_statetest_equation[round, bit, 0], down_AND2_statetest_equation[round, bit, 0]))
                model.addConstr((down_AND2_statetest_equation[round, bit, 2] == 1) >> (down_AND_equation[round, bit, 2] == 1))
                
                model.addConstr((down_AND1_statetest_equation[round, bit, 2] == 1) >> (down_AND_equation[round, bit, 2] == 1))
                model.addConstr((down_AND_equation[round, bit, 2] == 1) >> (2*down_AND1_statetest_equation[round, bit, 2] + 2*down_AND2_statetest_equation[round, bit, 2] + down_AND1_statetest_equation[round, bit, 1] + down_AND2_statetest_equation[round, bit, 1] >=2))
               
                model.addConstr((down_AND_equation[round, bit, 1] == 1) >> (down_AND1_statetest_equation[round, bit, 0] + down_AND2_statetest_equation[round, bit, 0] >=1))
                model.addConstr(down_right2_equation[round, bit, 2]==gp.or_(down_left_equation[round, bit, 2], down_right_equation[round, (bit+dec_down)%state_size, 2], down_AND_equation[round, bit, 2]))
                model.addConstr(down_right2_equation[round, bit, 0]==gp.and_(down_left_equation[round, bit, 0], down_right_equation[round, (bit+dec_down)%state_size, 0], down_AND_equation[round, bit, 0]))

        #Backward propagation between rounds
        for round, bit, type_equation in product(range(MITM_down_size-1), range(state_size), range(3)):
                model.addConstr(down_right_equation[round, bit, type_equation] == down_right2_equation[round+1, bit, type_equation], name="backward propagation of linearity between rounds")
                model.addConstr(down_left_equation[round, bit, type_equation] == down_right_equation[round+1, bit, type_equation], name="backward propagation of linearity between rounds")
        
        
        ### unique value constraints : thoose constraints ensure, for exemple, that the value of a state is no known an unknown at the same time ###
        for round, bit, state in product(range(structure_size), range(state_size), range(2)):
                model.addConstr(gp.quicksum(key_structure[round, bit, key_color] for key_color in range(3)) == 1)
                for color in range(3):
                        model.addConstr(gp.quicksum(structure_left1[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_left1 color cannot be active and inactive")
                        model.addConstr(gp.quicksum(structure_right1[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_right1 cannot be active and inactive")
                for color in range(2):
                        model.addConstr(gp.quicksum(structure_right2[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_right2 cannot be active and inactive")
                        model.addConstr(gp.quicksum(structure_AND[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_AND cannot be active and inactive")
                        model.addConstr(gp.quicksum(structure_left2[round, bit, state, color, activity] for activity in range(2)) <= 1, name="structure_left2 cannot be active and inactive")

        for round, bit in product(range(MITM_down_size), range(state_size)):
                model.addConstr(gp.quicksum(down_state_test_or[round, bit, value] for value in range(2))==1)
                model.addConstr(gp.quicksum(down_left_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation left down')
                model.addConstr(gp.quicksum(down_right_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation right down')
                model.addConstr(gp.quicksum(down_right2_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation right2  down')
                model.addConstr(gp.quicksum(down_AND_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND down')
                model.addConstr(gp.quicksum(down_AND_up_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND1 down')
                model.addConstr(gp.quicksum(down_AND_mid_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND2 down')   
                model.addConstr(gp.quicksum(down_AND1_statetest_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND1 statetest down')
                model.addConstr(gp.quicksum(down_AND2_statetest_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND2 statetest down')   
                model.addConstr(gp.quicksum(down_left_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value down left difference")
                model.addConstr(gp.quicksum(down_left_difference_AND[round, bit, value] for value in range(3)) == 1, name = f"unique value down left difference AND")
                model.addConstr(gp.quicksum(down_left_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value down left difference XOR")
                model.addConstr(gp.quicksum(down_right_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value down right difference XOR ")
                model.addConstr(gp.quicksum(down_right_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value down right difference")
                model.addConstr(gp.quicksum(down_left_state[round, bit, value] for value in range(2)) == 1, name = f"unique value down left state")
                model.addConstr(gp.quicksum(down_left_state_mid[round, bit, value] for value in range(3)) == 1, name = f"unique value down left state")
                model.addConstr(gp.quicksum(down_left_state_up[round, bit, value] for value in range(3)) == 1, name = f"unique value down left state")
                model.addConstr(gp.quicksum(down_left_state_down[round, bit, value] for value in range(2)) == 1, name = f"unique value down left state")
                model.addConstr(gp.quicksum(down_right_state[round, bit, value] for value in range(2)) == 1, name = f"unique value down right state")
                model.addConstr(gp.quicksum(down_var_for_right_XOR_0[round, bit, value] for value in range(2)) == 1, name = f"unique value down_var_for_right_XOR_0")
                model.addConstr(gp.quicksum(down_var_for_right_XOR_1[round, bit, value] for value in range(2)) == 1, name = f"unique value down_var_for_right_XOR_1")
                
        for round, bit in product(range(MITM_up_size), range(state_size)):
                model.addConstr(gp.quicksum(up_state_test_or[round, bit, value] for value in range(2))==1)
                model.addConstr(gp.quicksum(up_left_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation left up')
                model.addConstr(gp.quicksum(up_right_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation right up')
                model.addConstr(gp.quicksum(up_right2_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation right2  up')
                model.addConstr(gp.quicksum(up_AND_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND up')
                model.addConstr(gp.quicksum(up_AND1_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND1 up')
                model.addConstr(gp.quicksum(up_AND2_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND2 up')   
                model.addConstr(gp.quicksum(up_AND1_statetest_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND1 statetest up')
                model.addConstr(gp.quicksum(up_AND2_statetest_equation[round, bit, equation_type] for equation_type in range(3)) == 1, name = f'unique equation AND2 statetest up')   
                model.addConstr(gp.quicksum(up_left_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value up left difference")
                model.addConstr(gp.quicksum(up_left_difference_AND[round, bit, value] for value in range(3)) == 1, name = f"unique value up left difference AND")
                model.addConstr(gp.quicksum(up_left_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value up left difference XOR")
                model.addConstr(gp.quicksum(up_right_difference_XOR[round, bit, value] for value in range(3)) == 1, name = f"unique value up right difference XOR ")
                model.addConstr(gp.quicksum(up_right_difference[round, bit, value] for value in range(3)) == 1, name = f"unique value up right difference")
                model.addConstr(gp.quicksum(up_left_state[round, bit, value] for value in range(2)) == 1, name = f"unique value up left state")
                model.addConstr(gp.quicksum(up_left_state_mid[round, bit, value] for value in range(3)) == 1, name = f"unique value up left state")
                model.addConstr(gp.quicksum(up_left_state_up[round, bit, value] for value in range(3)) == 1, name = f"unique value up left state")
                model.addConstr(gp.quicksum(up_left_state_down[round, bit, value] for value in range(2)) == 1, name = f"unique value up left state")
                model.addConstr(gp.quicksum(up_right_state[round, bit, value] for value in range(2)) == 1, name = f"unique value up right state")
                model.addConstr(gp.quicksum(up_var_for_right_XOR_0[round, bit, value] for value in range(2)) == 1, name = f"unique value up_var_for_right_XOR_0")
                model.addConstr(gp.quicksum(up_var_for_right_XOR_1[round, bit, value] for value in range(2)) == 1, name = f"unique value up_var_for_right_XOR_1")
                
        for round, bit in product(range(total_round), range(subkey_size)):
                model.addConstr(gp.quicksum(key[round, bit, value] for value in range(2)) == 1, name=f"key unique value")

        #Constraints only for display
        display_constraint = gp.quicksum(up_left_state_mid[round, bit, 1] + up_left_state_up[round, bit, 1] + up_left_state[round, bit, 1] for round in range(MITM_up_size) for bit in range(state_size)) + gp.quicksum(down_left_state_mid[round, bit, 1] + down_left_state_up[round, bit, 1] + down_left_state[round, bit, 1] for round in range(MITM_down_size) for bit in range(state_size))
        model.setObjectiveN(-1*display_constraint,3, 1)

        model.optimize()

        
        if model.Status != GRB.INFEASIBLE:
                #if the model is Feaible the best solution is displayed in the consol.
                print(" Non linearity propagation for states tests")
                for round in range(MITM_up_size):
                        for bit in range(state_size):
                                if up_state_test_or[round, bit, 1].X==1:
                                        print(f"\033[95m 0 ", end="")
                                else :
                                        print(f"\033[90m 0 ", end="")
                        print("")
                for round in range(MITM_down_size):
                        for bit in range(state_size):
                                if down_state_test_or[round, bit, 1].X==1:
                                        print(f"\033[95m 0 ", end="")
                                else :
                                        print(f"\033[90m 0 ", end="")
                        print("")
                for round in range(MITM_up_size):
                        print(f"\033[90m ROUND : {round}")
                        for bit in range(state_size):
                                couleur=0
                                if up_left_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif up_left_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif up_left_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L1     ", end="")
                        for bit in range(state_size):
                                couleur=0
                                if up_right_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif up_right_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif up_right_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m R1")
                        for bit in range(state_size):
                                if key[structure_size + round, (bit-dec_up)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + round, (bit-dec_up)%state_size, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_8    ", end="")
                        for bit in range(state_size):
                                if key[structure_size + round, (bit+dec_mid)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + round, (bit+dec_mid)%state_size, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_1")
                        for bit in range(state_size):
                                couleur=0
                                if up_AND1_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif up_AND1_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif up_AND1_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND1   ", end="")
                        for bit in range(state_size):
                                couleur=0
                                if up_AND2_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif up_AND2_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif up_AND2_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND2")
                        for bit in range(state_size):
                                couleur=0
                                if up_AND1_statetest_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif up_AND1_statetest_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif up_AND1_statetest_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND1   ", end="")
                        for bit in range(state_size):
                                couleur=0
                                if up_AND2_statetest_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif up_AND2_statetest_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif up_AND2_statetest_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND2")
                        for bit in range(state_size):
                                couleur=0
                                if up_AND_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif up_AND_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif up_AND_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND    ", end="")
                        for bit in range(state_size):
                                couleur=0
                                if up_right2_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif up_right2_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif up_right2_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m R2")
                print("Differential DISTINGUISHER")
                for round in range(MITM_down_size):
                        print(f"\033[90m ROUND : {round}")
                        for bit in range(state_size):
                                couleur=0
                                if down_AND_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif down_AND_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif down_AND_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND    ", end="")
                        for bit in range(state_size):
                                couleur=0
                                if down_right2_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif down_right2_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif down_right2_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m R2")
                        for bit in range(state_size):
                                couleur=0
                                if down_AND1_statetest_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif down_AND1_statetest_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif down_AND1_statetest_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND1   ", end="")
                        for bit in range(state_size):
                                couleur=0
                                if down_AND2_statetest_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif down_AND2_statetest_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif down_AND2_statetest_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND2")
                        for bit in range(state_size):
                                couleur=0
                                if down_AND_up_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif down_AND_up_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif down_AND_up_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND1   ", end="")
                        for bit in range(state_size):
                                couleur=0
                                if down_AND_mid_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif down_AND_mid_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif down_AND_mid_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m AND2")
                        for bit in range(state_size):
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-dec_up)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-dec_up)%state_size, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_8    ", end="")
                        for bit in range(state_size):
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit+dec_mid)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit+dec_mid)%state_size, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_1")
                        for bit in range(state_size):
                                couleur=0
                                if down_left_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif down_left_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif down_left_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L1     ", end="")
                        for bit in range(state_size):
                                couleur=0
                                if down_right_equation[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                elif down_right_equation[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m L ", end="")
                                elif down_right_equation[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m N ", end="")
                                else : print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m R1")            
                print("START of the attack")
                
                for round in range(structure_size):
                        print(f"\033[90m ROUND : {round}")
                        for bit in range(state_size):
                                if structure_left1[round, bit, 0, 2, 1].X == 1:
                                        couleur = 5
                                elif structure_left1[round, bit, 0, 1, 1].X == 1:
                                        couleur = 1
                                elif structure_left1[round, bit, 0, 0, 1].X == 1:
                                        couleur = 4
                                else : couleur = 0
                                if structure_left1[round, bit, 1, 2, 1].X == 1:
                                        print(f"\033[9{couleur}m D ", end="")
                                elif structure_left1[round, bit, 1, 1, 1].X == 1:
                                        print(f"\033[9{couleur}m r ", end="")
                                elif structure_left1[round, bit, 1, 0, 1].X == 1:
                                        print(f"\033[9{couleur}m b ", end="")
                                else : print(f"\033[9{couleur}m 0 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L1     ", end="")
                        for bit in range(state_size):
                                if structure_right1[round, bit, 0, 2, 1].X == 1:
                                        couleur = 5
                                elif structure_right1[round, bit, 0, 1, 1].X == 1:
                                        couleur = 1
                                elif structure_right1[round, bit, 0, 0, 1].X == 1:
                                        couleur = 4
                                else : couleur = 0
                                if structure_right1[round, bit, 1, 2, 1].X == 1:
                                        print(f"\033[9{couleur}m D ", end="")
                                elif structure_right1[round, bit, 1, 1, 1].X == 1:
                                        print(f"\033[9{couleur}m r ", end="")
                                elif structure_right1[round, bit, 1, 0, 1].X == 1:
                                        print(f"\033[9{couleur}m b ", end="")
                                else : print(f"\033[9{couleur}m 0 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m R1")
                        for bit in range(state_size):
                                couleur = 0
                                if structure_AND[round, bit, 1, 1, 1].X == 1:
                                        print(f"\033[9{couleur}m r ", end="")
                                elif structure_AND[round, bit, 1, 0, 1].X == 1:
                                        print(f"\033[9{couleur}m b ", end="")
                                else : print(f"\033[9{couleur}m 0 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m A     ", end="")
                        for bit in range(state_size):
                                if key_structure[round, bit, 0].X == 1:
                                        print(f"\033[90m □ ", end="")
                                elif key_structure[round, bit, 1].X == 1:
                                        print(f"\033[94m □ ", end="")
                                elif key_structure[round, bit, 2].X == 1:
                                        print(f"\033[91m □ ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_1")
                        for bit in range(state_size):
                                if structure_left2[round, bit, 0, 1, 1].X == 1 and structure_left2[round, bit, 0, 0, 1].X == 1:
                                        couleur = 5
                                elif structure_left2[round, bit, 0, 0, 1].X == 1:
                                        couleur = 4
                                elif structure_left2[round, bit, 0, 1, 1].X == 1:
                                        couleur = 1
                                else : couleur = 0
                                if structure_left2[round, bit, 1, 1, 1].X == 1:
                                        print(f"\033[9{couleur}m r ", end="")
                                elif structure_left2[round, bit, 1, 0, 1].X == 1:
                                        print(f"\033[9{couleur}m b ", end="")
                                else : print(f"\033[9{couleur}m 0 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L2     ", end="")
                        for bit in range(state_size):
                                if structure_right2[round, bit, 0, 1, 1].X == 1 and structure_right2[round, bit, 0, 0, 1].X == 1:
                                        couleur = 5
                                elif structure_right2[round, bit, 0, 0, 1].X == 1:
                                        couleur = 4
                                elif structure_right2[round, bit, 0, 1, 1].X == 1:
                                        couleur = 1
                                else : couleur = 0
                                if structure_right2[round, bit, 1, 1, 1].X == 1:
                                        print(f"\033[9{couleur}m r ", end="")
                                elif structure_right2[round, bit, 1, 0, 1].X == 1:
                                        print(f"\033[9{couleur}m b ", end="")
                                else : print(f"\033[9{couleur}m 0 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m r2")
                
                print("END OF THE STRUCTURE")
                for round in range(MITM_up_size):
                        print(f"\033[90m ROUND : {structure_size + round}")
                        for bit in range(state_size):
                                if key[structure_size + round, (bit-dec_up)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + round, (bit-dec_up)%state_size, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_8")
                        for bit in range(state_size):
                                couleur = 1*int(up_left_state_up[round, bit, 1].X) + 7*int(up_left_state_up[round, bit, 2].X)
                                if up_right_difference[round, (bit+dec_up)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_right_difference[round, (bit+dec_up)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_right_difference[round, (bit+dec_up)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("\033[90m||", end="")
                        print("\033[90m L_8     ", end="")
                        for bit in range(state_size):
                                if key[structure_size + round, bit, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + round, bit, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K")
                        for bit in range(state_size):
                                if key[structure_size + round, (bit+dec_mid)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + round, (bit+dec_mid)%state_size, 1].X == 1:
                                        print(f"\033[93m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_1")
                        for bit in range(state_size):
                                couleur = 1*int(up_left_state_mid[round, bit, 1].X) + 7*int(up_left_state_mid[round, bit, 2].X)
                                if up_right_difference[round, (bit+dec_mid)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_right_difference[round, (bit+dec_mid)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_right_difference[round, (bit+dec_mid)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("\033[90m||", end="")
                        print("\033[90m L_1     ", end="")
                        for bit in range(state_size):
                                couleur = 1*int(up_right_state[round, bit, 1].X)
                                if up_left_difference_AND[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_left_difference_AND[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if up_left_difference_AND[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m P ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_AND")
                        for bit in range(state_size):
                                couleur = 1*int(up_left_state_down[round, bit, 1].X)
                                if up_right_difference[round, (bit+dec_down)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_right_difference[round, (bit+dec_down)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_right_difference[round, (bit+dec_down)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_2     ", end="")
                        for bit in range(state_size):
                                couleur = 1*int(up_right_state[round, bit, 1].X)
                                if up_left_difference_XOR[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_left_difference_XOR[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_left_difference_XOR[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_XOR")
                        for bit in range(state_size):
                                couleur = 1*int(up_left_state[round, bit, 1].X)
                                if up_left_difference[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_left_difference[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_left_difference[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L       ", end="")
                        for bit in range(state_size):
                                couleur = 1*int(up_right_state[round, bit, 1].X)
                                if up_right_difference[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if up_right_difference[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if up_right_difference[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if bit in [3, 7, 11]:
                                        print ("||", end="")
                        print("\033[90m R")
                print("")
                print("DISTINGUISHER")
                print("")
                for round in range(MITM_down_size):
                        print(f"\033[90m ROUND : {structure_size + MITM_up_size + distinguisher_size + round}")
                        for bit in range(state_size):
                                couleur = 4*int(down_left_state[round, bit, 1].X)
                                if down_left_difference[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L       ", end="")
                        for bit in range(state_size):
                                couleur = 4*int(down_right_state[round, bit, 1].X)
                                if down_right_difference[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_right_difference[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_right_difference[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m R")
                        for bit in range(state_size):
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-dec_up)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-dec_up)%state_size, 1].X == 1:
                                        print(f"\033[96m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_8")
                        for bit in range(state_size):
                                couleur = 4*int(down_left_state_up[round, bit, 1].X) + 7*int(down_left_state_up[round, bit, 2].X)
                                if down_left_difference[round, (bit+dec_up)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference[round, (bit+dec_up)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference[round, (bit+dec_up)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_8     ", end="")
                        for bit in range(state_size):
                                if key[structure_size + MITM_up_size + distinguisher_size + round, bit, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + MITM_up_size + distinguisher_size + round, bit, 1].X == 1:
                                        print(f"\033[96m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K")
                        for bit in range(state_size):
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-dec_mid)%state_size, 0].X == 1:
                                        print(f"\033[90m 0 ", end="")
                                if key[structure_size + MITM_up_size + distinguisher_size + round, (bit-dec_mid)%state_size, 1].X == 1:
                                        print(f"\033[96m 1 ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m K_1")
                        for bit in range(state_size):
                                couleur = 4*int(down_left_state_mid[round, bit, 1].X) + 7*int(down_left_state_mid[round, bit, 2].X)
                                if down_left_difference[round, (bit+dec_mid)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference[round, (bit+dec_mid)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference[round, (bit+dec_mid)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_1     ", end="")
                        for bit in range(state_size):
                                couleur = 4*int(down_right_state[round, bit, 1].X)
                                if down_left_difference_AND[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference_AND[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if down_left_difference_AND[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m P ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_AND")
                        for bit in range(state_size):
                                couleur = 4*int(down_left_state_down[round, bit, 1].X)
                                if down_left_difference[round, (bit+dec_down)%state_size, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference[round, (bit+dec_down)%state_size, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference[round, (bit+dec_down)%state_size, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_2     ", end="")
                        for bit in range(state_size):
                                couleur = 4*int(down_right_state[round, bit, 1].X)
                                if down_left_difference_XOR[round, bit, 0].X == 1:
                                        print(f"\033[9{couleur}m 0 ", end="")
                                if down_left_difference_XOR[round, bit, 1].X == 1:
                                        print(f"\033[9{couleur}m 1 ", end="")
                                if down_left_difference_XOR[round, bit, 2].X == 1:
                                        print(f"\033[9{couleur}m ? ", end="")
                                if (bit+1)%4 == 0 :
                                        print ("||", end="")
                        print("\033[90m L_XOR")

                print("MILP complexity : ", complexity.X)
                print("--- UP part parameters ---")
                print("key : ", key_quantity_up.getValue())
                print("state test: ", state_test_up_quantity.getValue())
                print("filtered state test", filtered_state_test_up.getValue())
                print("proba key rec : ", probabilistic_key_recovery_up.getValue())
                print('complexity = ', time_complexity_up.getValue()+distinguisher_proba)
                print("")
                print("--- DOWN values ---")
                print("key : ", key_quantity_down.getValue())
                print("state test : ", state_test_down_quantity.getValue())
                print("filtered state test", filtered_state_test_down.getValue())
                print("proba key rec : ", probabilistic_key_recovery_down.getValue())
                print('complexity = ', time_complexity_down.getValue()+distinguisher_proba)
                print("")
                print("--- MATCH and Structure ---")
                print("fix number", structure_fix.getValue())
                print("filtered differences", structure_match_differences.getValue())
                if key_schedule_linearity == 1:
                        print("key quantity", total_key_information.getValue())
                if key_schedule_linearity == 0:
                        print("key quantity", key_quantity_up.getValue() + key_quantity_down.getValue() + filtered_state_test_down.getValue() + filtered_state_test_up.getValue() + structure_match_differences.getValue())
                print("complexite match", time_complexity_match.getValue()+distinguisher_proba)
                print("")
                print("Final time complexity :", math.log2(pow(2,time_complexity_up.getValue()+distinguisher_proba) + pow(2,time_complexity_down.getValue()+distinguisher_proba) + pow(2,time_complexity_match.getValue()+distinguisher_proba)))
                print("Final memory complexity :", min(key_quantity_up.getValue() + state_test_up_quantity.getValue() +2*state_size - structure_fix.getValue(), key_quantity_down.getValue() + state_test_down_quantity.getValue() +2*state_size - structure_fix.getValue()))
                print("Final data complexity :", distinguisher_proba + probabilistic_key_recovery_up.getValue() + probabilistic_key_recovery_down.getValue())
                print("")
                
                #Generation of the matplotib image if require :
                if pdf_image ==1 :
                        mult = 1

                        font_decallage = 4
                        font_etat = 6
                        font_legende = 8
                        font_difference = 4
                        font_text = 8

                        if 2*state_size == 128 :
                                font_decallage = 2
                                font_etat = 4
                                font_legende = 6
                                font_difference = 3
                                font_text = 5.5
                
                        plt.rcParams['lines.linewidth'] = 0.1
                        plt.rcParams.update({'font.size': font_etat})

                        r_up_max = structure_size+MITM_up_size
                        r_up_min = structure_size

                        r_down_max = MITM_down_size
                        r_down_min = 0

                        taille_distingueur = distinguisher_size
                        proba_distingueur = distinguisher_probability

                        if state_size in [8, 16]:
                                state_draw = 16
                        elif state_size in [32, 64, 128]:
                                state_draw = 32
                        elif state_size in [12, 24, 48, 96]:
                                state_draw = 24
                        else : 
                                print("wrong state size")
                                state_draw = 0

                        n_s = int(state_size//state_draw)
                        
                        x_min, x_max = -7*mult, (state_draw*2+0.1*(state_draw//4-1)+10+7)*mult
                        y_min, y_max = min((r_up_max)*(-6*n_s-11)*mult, ((r_down_max)*(-6*n_s-11)-28)*mult), 1
                        
                        fig = plt.figure()
                        draw = fig.add_subplot()
                        draw.set_aspect('equal', adjustable='box')

                        #Strucutre : 
                        for r in range(0, structure_size):
                                dec_r=(-1*r)*(-6*n_s-11)
                                for k in range(4):
                                        #trait haut gauche 
                                        plt.plot([(-6)*mult, (-6)*mult],[(0-n_s/2 - dec_r)*mult,(-(5.75*n_s+5)-n_s/2 - dec_r)*mult], color="black")
                                        plt.plot([(-6)*mult,( state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult],[(-(6.25*n_s+5) - dec_r)*mult,( -(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                                        plt.plot([(-6)*mult,(-4)*mult], [(0-n_s/2-dec_r)*mult,(0-n_s/2-dec_r)*mult], color="black")
                                        plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult], [( -(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-5- dec_r)*mult], color="black")
                                        
                                        #trait haut droit
                                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+6)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult],[(0-n_s/2 - dec_r)*mult, (-(6.25*n_s+5) - dec_r)*mult], color="black")
                                        plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult, (-6+state_draw/2)*mult],[(-(6.25*n_s+5) - dec_r)*mult, (-(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+4)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult],[(0-n_s/2 - dec_r)*mult, (0-n_s/2 - dec_r)*mult], color="black")
                                        plt.plot([(-6+state_draw/2)*mult,(-6+state_draw/2)*mult], [( -(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-4-1 - dec_r)*mult], color="black")
                                        
                                        #text
                                        plt.text((-5.5)*mult, (-n_s*2.4 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                                        plt.text((-5.5)*mult, (-n_s*3.4-1 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)
                                        plt.text((-5.5)*mult, (-n_s*4.4-2 - dec_r)*mult, f"<<< {dec_down}", fontname="serif", fontsize=font_decallage)

                                        plt.text((state_draw+0.5-4)*mult, (-n_s/2-0.25 - dec_r)*mult, f"L{r}")
                                        plt.text((state_draw+13-1.5)*mult, (-n_s/2-0.25 - dec_r)*mult, f"R{r}", fontname="serif")
                                        plt.text((state_draw+7.5)*mult, (-3*n_s/2 - 1.5 - dec_r)*mult, f"K{r}", fontname="serif")


                                        #decallage des premiers etats
                                        if k==0 :
                                                dec_start = 4
                                        else : dec_start = 0

                                        for j in range(state_size//state_draw):
                                        
                                                for i in range(state_draw):
                                                        dec = 0
                                
                                                        #trait horizontaux millieu AND et XOR
                                                        if j%n_s ==0 and k in [1, 3]:
                                                                plt.plot([(state_draw)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                        if j%n_s ==0 and k in [3]:
                                                                plt.plot([(state_draw+5)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                        
                                                        if j%n_s ==0 and k in [2]:
                                                                plt.plot([(state_draw)*mult,(state_draw+4.5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                plt.plot([(state_draw+5.5)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")

                                                        #trait verticaux
                                                        if j%n_s ==0 and k in [1]:
                                                                plt.plot([(state_draw+5)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-2*n_s-2+0.5 - dec_r)*mult], color="black")
                                                        
                                                        if j%n_s ==0 and k in [2]:
                                                                plt.plot([(state_draw+5)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2-0.5 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1-0.5 - dec_r)*mult], color="black")

                                                        #cercle XOR et AND
                                                        if j%n_s ==0 and k in [2, 3]:
                                                                circle = plt.Circle(((state_draw+5)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)
                                                        
                                                        if j%n_s ==0 and k in [2]:
                                                                circle = plt.Circle(((state_draw+5)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.1)*mult, color = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)
                                                        
                                                        if j%n_s ==0 and k in [1, 2, 3]:
                                                                #trait horizontaux gauche
                                                                plt.plot([(-6)*mult,(0)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                #trait horizontaux droite
                                                        if j%n_s ==0 and k in [1, 3]:
                                                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6+0.5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                #cercle Xor droit
                                                                circle = plt.Circle(((state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)

                                                        #decalage tout les quatres etats
                                                        if i%4 == 0 and i!=0:
                                                                dec+=0.1
                                                        #Couleur Carré 
                                                        color_right = "white"
                                                        color_left = "white"
                                                        color="white"
                                                        #Carre état
                                                        if k==0:
                                                                if structure_left1[r, j*state_draw+i, 0, 2, 1].X ==1:
                                                                        color = "silver"
                                                                elif structure_left1[r, j*state_draw+i, 1, 2, 1].X==1:
                                                                        color = "lightgreen"
                                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square) 
                                                                color="white"
                                                                if structure_right1[r, j*state_draw+i, 0, 2, 1].X ==1:
                                                                        color = "silver"
                                                                square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square)
                                                        if k==1:
                                                                if structure_left1[r, ((j*state_draw+i)+8)%state_size, 0, 2, 1].X ==1:
                                                                        color = "silver"
                                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square) 
                                                                color="white"
                                                                if key_structure[r, j*state_draw+i, 1].X==1:
                                                                        color="dodgerblue"
                                                                if key_structure[r, j*state_draw+i, 2].X==1:
                                                                        color="red"
                                                                square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square)
                                                        if k==2:
                                                                if structure_left1[r, ((j*state_draw+i)+1)%state_size, 0, 2, 1].X ==1:
                                                                        color = "silver"
                                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square) 
                                                                color="white"
                                                                square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square)
                                                        if k==3:
                                                                if structure_left1[r, ((j*state_draw+i)+2)%state_size, 0, 2, 1].X ==1:
                                                                        color = "silver"
                                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square) 
                                                                color="white"
                                                                square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square)
                                                         
                                                

                        #UPPER PART
                        for r in range(r_up_min,r_up_max):
                                dec_r = (-1*r)*(-6*n_s-11)
                                for k in range(6):
                                        #trait haut gauche 
                                        plt.plot([(-6)*mult, (-6)*mult],[(0-n_s/2 - dec_r)*mult,(-(5.75*n_s+5)-n_s/2 - dec_r)*mult], color="black")
                                        plt.plot([(-6)*mult,( state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult],[(-(6.25*n_s+5) - dec_r)*mult,( -(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                                        plt.plot([(-6)*mult,(-4)*mult], [(0-n_s/2-dec_r)*mult,(0-n_s/2-dec_r)*mult], color="black")
                                        plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2)*mult], [( -(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-5- dec_r)*mult], color="black")
                                        
                                        #trait haut droit
                                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+6)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult],[(0-n_s/2 - dec_r)*mult, (-(6.25*n_s+5) - dec_r)*mult], color="black")
                                        plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult, (-6+state_draw/2)*mult],[(-(6.25*n_s+5) - dec_r)*mult, (-(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+4)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult],[(0-n_s/2 - dec_r)*mult, (0-n_s/2 - dec_r)*mult], color="black")
                                        plt.plot([(-6+state_draw/2)*mult,(-6+state_draw/2)*mult], [( -(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-4-1 - dec_r)*mult], color="black")
                                        
                                        #text
                                        plt.text((-5.5)*mult, (-n_s*2.4-2 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                                        plt.text((-5.5)*mult, (-n_s*4.4-4 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)
                                        plt.text((-5.5)*mult, (-n_s*5.4-5 - dec_r)*mult, f"<<< {dec_down}", fontname="serif", fontsize=font_decallage)

                                        if r!=r_up_min:
                                                plt.text((state_draw+0.5)*mult, (-n_s*1.4-1 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                                                plt.text((state_draw+0.5)*mult, (-n_s*3.4-3 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)

                                        plt.text((state_draw+0.5-4)*mult, (-n_s/2-0.25 - dec_r)*mult, f"L{r}")
                                        plt.text((state_draw+13-1)*mult, (-n_s/2-0.25 - dec_r)*mult, f"R{r}", fontname="serif")
                                        if r!=r_up_min:
                                                plt.text((2*state_draw+10.5)*mult, (-5*n_s/2 - 2 -0.25 - dec_r)*mult, f"K'{r}", fontname="serif")


                                        #decallage des premiers etats
                                        if k==0 :
                                                dec_start = 4
                                        else : dec_start = 0

                                        for j in range(state_size//state_draw):
                                        
                                                for i in range(state_draw):
                                                        dec = 0
                                                        #trait clé de gauche
                                                        if j%n_s ==0 and k in [1, 3] and r!=r_up_min:
                                                                #trait droite
                                                                plt.plot([(state_draw)*mult,(state_draw+8)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                                        
                                                                #traits gauche et XOR
                                                                plt.plot([(-2)*mult,0],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                plt.plot([(-2)*mult,(-2)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1.5 - dec_r)*mult], color="black")
                                                                circle = plt.Circle(((-2)*mult, (-1*j-(n_s+1)*k-n_s/2-n_s-1 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)

                                                        #trait millieu cle de droite
                                                        if j%n_s ==0 and k in [2] and r!=r_up_min:
                                                                plt.plot([(state_draw+8)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                                                plt.plot([(state_draw+8)*mult,(state_draw+8)*mult],[(-1*(j-1-n_s)-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*(j+1+n_s)-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                                        
                                                        #trait horizontaux millieu AND et XOR
                                                        if j%n_s ==0 and k in [2, 5]:
                                                                plt.plot([(state_draw)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                        if j%n_s ==0 and k in [5]:
                                                                plt.plot([(state_draw+5)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                        
                                                        if j%n_s ==0 and k in [4]:
                                                                plt.plot([(state_draw)*mult,(state_draw+4.5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                plt.plot([(state_draw+5.5)*mult,(state_draw+10+0.1*(state_draw//4 -1))*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")

                                                        #trait verticaux
                                                        if j%n_s ==0 and k in [2]:
                                                                plt.plot([(state_draw+5)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-2*n_s-2+0.5 - dec_r)*mult], color="black")
                                                        
                                                        if j%n_s ==0 and k in [4]:
                                                                plt.plot([(state_draw+5)*mult,(state_draw+5)*mult],[(-1*j-(n_s+1)*k-n_s/2-0.5 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1-0.5 - dec_r)*mult], color="black")

                                                        #cercle XOR et AND
                                                        if j%n_s ==0 and k in [4, 5]:
                                                                circle = plt.Circle(((state_draw+5)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)
                                                        
                                                        if j%n_s ==0 and k in [4]:
                                                                circle = plt.Circle(((state_draw+5)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.1)*mult, color = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)
                                                        
                                                        if j%n_s ==0 and k in [2, 4, 5]:
                                                                #trait horizontaux gauche
                                                                plt.plot([(-6)*mult,(0)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                #trait horizontaux droite
                                                        if j%n_s ==0 and k in [5]:
                                                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6+0.5)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                #cercle Xor droit
                                                                circle = plt.Circle(((state_draw*2+0.1*(state_draw//4 -1)+10+6)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)

                                                        #decalage tout les quatres etats
                                                        if i%4 == 0 and i!=0:
                                                                dec+=0.1
                                                        #Carre état
                                                        color_right="white"
                                                        color_left="white"
                                                        diff_value="0"
                                                        if r==r_up_min:
                                                                color_right="lightcoral"
                                                                color_left="lightcoral"
                                                        else :
                                                                if k == 0:
                                                                        if r != r_up_min +1 :
                                                                                if up_left_state[r-structure_size-2, j*state_draw+i, 1].X == 1:
                                                                                        color_right="lightcoral"
                                                                        else :
                                                                                color_right="lightcoral"
                                                                        if up_left_state[r-structure_size-1, j*state_draw+i, 1].X == 1:
                                                                                color_left="lightcoral"
                
                                                                if k == 1:
                                                                        if key[r, (j*state_draw+i+dec_up)%state_size, 1].X == 1:
                                                                                color_left="red"
                                                                if k == 2:
                                                                        if up_left_state_up[r-structure_size, j*state_draw+i, 1].X == 1:
                                                                                color_left="lightcoral"
                                                                        if up_state_test_or[r-structure_size, (j*state_draw+i+dec_up)%state_size, 1].X == 1:
                                                                                if up_left_equation[r-structure_size, (j*state_draw+i+dec_up)%state_size, 2].X == 1:
                                                                                        color_left="orange"
                                                                                else :
                                                                                        color_left="gold"
                                                                        if key[r, j*state_draw+i, 1].X == 1:
                                                                                color_right="red"
                                                                if k == 3:
                                                                        if key[r, (j*state_draw+i+dec_mid)%state_size, 1].X == 1:
                                                                                color_left="red"
                                                                if k == 4:
                                                                        if up_left_state_mid[r-structure_size, j*state_draw+i, 1].X == 1:
                                                                                color_left="lightcoral"
                                                                        if up_state_test_or[r-structure_size, (j*state_draw+i+dec_mid)%state_size, 1].X == 1:
                                                                                if up_left_equation[r-structure_size, (j*state_draw+i+dec_mid)%state_size, 2].X == 1:
                                                                                        color_left="orange"
                                                                                else :
                                                                                        color_left="gold"
                                                                        if up_left_state_up[r-structure_size, j*state_draw+i, 0].X == 0 and up_left_state_mid[r-structure_size, j*state_draw+i, 0].X==0:
                                                                                color_right="lightcoral"

                                                                if k == 5:
                                                                        if up_left_state_down[r-structure_size, j*state_draw+i, 1].X == 1:
                                                                                color_left="lightcoral"
                                                                        if up_left_state_up[r-structure_size, j*state_draw+i, 0].X == 0 and up_left_state_mid[r-structure_size, j*state_draw+i, 0].X==0 and up_left_state_down[r-structure_size, j*state_draw+i, 0].X==0:
                                                                                color_right="lightcoral"
                                                        if r!=r_up_min:
                                                                square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_left, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square)
                                                                if k not in [1,3]:  
                                                                        square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_right, edgecolor = "black", linewidth=0.1)
                                                                        draw.add_patch(square)
                                                        else :
                                                                if k not in [1,3]: 
                                                                        square = Rectangle(((i+dec-dec_start)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_left, edgecolor = "black", linewidth=0.1)
                                                                        draw.add_patch(square)
                                                                if k not in [1,2,3]:  
                                                                        square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_right, edgecolor = "black", linewidth=0.1)
                                                                        draw.add_patch(square)
                                                        if k == 0:
                                                                if up_right_difference[r-structure_size, j*state_draw+i, 1].X==1:
                                                                        diff_value="1"
                                                                elif up_right_difference[r-structure_size, j*state_draw+i, 2].X==1:
                                                                        diff_value="?"
                                                                plt.text((i+dec-dec_start+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"
                                                                if up_right_difference_XOR[r-structure_size, j*state_draw+i, 1].X==1:
                                                                        diff_value="1"
                                                                elif up_right_difference_XOR[r-structure_size, j*state_draw+i, 2].X==1:
                                                                        diff_value="?"
                                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"
                                                        if k == 2:
                                                                if up_right_difference[r-structure_size, (j*state_draw+i-8)%state_size, 1].X==1:
                                                                        diff_value="1"
                                                                elif up_right_difference[r-structure_size, (j*state_draw+i-8)%state_size, 2].X==1:
                                                                        diff_value="?"
                                                                plt.text((i+dec-dec_start+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"
                                                        if k == 4:
                                                                if up_right_difference[r-structure_size, (j*state_draw+i+dec_mid)%state_size,1].X==1:
                                                                        diff_value="1"
                                                                if up_right_difference[r-structure_size, (j*state_draw+i+dec_mid)%state_size,2].X==1:
                                                                        diff_value="?"
                                                                plt.text((i+dec-dec_start+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"
                                                                if up_left_difference_AND[r-structure_size, j*state_draw+i,1].X==1:
                                                                        diff_value="?"
                                                                if up_left_difference_AND[r-structure_size, j*state_draw+i,2].X==1:
                                                                        diff_value="P"
                                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"
                                                        if k == 5:
                                                                if up_right_difference[r-structure_size, (j*state_draw+i+dec_down)%state_size,1].X==1:
                                                                        diff_value="1"
                                                                if up_right_difference[r-structure_size, (j*state_draw+i+dec_down)%state_size,2].X==1:
                                                                        diff_value="?"
                                                                plt.text((i+dec-dec_start+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"
                                                                if up_left_difference_XOR[r-structure_size, j*state_draw+i,1].X==1:
                                                                        diff_value="1"
                                                                if up_left_difference_XOR[r-structure_size, j*state_draw+i,2].X==1:
                                                                        diff_value="?"
                                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"

                        #size control                                                      
                        fig.set_size_inches(8.27, 11.27)
                        #draw.set_aspect('equal')
                        plt.axis("off")
                        #plt.axis("equal")
                        draw.set_xlim(x_min, x_max)
                        draw.set_ylim(y_min, y_max)      
                        fig.savefig(f'{name}_up.pdf', format='pdf',  bbox_inches='tight', dpi=300)

                        fig = plt.figure()
                        draw = fig.add_subplot()
                        draw.set_aspect('equal', adjustable='box')

                        #LOWER PART AND DISTINGUISHER
                        dec_d = 0#10+state_draw*2+12+10
                        square = Rectangle(((dec_d)*mult, 0), (state_draw*2+10)*mult, (-4)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)
                        plt.text((dec_d+state_draw*0.5)*mult, -2.75*mult, f"{taille_distingueur}-rounds differential distinguisher", fontsize=font_text)
                        plt.plot([(4 + dec_d)*mult, (4 + dec_d)*mult],[-4*mult,-6*mult], color="black")
                        plt.plot([(4 + dec_d+1.5*state_draw+10+0.4)*mult, (4 + dec_d+1.5*state_draw+10+0.4)*mult],[-4*mult,-6*mult], color="black")
                                
                        for r in range(r_down_min,r_down_max):
                                dec_r = (-1*r)*(-6*n_s-11)+6
                                for k in range(6):
                                        #trait haut gauche 
                                        plt.plot([(-6 + dec_d)*mult, (-6 + dec_d)*mult],[(0-n_s/2 - dec_r)*mult,(-(5.75*n_s+5)-n_s/2 - dec_r)*mult], color="black")
                                        plt.plot([(-6 + dec_d)*mult,(-4 + dec_d)*mult], [(0-n_s/2-dec_r)*mult,(0-n_s/2-dec_r)*mult], color="black")    
                                        if r!=r_down_max-1:
                                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2 + dec_d)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2 + dec_d)*mult], [(-(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-5- dec_r)*mult], color="black")
                                                plt.plot([(-6 + dec_d)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6-state_draw/2 + dec_d)*mult],[(-(6.25*n_s+5) - dec_r)*mult,( -(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                                        
                                        #trait haut droit
                                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+6 + dec_d)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6 + dec_d)*mult],[(0-n_s/2 - dec_r)*mult, (-(6.25*n_s+5) - dec_r)*mult], color="black")
                                        plt.plot([(state_draw*2+0.1*(state_draw//4-1)+10+4 + dec_d)*mult, (state_draw*2+0.1*(state_draw//4 -1)+10+6 + dec_d)*mult],[(0-n_s/2 - dec_r)*mult, (0-n_s/2 - dec_r)*mult], color="black")    
                                        if r!=r_down_max-1:
                                                plt.plot([(-6+state_draw/2 + dec_d)*mult,(-6+state_draw/2 + dec_d)*mult], [(-(6.25*n_s+5)-4 - dec_r)*mult,(-6*n_s-6-5 - dec_r)*mult], color="black")
                                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10+6 + dec_d)*mult, (-6+state_draw/2 + dec_d)*mult],[(-(6.25*n_s+5) - dec_r)*mult, (-(6.25*n_s+5)-4 - dec_r)*mult], color="black")
                                        
                                        #text
                                        plt.text((-5.5 + dec_d)*mult, (-n_s*2.4-2 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                                        plt.text((-5.5 + dec_d)*mult, (-n_s*4.4-4 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)
                                        plt.text((-5.5 + dec_d)*mult, (-n_s*5.4-5 - dec_r)*mult, f"<<< {dec_down}", fontname="serif", fontsize=font_decallage)

                                        if r!=r_down_max-1:
                                                plt.text((state_draw+0.5 + dec_d)*mult, (-n_s*1.4-1 - dec_r)*mult, f"<<< {dec_up}", fontname="serif", fontsize=font_decallage)
                                                plt.text((state_draw+0.5 + dec_d)*mult, (-n_s*3.4-3 - dec_r)*mult, f"<<< {dec_mid}", fontname="serif", fontsize=font_decallage)

                                        plt.text((state_draw+0.5-4 + dec_d)*mult, (-n_s/2-0.25 - dec_r)*mult, f"L{r+taille_distingueur+r_up_max}")
                                        plt.text((state_draw+13-2 + dec_d)*mult, (-n_s/2-0.25 - dec_r)*mult, f"R{r+taille_distingueur+r_up_max}", fontname="serif")
                                        if r!=r_down_max-1:
                                                plt.text((2*state_draw+10.5 + dec_d)*mult, (-5*n_s/2 - 2 -0.25 - dec_r)*mult, f"K'{r+taille_distingueur+r_up_max}", fontname="serif")


                                        #decallage des premiers etats
                                        if k==0 :
                                                dec_start = 4
                                        else : dec_start = 0

                                        for j in range(state_size//state_draw):
                                        
                                                for i in range(state_draw):
                                                        dec = 0
                                                        #trait clé de gauche
                                                        if j%n_s ==0 and k in [1, 3] and r!=r_down_max-1:
                                                                #trait droite
                                                                plt.plot([(state_draw + dec_d)*mult,(state_draw+8 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                                                
                                                                #traits gauche et XOR
                                                                plt.plot([(-2 + dec_d)*mult,(0 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                plt.plot([(-2 + dec_d)*mult,(-2 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1.5 - dec_r)*mult], color="black")
                                                                circle = plt.Circle(((-2 + dec_d)*mult, (-1*j-(n_s+1)*k-n_s/2-n_s-1 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)

                                                        #trait millieu cle de droite
                                                        if j%n_s ==0 and k in [2] and r!=r_down_max-1:
                                                                plt.plot([(state_draw+8 + dec_d)*mult,(state_draw+10+0.1*(state_draw//4 -1) + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                                                plt.plot([(state_draw+8 + dec_d)*mult,(state_draw+8 + dec_d)*mult],[(-1*(j-1-n_s)-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*(j+1+n_s)-(n_s+1)*k-n_s/2 - dec_r)*mult], color="gray", linestyle="dotted")
                                                        
                                                        #trait horizontaux millieu AND et XOR
                                                        if j%n_s ==0 and k in [2, 5]:
                                                                plt.plot([(state_draw + dec_d)*mult,(state_draw+5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                        if j%n_s ==0 and k in [5]:
                                                                plt.plot([(state_draw+5 + dec_d)*mult,(state_draw+10+0.1*(state_draw//4 -1) + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                        
                                                        if j%n_s ==0 and k in [4]:
                                                                plt.plot([(state_draw + dec_d)*mult,(state_draw+4.5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                plt.plot([(state_draw+5.5 + dec_d)*mult,(state_draw+10+0.1*(state_draw//4 -1) + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")

                                                        #trait verticaux
                                                        if j%n_s ==0 and k in [2]:
                                                                plt.plot([(state_draw+5 + dec_d)*mult,(state_draw+5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-2*n_s-2+0.5 - dec_r)*mult], color="black")
                                                        
                                                        if j%n_s ==0 and k in [4]:
                                                                plt.plot([(state_draw+5 + dec_d)*mult,(state_draw+5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2-0.5 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2-n_s-1-0.5 - dec_r)*mult], color="black")

                                                        #cercle XOR et AND
                                                        if j%n_s ==0 and k in [4, 5]:
                                                                circle = plt.Circle(((state_draw+5 + dec_d)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)
                                                        
                                                        if j%n_s ==0 and k in [4]:
                                                                circle = plt.Circle(((state_draw+5 + dec_d)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.1)*mult, color = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)
                                                        
                                                        if j%n_s ==0 and k in [2, 4, 5]:
                                                        #trait horizontaux gauche
                                                                plt.plot([(-6 + dec_d)*mult,(0 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                        #trait horizontaux droite
                                                        if j%n_s ==0 and k in [5]:
                                                                plt.plot([(state_draw*2+0.1*(state_draw//4 -1)+10 + dec_d)*mult,(state_draw*2+0.1*(state_draw//4 -1)+10+6+0.5 + dec_d)*mult],[(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult,(-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult], color="black")
                                                                #cercle Xor droit
                                                                circle = plt.Circle(((state_draw*2+0.1*(state_draw//4 -1)+10+6+dec_d)*mult, (-1*j-(n_s+1)*k-n_s/2 - dec_r)*mult), (0.5)*mult, facecolor="white", edgecolor = "black", linewidth = 0.1)
                                                                draw.add_patch(circle)
                                                        
                                                        #decalage tout les quatres etats
                                                        if i%4 == 0 and i!=0:
                                                                dec+=0.1
                                                        #Carre état
                                                        color_right="white"
                                                        color_left="white"
                                                        diff_value="0"
                                                        if r==r_down_max-1:
                                                                color_right="lightskyblue"
                                                                color_left="lightskyblue"
                                                        else :
                                                                if k == 0 and r!=r_down_max-1:
                                                                        if down_right_state[r, j*state_draw+i, 1].X == 1:
                                                                                color_right="lightskyblue"
                                                                        if r!= r_down_max-1:
                                                                                if down_right_state[r+1, j*state_draw+i, 1].X == 1:
                                                                                        color_left="lightskyblue"
                                                                        else :
                                                                                color_left="lightskyblue"
                                                                if k == 1:
                                                                        if key[r+taille_distingueur+r_up_max, (j*state_draw+i+dec_up)%state_size, 1].X == 1:
                                                                                color_left="dodgerblue"
                                                                if k == 2:
                                                                        if down_left_state_up[r, j*state_draw+i, 1].X == 1:
                                                                                color_left="lightskyblue"
                                                                        if down_state_test_or[r, (j*state_draw+i+dec_up)%state_size, 1].X == 1:
                                                                                if down_right_equation[r, (j*state_draw+i+dec_up)%state_size, 2].X==1:
                                                                                        color_left="mediumturquoise"
                                                                                else :
                                                                                        color_left="aquamarine"
                                                                        if key[r+taille_distingueur+r_up_max, j*state_draw+i, 1].X == 1:
                                                                                color_right="dodgerblue"
                                                                if k == 3:
                                                                        if key[r+taille_distingueur+r_up_max, (j*state_draw+i+dec_mid)%state_size, 1].X == 1:
                                                                                color_left="dodgerblue"
                                                                if k == 4:
                                                                        if down_left_state_mid[r, j*state_draw+i, 1].X == 1:
                                                                                color_left="lightskyblue"
                                                                        if down_state_test_or[r, (j*state_draw+i+dec_mid)%state_size, 1].X == 1:
                                                                                if down_right_equation[r, (j*state_draw+i+dec_mid)%state_size, 2].X==1:
                                                                                        color_left="mediumturquoise"
                                                                                else :
                                                                                        color_left="aquamarine"
                                                                        if down_left_state_up[r, j*state_draw+i, 0].X == 0 and down_left_state_mid[r, j*state_draw+i, 0].X==0:
                                                                                color_right="lightskyblue"

                                                                if k == 5:
                                                                        if down_left_state_down[r, j*state_draw+i, 1].X == 1:
                                                                                color_left="lightskyblue"
                                                                        if down_left_state_up[r, j*state_draw+i, 0].X == 0 and down_left_state_mid[r, j*state_draw+i, 0].X==0 and down_left_state_down[r, j*state_draw+i, 0].X==0:
                                                                                color_right="lightskyblue"
                                                        if r!=r_down_max-1:
                                                                square = Rectangle(((i+dec-dec_start + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_left, edgecolor = "black", linewidth=0.1)
                                                                draw.add_patch(square)
                                                                if k not in [1,3]:  
                                                                        square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_right, edgecolor = "black", linewidth=0.1)
                                                                        draw.add_patch(square)
                                                        else :
                                                                if k not in [1,3]: 
                                                                        square = Rectangle(((i+dec-dec_start + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_left, edgecolor = "black", linewidth=0.1)
                                                                        draw.add_patch(square)
                                                                if k not in [1,2,3]:  
                                                                        square = Rectangle(((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r)*mult), (1)*mult, (1)*mult, facecolor=color_right, edgecolor = "black", linewidth=0.1)
                                                                        draw.add_patch(square)
                                                        if k == 0:
                                                                if down_left_difference[r, j*state_draw+i,1].X==1:
                                                                        diff_value="1"
                                                                if down_left_difference[r, j*state_draw+i,2].X==1:
                                                                        diff_value="?"
                                                                plt.text((i+dec-dec_start+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"
                                                                if down_right_difference[r, j*state_draw+i,1].X==1:
                                                                        diff_value="1"
                                                                if down_right_difference[r, j*state_draw+i,2].X==1:
                                                                        diff_value="?"
                                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                        if k == 2:
                                                                if down_left_difference[r, (j*state_draw+i-8)%state_size,1].X==1:
                                                                        diff_value="1"
                                                                if down_left_difference[r, (j*state_draw+i-8)%state_size,2].X==1:
                                                                        diff_value="?"
                                                                plt.text((i+dec-dec_start+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                        if k == 4:
                                                                if down_left_difference[r, (j*state_draw+i+dec_mid)%state_size,1].X==1:
                                                                        diff_value="1"
                                                                if down_left_difference[r, (j*state_draw+i+dec_mid)%state_size,2].X==1:
                                                                        diff_value="?"
                                                                plt.text((i+dec-dec_start+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"
                                                                if down_left_difference_AND[r, j*state_draw+i,1].X==1:
                                                                        diff_value="?"
                                                                if down_left_difference_AND[r, j*state_draw+i,2].X==1:
                                                                        diff_value="P"
                                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                        if k == 5:
                                                                if down_left_difference[r, (j*state_draw+i+dec_down)%state_size,1].X==1:
                                                                        diff_value="1"
                                                                if down_left_difference[r, (j*state_draw+i+dec_down)%state_size,2].X==1:
                                                                        diff_value="?"
                                                                plt.text((i+dec-dec_start+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                                                                diff_value="0"
                                                                if down_left_difference_XOR[r, j*state_draw+i,1].X==1:
                                                                        diff_value="1"
                                                                if down_left_difference_XOR[r, j*state_draw+i,2].X==1:
                                                                        diff_value="?"
                                                                plt.text((dec_start + state_draw + 10 + i + 0.1*(state_draw//4 -1) + dec+0.2 + dec_d)*mult, (-1*j-(n_s+1)*k-1 - dec_r+0.2)*mult, diff_value, fontname="serif", fontsize=font_difference)
                        #Légende
                        dec_d=dec_d-6
                        #upper state
                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-6)*mult), (1)*mult, (1)*mult, facecolor="red", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)               
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-6)*mult, ": This key bit is guessed by the upper part of the attack", fontname="serif", fontsize=font_legende)

                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-8)*mult), (1)*mult, (1)*mult, facecolor="lightcoral", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)               
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-8)*mult, ": This state bit can be computed by the upper part of the attack", fontname="serif", fontsize=font_legende)

                        if state_test_up_quantity.getValue() != 0:
                                square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-10)*mult), (1)*mult, (1)*mult, facecolor="gold", edgecolor = "black", linewidth=0.1)
                                draw.add_patch(square)               
                                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-10)*mult, ": This state bit is guessed by the upper part of the attack,", fontname="serif", fontsize=font_legende)
                                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-12)*mult, "  it is used to sieve the candidates during the match", fontname="serif", fontsize=font_legende)
                                
                                if state_test_up_quantity.getValue() != filtered_state_test_up.getValue():
                                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-14)*mult), (1)*mult, (1)*mult, facecolor="orange", edgecolor = "black", linewidth=0.1)
                                        draw.add_patch(square)               
                                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-14)*mult, ": This state bit is guessed by the upper part of the attack,", fontname="serif", fontsize=font_legende)
                                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-16)*mult, "  it cannot be used in the match because of it's non linearity", fontname="serif", fontsize=font_legende)

                        #lower state
                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-18)*mult), (1)*mult, (1)*mult, facecolor="dodgerblue", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)               
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-18)*mult, ": This key bit is guessed by the lower part of the attack", fontname="serif", fontsize=font_legende)

                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-20)*mult), (1)*mult, (1)*mult, facecolor="lightskyblue", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)               
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-20)*mult, ": This state bit can be computed by the lower part of the attack", fontname="serif", fontsize=font_legende)

                        if state_test_down_quantity.getValue() != 0:
                                square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-22)*mult), (1)*mult, (1)*mult, facecolor="aquamarine", edgecolor = "black", linewidth=0.1)
                                draw.add_patch(square)               
                                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-22)*mult, ": This state bit is guessed by the lower part of the attack,", fontname="serif", fontsize=font_legende)
                                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-24)*mult, "  it is used to sieve the candidates during the match", fontname="serif", fontsize=font_legende)
                                
                                if state_test_down_quantity.getValue() != filtered_state_test_down.getValue() :
                                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-26)*mult), (1)*mult, (1)*mult, facecolor="deepskyblue", edgecolor = "black", linewidth=0.1)
                                        draw.add_patch(square)               
                                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-26)*mult, ": This state bit is guessed by the lower part of the attack", fontname="serif", fontsize=font_legende)
                                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-28)*mult, "  it cannot be used in the match because of it's non linearity", fontname="serif", fontsize=font_legende)
                                
                        #differences
                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-30)*mult), (1)*mult, (1)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square) 
                        plt.text((dec_d+0.2)*mult, ((r_down_max)*(-6*n_s-11)-30+0.2)*mult, "0", fontname="serif", fontsize=font_difference)              
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-30)*mult, ": The difference on this bit is 0", fontname="serif", fontsize=font_legende)

                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-32)*mult), (1)*mult, (1)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)               
                        plt.text((dec_d+0.2)*mult, ((r_down_max)*(-6*n_s-11)-32+0.2)*mult, "1", fontname="serif", fontsize=font_difference)              
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-32)*mult, ": The difference on this bit is 1", fontname="serif", fontsize=font_legende)

                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-34)*mult), (1)*mult, (1)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)               
                        plt.text((dec_d+0.2)*mult, ((r_down_max)*(-6*n_s-11)-34+0.2)*mult, "?", fontname="serif", fontsize=font_difference)              
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-34)*mult, ": The difference on this bit can be 0 or 1", fontname="serif", fontsize=font_legende)
                        
                        if probabilistic_key_recovery_down.getValue() + probabilistic_key_recovery_up.getValue() !=0 :
                                square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-36)*mult), (1)*mult, (1)*mult, facecolor="white", edgecolor = "black", linewidth=0.1)
                                draw.add_patch(square)               
                                plt.text((dec_d+0.2)*mult, ((r_down_max)*(-6*n_s-11)-36+0.2)*mult, "P", fontname="serif", fontsize=font_difference)              
                                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-36)*mult, ": The difference on this bit is considered 0 by probabilist propagation", fontname="serif", fontsize=font_legende)
                        
                        #structure
                        square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-38)*mult), (1)*mult, (1)*mult, facecolor="lightgreen", edgecolor = "black", linewidth=0.1)
                        draw.add_patch(square)               
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-38)*mult, ": The difference on this bit can be computed by the upper", fontname="serif", fontsize=font_legende)
                        plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-40)*mult, "  and lower part of the attack", fontname="serif", fontsize=font_legende)
                        
                        if structure_fix.getValue() != 0:
                                square = Rectangle(((dec_d)*mult,((r_down_max)*(-6*n_s-11)-42)*mult), (1)*mult, (1)*mult, facecolor="silver", edgecolor = "black", linewidth=0.1)
                                draw.add_patch(square)               
                                plt.text((dec_d+1.5)*mult, ((r_down_max)*(-6*n_s-11)-42)*mult, ": The value of this bit is fix", fontname="serif", fontsize=font_legende)
                        

                        #size control                                                      
                        fig.set_size_inches(8.27, 11.27)
                        plt.axis("off")
                        #plt.axis("equal")
                        draw.set_xlim(x_min, x_max)
                        draw.set_ylim(y_min, y_max)
                        fig.savefig(f'{name}_down', format='pdf',  bbox_inches='tight', dpi=300)

                        
        else : #if model is not feasible, return ISS file for debuging
                model.computeIIS()
                model.write("model_infeasible.ilp")
                return([False])

diff_mitm_SIMON()

