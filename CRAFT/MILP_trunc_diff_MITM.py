#Trunc diff MITM MILP model for CRAFT
import gurobipy as gp
from gurobipy import GRB
import numpy as np

def attack(structure_size, MITM_up_size, distinguisher_size, MITM_down_size):
    options = {
    "WLSACCESSID" : "11f688cc-42d0-4f22-861f-3126b776b700",
    "WLSSECRET" : "017dd5f9-e815-4929-9036-3d33abb3103c",
    "LICENSEID" : 2602460
    }
    with gp.Env(params=options) as env, gp.Model(env=env) as model:
        
        #CONSTRAINTS INITIALISATION
        total_round = structure_size + MITM_up_size + distinguisher_size + MITM_down_size

        structure_state = np.zeros([structure_size, 4, 4, 4, 5], dtype = "object") #[round, step, row, col , color]
        for round in range(structure_size):
            for step in range(4):
                for row in range(4):
                    for col in range(4):
                        for color in range(5):
                            structure_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"Structure state {round} {step} {row} {col} {color}")
                        model.addConstr(gp.quicksum(structure_state[round, step, row, col, color] for color in range(5)) == 1) #color constraints
        
        MITM_up_state = np.zeros([MITM_up_size, 4, 4, 4, 3], dtype = "object") #[round, step, row, col, color : 0=unknow 1=know 2 statetested]
        MITM_up_differential = np.zeros([MITM_up_size, 4, 4, 4, 3], dtype = "object") #[round, step, row, col, color : 0=zero 1=know 2 probabilisitc anulation]
        for round in range(MITM_up_size):
            for step in range(4):
                for row in range(4):
                    for col in range(4):
                        for color in range(3):
                            MITM_up_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM up state {round} {step} {row} {col} {color}")
                            MITM_up_differential[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM up differnential {round} {step} {row} {col} {color}")
                        model.addConstr(gp.quicksum(MITM_up_state[round, step, row, col, color] for color in range(3)) == 1) #color constraints
                        model.addConstr(gp.quicksum(MITM_up_differential[round, step, row, col, color] for color in range(3)) == 1) #color constraints


        distinguisher_differential = np.zeros([distinguisher_size, 4, 4, 4, 3], dtype = object) #[round, step, row, col , color : 0=null 1=know, 2=cancel]
        for round in range(distinguisher_size):
            for step in range(4):
                for row in range(4):
                    for col in range(4):
                        for color in range(3):
                            distinguisher_differential[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"distiguisher {round} {step} {row} {col} {color}")
                        model.addConstr(gp.quicksum(distinguisher_differential[round, step, row, col, color] for color in range(3)) == 1) # color constraints
        
        MITM_down_state = np.zeros([MITM_down_size, 4, 4, 4, 3], dtype = "object") #[round, step, row, col, color : 0=unknow 1=know 2 statetested]
        MITM_down_differential = np.zeros([MITM_down_size, 4, 4, 4, 3], dtype = "object") #[round, step, row, col, color : 0=zero 1=know 2 probabilisitc anulation]
        for round in range(MITM_down_size):
            for step in range(4):
                for row in range(4):
                    for col in range(4):
                        for color in range(3):
                            MITM_down_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM down state {round} {step} {row} {col} {color}")
                            MITM_down_differential[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM down differnential {round} {step} {row} {col} {color}")
                        model.addConstr(gp.quicksum(MITM_down_state[round, step, row, col, color] for color in range(3)) == 1) #color constraints
                        model.addConstr(gp.quicksum(MITM_down_differential[round, step, row, col, color] for color in range(3)) == 1) #color constraints
        
        key = np.zeros([total_round, 4, 4, 4], dtype = "object") #[round, row, col, color : 0=unknow 1=red 2=blue 3=purple]
        for round in range(total_round):
            for col in range(4):
                for row in range(4):
                    for color in range(4):
                        key[round, row, col ,color] = model.addVar(vtype = GRB.BINARY, name =f"key {round} {step} {row} {col} {color}")
                    model.addConstr(gp.quicksum(key[round, row, col, color] for color in range(4)) == 1) #color constraints

        key_odd = np.zeros([4,4,4], dtype = "object") #[row, col, color 0=unknow 1=red 2=blue 3=purple]
        key_even = np.zeros([4,4,4], dtype = "object")#[row, col, color 0=unknow 1=red 2=blue 3=purple]
        for row in range(4):
            for col in range(4):
                for color in range (4):
                    key_odd[row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"key odd {row} {col} {color}")
                    key_even[row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"key even {row} {col} {color}")
                model.addConstr(gp.quicksum(key_odd[row, col, color] for color in range(4)) == 1) #color constraints
                model.addConstr(gp.quicksum(key_even[row, col, color] for color in range(4)) == 1) #color constraints
        
        complexity_red = model.addVar(lb = 0.0, ub = 60.0,vtype= GRB.INTEGER, name = "complexite")
        complexity_blue = model.addVar(lb = 0.0, ub = 60.0,vtype= GRB.INTEGER, name = "complexite")
        complexity_match = model.addVar(lb = 0.0, ub = 60.0,vtype= GRB.INTEGER, name = "complexite")
        complexity = model.addVar(lb = 0.0, ub = 60.0,vtype= GRB.INTEGER, name = "complexite")

        #Optimisation function
        fix_number = gp.quicksum(structure_state[round, step, row, col, 4] for round in range(structure_size) for step in [1,2] for row in range(4) for col in range(4))

        state_test_up = gp.quicksum(MITM_up_state[round, 3, row, col, 2] for round in range(MITM_up_size) for row in range(4) for col in range(4))
        state_test_down = gp.quicksum(MITM_down_state[round, 0, row, col, 2] for round in range(MITM_down_size) for row in range(4) for col in range(4))

        proba_diff_up = gp.quicksum(MITM_up_differential[round, 0, row, col, 2] for round in range(MITM_up_size) for row in range(4) for col in range(4))
        proba_diff_down = gp.quicksum(MITM_down_differential[round, 1, row, col, 2] for round in range(MITM_down_size) for row in range(4) for col in range(4))

        red_key_guess = gp.quicksum(key_even[row, col, color] + key_odd[row, col, color] for row in range(4) for col in range(4) for color in [1,3])
        blue_key_guess = gp.quicksum(key_even[row, col, color] + key_odd[row, col, color] for row in range(4) for col in range(4) for color in [2,3])
        purple_key_guess = gp.quicksum(key_even[row, col, color] + key_odd[row, col, color] for row in range(4) for col in range(4) for color in [3])

        propa_distinguisher = gp.quicksum(distinguisher_differential[round, 1, row, col, 2] for round in range(distinguisher_size) for row in range(4) for col in range(4))
        end_distinguisher_zero = gp.quicksum(distinguisher_differential[distinguisher_size-1, 3, row, col, 0] for row in range(4) for col in range(4))
        start_distinguisher_active = gp.quicksum(distinguisher_differential[0, 0, row, col, 1] for row in range(4) for col in range(4))
        end_distinguisher_active = gp.quicksum(distinguisher_differential[distinguisher_size-1, 3, row, col, 1] for row in range(4) for col in range(4))

        red_complexity = propa_distinguisher + red_key_guess + state_test_down + end_distinguisher_active - start_distinguisher_active + proba_diff_up
        blue_complexity = propa_distinguisher + blue_key_guess + state_test_up + proba_diff_down
        if structure_size <= 1 :
            match_complexity = red_complexity + blue_complexity - purple_key_guess - 16 - fix_number
        if structure_size >= 2 :
            match_complexity = red_complexity + blue_complexity - purple_key_guess - fix_number
        
        model.addConstr(red_complexity <= complexity + complexity_red)
        model.addConstr(blue_complexity <= complexity + complexity_blue)
        model.addConstr(match_complexity <= complexity + complexity_match)

        model.setObjective(complexity + complexity_blue + complexity_red + complexity_match)
        model.ModelSense = GRB.MINIMIZE

        #Force proba key rec
        #model.addConstr(proba_diff_up >= 1)
        #model.addConstr(proba_diff_down >= 1)
        #model.addConstr(state_test_down>=1)
        #model.addConstr(state_test_up>=1)

        #Constraints
        #------------------------------------------------------------------------------------------------------------------------------------------
        ### KEY CONSTRAINTS ###
        #------------------------------------------------------------------------------------------------------------------------------------------
        # distributing odd and even key
        for row in range(4):
            for col in range(4):
                for color in range(4):
                    for round in range(0, total_round, 2):
                        model.addConstr(key[round, row, col, color] == key_even[row, col, color])
                    for round in range(1, total_round, 2):
                        model.addConstr(key[round, row, col, color] == key_odd[row, col, color])
        
        #------------------------------------------------------------------------------------------------------------------------------------------
        ###Structure ### 
        #------------------------------------------------------------------------------------------------------------------------------------------
        
        if structure_size >=1:
           
            model.addConstr(propa_distinguisher-start_distinguisher_active + proba_diff_up + proba_diff_down >= 16 - fix_number)
            model.addConstr(fix_number<=16)
            model.addConstr(fix_number>=1)
            
            #MC
            for round in range(structure_size-1):
                for col in range(4):
                    #unknow propagate to unknow
                    model.addConstr((structure_state[round, 0, 0, col, 0] == 0) >> (structure_state[round, 1, 0, col, 0] == 0))
                    model.addConstr((structure_state[round, 0, 1, col, 0] == 0) >> (structure_state[round, 1, 1, col, 0] == 0))
                    model.addConstr((structure_state[round, 0, 2, col, 0] == 0) >> (structure_state[round, 1, 2, col, 0] == 0))
                    model.addConstr((structure_state[round, 0, 2, col, 0] == 0) >> (structure_state[round, 1, 0, col, 0] == 0))
                    model.addConstr((structure_state[round, 0, 3, col, 0] == 0) >> (structure_state[round, 1, 3, col, 0] == 0))
                    model.addConstr((structure_state[round, 0, 3, col, 0] == 0) >> (structure_state[round, 1, 0, col, 0] == 0))
                    model.addConstr((structure_state[round, 0, 3, col, 0] == 0) >> (structure_state[round, 1, 1, col, 0] == 0))

                    #first line
                    #red element can't come from blue or unknow element
                    model.addConstr((structure_state[round, 1, 0, col, 1] == 1) >> (structure_state[round, 0, 0, col, 2] + structure_state[round, 0, 2, col, 2] + structure_state[round, 0, 3, col, 2] == 0))
                    model.addConstr((structure_state[round, 1, 0, col, 1] == 1) >> (structure_state[round, 0, 0, col, 0] + structure_state[round, 0, 2, col, 0] + structure_state[round, 0, 3, col, 0] == 0))
                    model.addConstr((structure_state[round, 1, 0, col, 1] == 1) >> (structure_state[round, 0, 0, col, 3] + structure_state[round, 0, 2, col, 3] + structure_state[round, 0, 3, col, 3] <= 2))

                    #blue element can't come from blue or unknow element
                    model.addConstr((structure_state[round, 1, 0, col, 2] == 1) >> (structure_state[round, 0, 0, col, 1] + structure_state[round, 0, 2, col, 1] + structure_state[round, 0, 3, col, 1] == 0))
                    model.addConstr((structure_state[round, 1, 0, col, 2] == 1) >> (structure_state[round, 0, 0, col, 0] + structure_state[round, 0, 2, col, 0] + structure_state[round, 0, 3, col, 0] == 0))
                    model.addConstr((structure_state[round, 1, 0, col, 2] == 1) >> (structure_state[round, 0, 0, col, 3] + structure_state[round, 0, 2, col, 3] + structure_state[round, 0, 3, col, 3] <= 2))

                    #purple element can come only from purple element
                    model.addConstr((structure_state[round, 1, 0, col, 3] == 1) >> (structure_state[round, 0, 0, col, 3] + structure_state[round, 0, 2, col, 3] + structure_state[round, 0, 3, col, 3] == 3))

                    #fix element must come from purple or red element 
                    model.addConstr((structure_state[round, 1, 0, col, 4] == 1) >> (structure_state[round, 0, 0, col, 0] + structure_state[round, 0, 2, col, 0] + structure_state[round, 0, 3, col, 0] == 0))
                    model.addConstr((structure_state[round, 1, 0, col, 4] == 1) >> (structure_state[round, 0, 0, col, 2] + structure_state[round, 0, 2, col, 2] + structure_state[round, 0, 3, col, 0] == 0))
                    
                    #second line
                    #red element can't come from blue or unknow element
                    model.addConstr((structure_state[round, 1, 1, col, 1] == 1) >> (structure_state[round, 0, 1, col, 2] + structure_state[round, 0, 2, col, 2]  == 0))
                    model.addConstr((structure_state[round, 1, 1, col, 1] == 1) >> (structure_state[round, 0, 1, col, 0] + structure_state[round, 0, 2, col, 0]  == 0))
                    model.addConstr((structure_state[round, 1, 1, col, 1] == 1) >> (structure_state[round, 0, 1, col, 3] + structure_state[round, 0, 2, col, 3]  <= 1))

                    #blue element can't come from blue or unknow element
                    model.addConstr((structure_state[round, 1, 1, col, 2] == 1) >> (structure_state[round, 0, 1, col, 1] + structure_state[round, 0, 2, col, 1] == 0))
                    model.addConstr((structure_state[round, 1, 1, col, 2] == 1) >> (structure_state[round, 0, 1, col, 0] + structure_state[round, 0, 2, col, 0] == 0))
                    model.addConstr((structure_state[round, 1, 1, col, 2] == 1) >> (structure_state[round, 0, 1, col, 3] + structure_state[round, 0, 2, col, 3] <= 1))

                    #purple element can come only from purple element
                    model.addConstr((structure_state[round, 1, 1, col, 3] == 1) >> (structure_state[round, 0, 1, col, 3] + structure_state[round, 0, 2, col, 3] == 2))

                    model.addConstr((structure_state[round, 1, 1, col, 4] == 1) >> (structure_state[round, 0, 1, col, 0] + structure_state[round, 0, 2, col, 0] == 0))
                    model.addConstr((structure_state[round, 1, 1, col, 4] == 1) >> (structure_state[round, 0, 1, col, 2] + structure_state[round, 0, 2, col, 2] == 0))

                    #third line
                    #red element can't come from blue or unknow element
                    model.addConstr((structure_state[round, 1, 2, col, 1] == 1) >> (structure_state[round, 0, 2, col, 2]  == 0))
                    model.addConstr((structure_state[round, 1, 2, col, 1] == 1) >> (structure_state[round, 0, 2, col, 0]  == 0))
                    model.addConstr((structure_state[round, 1, 2, col, 1] == 1) >> (structure_state[round, 0, 2, col, 3]  <= 0))

                    #blue element can't come from blue or unknow element
                    model.addConstr((structure_state[round, 1, 2, col, 2] == 1) >> (structure_state[round, 0, 2, col, 1] == 0))
                    model.addConstr((structure_state[round, 1, 2, col, 2] == 1) >> (structure_state[round, 0, 2, col, 0] == 0))
                    model.addConstr((structure_state[round, 1, 2, col, 2] == 1) >> (structure_state[round, 0, 2, col, 3] <= 0))

                    #purple element can come only from purple element
                    model.addConstr((structure_state[round, 1, 2, col, 3] == 1) >> (structure_state[round, 0, 2, col, 3] == 1))

                    model.addConstr((structure_state[round, 1, 2, col, 4] == 1) >> (structure_state[round, 0, 2, col, 0] == 0))
                    model.addConstr((structure_state[round, 1, 2, col, 4] == 1) >> (structure_state[round, 0, 2, col, 2] == 2))

                    #fourth line
                    #red element can't come from blue or unknow element
                    model.addConstr((structure_state[round, 1, 3, col, 1] == 1) >> (structure_state[round, 0, 3, col, 2]  == 0))
                    model.addConstr((structure_state[round, 1, 3, col, 1] == 1) >> (structure_state[round, 0, 3, col, 0]  == 0))
                    model.addConstr((structure_state[round, 1, 3, col, 1] == 1) >> (structure_state[round, 0, 3, col, 3]  <= 0))

                    #blue element can't come from blue or unknow element
                    model.addConstr((structure_state[round, 1, 3, col, 2] == 1) >> (structure_state[round, 0, 3, col, 1] == 0))
                    model.addConstr((structure_state[round, 1, 3, col, 2] == 1) >> (structure_state[round, 0, 3, col, 0] == 0))
                    model.addConstr((structure_state[round, 1, 3, col, 2] == 1) >> (structure_state[round, 0, 3, col, 3] <= 0))

                    #purple element can come only from purple element
                    model.addConstr((structure_state[round, 1, 3, col, 3] == 1) >> (structure_state[round, 0, 3, col, 3] == 1))

                    model.addConstr((structure_state[round, 1, 3, col, 4] == 1) >> (structure_state[round, 0, 3, col, 0] == 0))
                    model.addConstr((structure_state[round, 1, 3, col, 4] == 1) >> (structure_state[round, 0, 3, col, 2] == 2))
                    
            #AK
            for round in range(structure_size):
                for row in range(4):
                    for col in range(4):
                        #State is unknow if the key or the state before/after is unknow
                        
                        #key is unknow, state must ne unknow in one side
                        model.addConstr((key[round, row, col, 0] == 1) >> (structure_state[round, 1, row, col, 0] + structure_state[round, 2, row, col, 0] >=1 ))

                        #key is red we cannot have : blue <-> blue, purple <-> blue, fix <-> blue
                        model.addConstr((key[round, row, col, 1] == 1) >> (structure_state[round, 1, row, col, 2] + structure_state[round, 2, row, col, 2] <=1 ))
                        model.addConstr((key[round, row, col, 1] == 1) >> (structure_state[round, 1, row, col, 3] + structure_state[round, 2, row, col, 2] <=1 ))
                        model.addConstr((key[round, row, col, 1] == 1) >> (structure_state[round, 1, row, col, 2] + structure_state[round, 2, row, col, 3] <=1 ))
                        model.addConstr((key[round, row, col, 1] == 1) >> (structure_state[round, 1, row, col, 4] + structure_state[round, 2, row, col, 2] <=1 ))
                        model.addConstr((key[round, row, col, 1] == 1) >> (structure_state[round, 1, row, col, 2] + structure_state[round, 2, row, col, 4] <=1 ))

                        #key is blue we cannot have : red <-> red, purple <-> red, fix <-> red
                        model.addConstr((key[round, row, col, 2] == 1) >> (structure_state[round, 1, row, col, 1] + structure_state[round, 2, row, col, 1] <=1 ))
                        model.addConstr((key[round, row, col, 2] == 1) >> (structure_state[round, 1, row, col, 3] + structure_state[round, 2, row, col, 1] <=1 ))
                        model.addConstr((key[round, row, col, 2] == 1) >> (structure_state[round, 1, row, col, 1] + structure_state[round, 2, row, col, 3] <=1 ))
                        model.addConstr((key[round, row, col, 2] == 1) >> (structure_state[round, 1, row, col, 4] + structure_state[round, 2, row, col, 1] <=1 ))
                        model.addConstr((key[round, row, col, 2] == 1) >> (structure_state[round, 1, row, col, 1] + structure_state[round, 2, row, col, 4] <=1 ))

                        #key is red/blue, state cannot be purple to purple
                        model.addConstr((key[round, row, col, 1] == 1) >> (structure_state[round, 1, row, col, 4] + structure_state[round, 2, row, col, 4] + structure_state[round, 1, row, col, 3] + structure_state[round, 2, row, col, 3] <= 1))
                        model.addConstr((key[round, row, col, 2] == 1) >> (structure_state[round, 1, row, col, 4] + structure_state[round, 2, row, col, 4] + structure_state[round, 1, row, col, 3] + structure_state[round, 2, row, col, 3] <= 1))

                        #state is blue/red, next/previous cannot be red/blue
                        model.addConstr((structure_state[round, 1, row, col, 1] == 1) >> (structure_state[round, 2, row, col, 2] == 0))
                        model.addConstr((structure_state[round, 1, row, col, 2] == 1) >> (structure_state[round, 2, row, col, 1] == 0))

                        model.addConstr((structure_state[round, 2, row, col, 1] == 1) >> (structure_state[round, 1, row, col, 2] == 0))
                        model.addConstr((structure_state[round, 2, row, col, 2] == 1) >> (structure_state[round, 1, row, col, 1] == 0))

                        #key is purple, state around AK are the same
                        for color in [0, 1, 2]:
                            model.addConstr((key[round, row, col, 3] == 1) >> (structure_state[round, 2, row, col, color] == structure_state[round, 1, row , col, color]))

                        #state is fix, cant be unknow after or before AK for equation
                        
                        model.addConstr((structure_state[round, 1, row, col, 4] == 1) >> (structure_state[round, 2, row, col, 0] == 0))
                        model.addConstr((structure_state[round, 2, row, col, 4] == 1) >> (structure_state[round, 1, row, col, 0] == 0))
                        model.addConstr((structure_state[round, 1, row, col, 3] == 1) >> (structure_state[round, 2, row, col, 0] == 0))
                        model.addConstr((structure_state[round, 2, row, col, 3] == 1) >> (structure_state[round, 1, row, col, 0] == 0))
                        model.addConstr((structure_state[round, 1, row, col, 2] == 1) >> (structure_state[round, 2, row, col, 0] == 0))
                        model.addConstr((structure_state[round, 2, row, col, 2] == 1) >> (structure_state[round, 1, row, col, 0] == 0))
                        model.addConstr((structure_state[round, 1, row, col, 1] == 1) >> (structure_state[round, 2, row, col, 0] == 0))
                        model.addConstr((structure_state[round, 2, row, col, 1] == 1) >> (structure_state[round, 1, row, col, 0] == 0))
                        
                        #if fix on a side , dont fix on the other side
                        model.addConstr((structure_state[round, 1, row, col, 4] == 1) >> (structure_state[round, 2, row, col, 4] == 0))
                        model.addConstr((structure_state[round, 2, row, col, 4] == 1) >> (structure_state[round, 1, row, col, 4] == 0))
            
            #Permutation
            for round in range(structure_size):
                for color in range(3):
                    model.addConstr(structure_state[round, 2, 0, 0, color] == structure_state[round, 3, 3, 3, color])
                    model.addConstr(structure_state[round, 2, 0, 1, color] == structure_state[round, 3, 3, 0, color])
                    model.addConstr(structure_state[round, 2, 0, 2, color] == structure_state[round, 3, 3, 1, color])
                    model.addConstr(structure_state[round, 2, 0, 3, color] == structure_state[round, 3, 3, 2, color])

                    model.addConstr(structure_state[round, 2, 1, 0, color] == structure_state[round, 3, 2, 2, color])
                    model.addConstr(structure_state[round, 2, 1, 1, color] == structure_state[round, 3, 2, 1, color])
                    model.addConstr(structure_state[round, 2, 1, 2, color] == structure_state[round, 3, 2, 0, color])
                    model.addConstr(structure_state[round, 2, 1, 3, color] == structure_state[round, 3, 2, 3, color])
                            
                    model.addConstr(structure_state[round, 2, 2, 0, color] == structure_state[round, 3, 1, 2, color])
                    model.addConstr(structure_state[round, 2, 2, 1, color] == structure_state[round, 3, 1, 1, color])
                    model.addConstr(structure_state[round, 2, 2, 2, color] == structure_state[round, 3, 1, 0, color])
                    model.addConstr(structure_state[round, 2, 2, 3, color] == structure_state[round, 3, 1, 3, color])

                    model.addConstr(structure_state[round, 2, 3, 0, color] == structure_state[round, 3, 0, 1, color])
                    model.addConstr(structure_state[round, 2, 3, 1, color] == structure_state[round, 3, 0, 2, color])
                    model.addConstr(structure_state[round, 2, 3, 2, color] == structure_state[round, 3, 0, 3, color])
                    model.addConstr(structure_state[round, 2, 3, 3, color] == structure_state[round, 3, 0, 0, color])

                model.addConstr(structure_state[round, 3, 0, 0, 3] == gp.or_(structure_state[round, 2, 3, 3, 3], structure_state[round, 2, 3, 3, 4]))
                model.addConstr(structure_state[round, 3, 0, 1, 3] == gp.or_(structure_state[round, 2, 3, 0, 3], structure_state[round, 2, 3, 0, 4]))
                model.addConstr(structure_state[round, 3, 0, 2, 3] == gp.or_(structure_state[round, 2, 3, 1, 3], structure_state[round, 2, 3, 1, 4]))
                model.addConstr(structure_state[round, 3, 0, 3, 3] == gp.or_(structure_state[round, 2, 3, 2, 3], structure_state[round, 2, 3, 2, 4]))

                model.addConstr(structure_state[round, 3, 1, 0, 3] == gp.or_(structure_state[round, 2, 2, 2, 3], structure_state[round, 2, 2, 2, 4]))
                model.addConstr(structure_state[round, 3, 1, 1, 3] == gp.or_(structure_state[round, 2, 2, 1, 3], structure_state[round, 2, 2, 1, 4]))
                model.addConstr(structure_state[round, 3, 1, 2, 3] == gp.or_(structure_state[round, 2, 2, 0, 3], structure_state[round, 2, 2, 0, 4]))
                model.addConstr(structure_state[round, 3, 1, 3, 3] == gp.or_(structure_state[round, 2, 2, 3, 3], structure_state[round, 2, 2, 3, 4]))

                model.addConstr(structure_state[round, 3, 2, 0, 3] == gp.or_(structure_state[round, 2, 1, 2, 3], structure_state[round, 2, 1, 2, 4]))
                model.addConstr(structure_state[round, 3, 2, 1, 3] == gp.or_(structure_state[round, 2, 1, 1, 3], structure_state[round, 2, 1, 1, 4]))
                model.addConstr(structure_state[round, 3, 2, 2, 3] == gp.or_(structure_state[round, 2, 1, 0, 3], structure_state[round, 2, 1, 0, 4]))
                model.addConstr(structure_state[round, 3, 2, 3, 3] == gp.or_(structure_state[round, 2, 1, 3, 3], structure_state[round, 2, 1, 3, 4]))
                
                model.addConstr(structure_state[round, 3, 3, 0, 3] == gp.or_(structure_state[round, 2, 0, 1, 3], structure_state[round, 2, 0, 1, 4]))
                model.addConstr(structure_state[round, 3, 3, 1, 3] == gp.or_(structure_state[round, 2, 0, 2, 3], structure_state[round, 2, 0, 2, 4]))
                model.addConstr(structure_state[round, 3, 3, 2, 3] == gp.or_(structure_state[round, 2, 0, 3, 3], structure_state[round, 2, 0, 3, 4]))
                model.addConstr(structure_state[round, 3, 3, 3, 3] == gp.or_(structure_state[round, 2, 0, 0, 3], structure_state[round, 2, 0, 0, 4]))

            #SB
            for round in range(structure_size-1):
                for row in range(4):
                    for col in range(4):
                        for color in range(4):
                            model.addConstr(structure_state[round, 3, row, col, color] == structure_state[round + 1, 0, row, col, color])

            #fix only in '1' and '2
            for round in range(structure_size):
                for step in [0,3]:
                    for row in range(4):
                        for col in range(4):
                            model.addConstr(structure_state[round, step, row, col, 4] == 0)
            
            #Structure must be balanced
            model.addConstr(gp.quicksum(structure_state[0, 1, row, col, color] for row in range(4) for col in range(4) for color in [1,3,4]) == fix_number)
            model.addConstr(gp.quicksum(structure_state[structure_size-1, 3, row, col, color] for row in range(4) for col in range(4) for color in [2,3,4]) == fix_number)

            for row in range(4):
                for col in range(4):
                    model.addConstr(structure_state[0, 1, row, col, 2] == 0)
                    model.addConstr(structure_state[structure_size-1, 3, row, col, 1] == 0)    
        #------------------------------------------------------------------------------------------------------------------------------------------
        ### MITM UP STATE CONSTRAINTS ### ~Forward propagation
        #------------------------------------------------------------------------------------------------------------------------------------------
        
        #MC
        for round in range(MITM_up_size):
            for col in range(4):
                model.addConstr(MITM_up_state[round, 1, 0, col, 0] == gp.or_(MITM_up_state[round, 0, row, col, 0] for row in [0, 2, 3]))
                model.addConstr(MITM_up_state[round, 1, 1, col, 0] == gp.or_(MITM_up_state[round, 0, row, col, 0] for row in [1, 3]))
                model.addConstr(MITM_up_state[round, 1, 2, col, 0] == MITM_up_state[round, 0, 2, col, 0])
                model.addConstr(MITM_up_state[round, 1, 3, col, 0] == MITM_up_state[round, 0, 3, col, 0])
        
        #AK
        for round in range(MITM_up_size-1):
            for row in range(4):
                for col in range(4):
                    #State after AK is unknow if : state before was, key is unknow or red
                    model.addConstr(MITM_up_state[round, 2, row, col, 0] == gp.or_(MITM_up_state[round, 1, row, col, 0], key[round+structure_size, row, col, 0], key[round+structure_size, row, col, 1]))
        for row in range(4):
            for col in range(4):
                for color in range(2):
                    model.addConstr(MITM_up_state[MITM_up_size-1, 2, row, col, color] == MITM_up_state[MITM_up_size-1, 1, row, col, color])

        #Permutation
        for round in range(MITM_up_size):
            for color in range(2):
                model.addConstr(MITM_up_state[round, 2, 0, 0, 1] == MITM_up_state[round, 3, 3, 3, 1])
                model.addConstr(MITM_up_state[round, 2, 0, 1, 1] == MITM_up_state[round, 3, 3, 0, 1])
                model.addConstr(MITM_up_state[round, 2, 0, 2, 1] == MITM_up_state[round, 3, 3, 1, 1])
                model.addConstr(MITM_up_state[round, 2, 0, 3, 1] == MITM_up_state[round, 3, 3, 2, 1])

                model.addConstr(MITM_up_state[round, 2, 1, 0, 1] == MITM_up_state[round, 3, 2, 2, 1])
                model.addConstr(MITM_up_state[round, 2, 1, 1, 1] == MITM_up_state[round, 3, 2, 1, 1])
                model.addConstr(MITM_up_state[round, 2, 1, 2, 1] == MITM_up_state[round, 3, 2, 0, 1])
                model.addConstr(MITM_up_state[round, 2, 1, 3, 1] == MITM_up_state[round, 3, 2, 3, 1])
                    
                model.addConstr(MITM_up_state[round, 2, 2, 0, 1] == MITM_up_state[round, 3, 1, 2, 1])
                model.addConstr(MITM_up_state[round, 2, 2, 1, 1] == MITM_up_state[round, 3, 1, 1, 1])
                model.addConstr(MITM_up_state[round, 2, 2, 2, 1] == MITM_up_state[round, 3, 1, 0, 1])
                model.addConstr(MITM_up_state[round, 2, 2, 3, 1] == MITM_up_state[round, 3, 1, 3, 1])

                model.addConstr(MITM_up_state[round, 2, 3, 0, 1] == MITM_up_state[round, 3, 0, 1, 1])
                model.addConstr(MITM_up_state[round, 2, 3, 1, 1] == MITM_up_state[round, 3, 0, 2, 1])
                model.addConstr(MITM_up_state[round, 2, 3, 2, 1] == MITM_up_state[round, 3, 0, 3, 1])
                model.addConstr(MITM_up_state[round, 2, 3, 3, 1] == MITM_up_state[round, 3, 0, 0, 1])
        
        #SB : unknow states remain unknow, state tested state '2' became knowm '1'
        for round in range(MITM_up_size-1):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        model.addConstr((MITM_up_state[round, 3, row, col, color] == 1) >> (MITM_up_state[round+1, 0, row, col, color] == 1)) 
                    model.addConstr((MITM_up_state[round, 3, row, col, 2] == 1) >> (MITM_up_state[round+1, 0, row, col, 1] == 1))
        
        #State test : performed only in the last step (before SB)
        for round in range(MITM_up_size):
            for step in range(3):
                for col in range(4):
                    for row in range(4):
                        model.addConstr(MITM_up_state[round, step, row, col, 2] == 0)
        
        #State test can be used only where the difference is known
        for round in range(MITM_up_size):
            for row in range(4):
                for col in range(4):
                    model.addConstr((MITM_up_state[round, 3, row, col, 2] == 1) >> (MITM_up_differential[round, 3, row, col, 1] ==1))
        
        #can't state test in the first round
        for row in range(4):
            for col in range(4):
                model.addConstr(MITM_up_state[0, 3, row, col, 2] == 0)
        
        #------------------------------------------------------------------------------------------------------------------------------------------
        ### MITM UP DIFFERENTIAL CONSTRAINTS ### ~Backward propagation
        #------------------------------------------------------------------------------------------------------------------------------------------

        #Permutation 
        for round in range(MITM_up_size):
            for color in range(2):
                model.addConstr(MITM_up_differential[round, 3, 0, 0, color] == MITM_up_differential[round, 2, 3, 3, color])
                model.addConstr(MITM_up_differential[round, 3, 0, 1, color] == MITM_up_differential[round, 2, 3, 0, color])
                model.addConstr(MITM_up_differential[round, 3, 0, 2, color] == MITM_up_differential[round, 2, 3, 1, color])
                model.addConstr(MITM_up_differential[round, 3, 0, 3, color] == MITM_up_differential[round, 2, 3, 2, color])

                model.addConstr(MITM_up_differential[round, 3, 1, 0, color] == MITM_up_differential[round, 2, 2, 2, color])
                model.addConstr(MITM_up_differential[round, 3, 1, 1, color] == MITM_up_differential[round, 2, 2, 1, color])
                model.addConstr(MITM_up_differential[round, 3, 1, 2, color] == MITM_up_differential[round, 2, 2, 0, color])
                model.addConstr(MITM_up_differential[round, 3, 1, 3, color] == MITM_up_differential[round, 2, 2, 3, color])
                    
                model.addConstr(MITM_up_differential[round, 3, 2, 0, color] == MITM_up_differential[round, 2, 1, 2, color])
                model.addConstr(MITM_up_differential[round, 3, 2, 1, color] == MITM_up_differential[round, 2, 1, 1, color])
                model.addConstr(MITM_up_differential[round, 3, 2, 2, color] == MITM_up_differential[round, 2, 1, 0, color])
                model.addConstr(MITM_up_differential[round, 3, 2, 3, color] == MITM_up_differential[round, 2, 1, 3, color])

                model.addConstr(MITM_up_differential[round, 3, 3, 0, color] == MITM_up_differential[round, 2, 0, 1, color])
                model.addConstr(MITM_up_differential[round, 3, 3, 1, color] == MITM_up_differential[round, 2, 0, 2, color])
                model.addConstr(MITM_up_differential[round, 3, 3, 2, color] == MITM_up_differential[round, 2, 0, 3, color])
                model.addConstr(MITM_up_differential[round, 3, 3, 3, color] == MITM_up_differential[round, 2, 0, 0, color])
        
        #AK, not impacted the differences
        for round in range(MITM_up_size):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        model.addConstr(MITM_up_differential[round, 2, row, col, color] == MITM_up_differential[round, 1, row, col, color])
        
        #MC
        for round in range(MITM_up_size):
            for col in range(4):
                model.addConstr(MITM_up_differential[round, 0, 0, col, 0] == gp.and_(MITM_up_differential[round, 1, row, col, 0] for row in [0, 2, 3]))
                model.addConstr(MITM_up_differential[round, 0, 1, col, 0] == gp.and_(MITM_up_differential[round, 1, row, col, 0] for row in [1, 3]))
                model.addConstr(MITM_up_differential[round, 0, 2, col, 0] == MITM_up_differential[round, 1, 2, col, 0])
                model.addConstr(MITM_up_differential[round, 0, 3, col, 0] == MITM_up_differential[round, 1, 3, col, 0])

                model.addConstr((MITM_up_differential[round, 0, 0, col, 2] == 1) >> (gp.quicksum(MITM_up_differential[round, 1, row, col, 1] for row in [0, 2, 3]) >=2 ))
                model.addConstr((MITM_up_differential[round, 0, 1, col, 2] == 1) >> (gp.quicksum(MITM_up_differential[round, 1, row, col, 1] for row in [1, 3]) == 2))
                model.addConstr(MITM_up_differential[round, 0, 2, col, 2] == 0)
                model.addConstr(MITM_up_differential[round, 0, 3, col, 2] == 0)

        #SB, guessed word with propabilistic key recovery became '0'
        for round in range(1,MITM_up_size):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        model.addConstr((MITM_up_differential[round, 0, row, col, color] == 1) >>  (MITM_up_differential[round-1, 3, row, col, color] == 1))
                    model.addConstr((MITM_up_differential[round, 0, row, col, 2] == 1) >> (MITM_up_differential[round-1, 3, row, col, 0] == 1))

        #Probabilistic key recovery is only possible with MC so in step '0'
        for round in range(MITM_up_size):
            for step in range(1,4):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(MITM_up_differential[round, step, row, col, 2] == 0)

        ### Link between differential propagation and state propagation : State must be know in step '3' (before SB) for the differential to propagate with proba 1 ###
        for round in range(MITM_up_size-1):
            for row in range(4):
                for col in range(4):
                    model.addConstr((MITM_up_differential[round, 3, row, col, 1] == 1) >> (MITM_up_state[round, 3, row, col, 0] == 0))

        ### Link between distinguisher and differential up ###
        
        for row in range(4):
            for col in range(4):
                for color in range(2):
                    model.addConstr(distinguisher_differential[0, 0, row, col, color] == MITM_up_differential[MITM_up_size-1, 3, row, col, color])
        
        #------------------------------------------------------------------------------------------------------------------------------------------
        ### TRUNCATED DIFFERENTIAL DISTINGUISHER
        #------------------------------------------------------------------------------------------------------------------------------------------
        """
        model.addConstr(distinguisher_differential[0, 0, 0, 0, 1] == 0)
        model.addConstr(distinguisher_differential[0, 0, 0, 1, 1] == 1)
        model.addConstr(distinguisher_differential[0, 0, 0, 2, 1] == 0)
        model.addConstr(distinguisher_differential[0, 0, 0, 3, 1] == 0)

        model.addConstr(distinguisher_differential[0, 0, 1, 0, 1] == 0)
        model.addConstr(distinguisher_differential[0, 0, 1, 1, 1] == 0)
        model.addConstr(distinguisher_differential[0, 0, 1, 2, 1] == 1)
        model.addConstr(distinguisher_differential[0, 0, 1, 3, 1] == 0)

        model.addConstr(distinguisher_differential[0, 0, 2, 0, 1] == 0)
        model.addConstr(distinguisher_differential[0, 0, 2, 1, 1] == 0)
        model.addConstr(distinguisher_differential[0, 0, 2, 2, 1] == 1)
        model.addConstr(distinguisher_differential[0, 0, 2, 3, 1] == 0)
        
        model.addConstr(distinguisher_differential[0, 0, 3, 0, 1] == 0)
        model.addConstr(distinguisher_differential[0, 0, 3, 1, 1] == 0)
        model.addConstr(distinguisher_differential[0, 0, 3, 2, 1] == 1)
        model.addConstr(distinguisher_differential[0, 0, 3, 3, 1] == 0)
        
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 0, 0, 1] == 0)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 0, 1, 1] == 0)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 0, 2, 1] == 0)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 0, 3, 1] == 1)

        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 1, 0, 1] == 1)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 1, 1, 1] == 0)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 1, 2, 1] == 0)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 1, 3, 1] == 0)

        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 2, 0, 1] == 1)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 2, 1, 1] == 0)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 2, 2, 1] == 0)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 2, 3, 1] == 0)
        
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 3, 0, 1] == 1)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 3, 1, 1] == 0)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 3, 2, 1] == 0)
        model.addConstr(distinguisher_differential[distinguisher_size-1, 3, 3, 3, 1] == 0)
        """
        #Distinguisher can never be fully know or unknow
        for round in range(distinguisher_size):
            for step in range(4):
                model.addConstr(gp.quicksum(distinguisher_differential[round, step, row, col, 0]  for row in range(4) for col in range(4)) >=1)
                model.addConstr(gp.quicksum(distinguisher_differential[round, step, row, col, 1]  for row in range(4) for col in range(4)) >=1)
        
        #MC
        for round in range(distinguisher_size):
            for col in range(4):
                model.addConstr(distinguisher_differential[round, 1, 0, col, 0] == gp.and_(distinguisher_differential[round, 0, row, col, 0] for row in [0, 2, 3]))
                model.addConstr(distinguisher_differential[round, 1, 1, col, 0] == gp.and_(distinguisher_differential[round, 0, row, col, 0] for row in [1, 3]))
                model.addConstr(distinguisher_differential[round, 1, 2, col, 0] == distinguisher_differential[round, 0, 2, col, 0])
                model.addConstr(distinguisher_differential[round, 1, 3, col, 0] == distinguisher_differential[round, 0, 3, col, 0])

                model.addConstr((distinguisher_differential[round, 1, 0, col, 2] == 1 ) >> (gp.quicksum(distinguisher_differential[round, 0, row, col, 1] for row in [0, 2, 3]) >=2))
                model.addConstr((distinguisher_differential[round, 1, 1, col, 2] == 1 ) >> (gp.quicksum(distinguisher_differential[round, 0, row, col, 1] for row in [1, 3]) == 2))
                model.addConstr(distinguisher_differential[round, 1, 2, col, 2] == 0)
                model.addConstr(distinguisher_differential[round, 1, 3, col, 2] == 0)

        #We can cancel words only in step '1' (after MC)
        for round in range(distinguisher_size):
            for step in [0, 2, 3]:
                for row in range(4):
                    for col in range(4):
                        model.addConstr(distinguisher_differential[round, step, row, col, 2] == 0)

        #AK
        for round in range(distinguisher_size):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        model.addConstr((distinguisher_differential[round, 1, row, col, color] == 1) >> (distinguisher_differential[round, 2, row, col, color] == 1))
                    model.addConstr((distinguisher_differential[round, 1, row, col, 2] == 1) >> (distinguisher_differential[round, 2, row, col, 0] == 1))
        
        #Permutation
        for round in range(distinguisher_size):
            for color in range(2):
                model.addConstr(distinguisher_differential[round, 3, 0, 0, color] == distinguisher_differential[round, 2, 3, 3, color])
                model.addConstr(distinguisher_differential[round, 3, 0, 1, color] == distinguisher_differential[round, 2, 3, 0, color])
                model.addConstr(distinguisher_differential[round, 3, 0, 2, color] == distinguisher_differential[round, 2, 3, 1, color])
                model.addConstr(distinguisher_differential[round, 3, 0, 3, color] == distinguisher_differential[round, 2, 3, 2, color])

                model.addConstr(distinguisher_differential[round, 3, 1, 0, color] == distinguisher_differential[round, 2, 2, 2, color])
                model.addConstr(distinguisher_differential[round, 3, 1, 1, color] == distinguisher_differential[round, 2, 2, 1, color])
                model.addConstr(distinguisher_differential[round, 3, 1, 2, color] == distinguisher_differential[round, 2, 2, 0, color])
                model.addConstr(distinguisher_differential[round, 3, 1, 3, color] == distinguisher_differential[round, 2, 2, 3, color])
                    
                model.addConstr(distinguisher_differential[round, 3, 2, 0, color] == distinguisher_differential[round, 2, 1, 2, color])
                model.addConstr(distinguisher_differential[round, 3, 2, 1, color] == distinguisher_differential[round, 2, 1, 1, color])
                model.addConstr(distinguisher_differential[round, 3, 2, 2, color] == distinguisher_differential[round, 2, 1, 0, color])
                model.addConstr(distinguisher_differential[round, 3, 2, 3, color] == distinguisher_differential[round, 2, 1, 3, color])

                model.addConstr(distinguisher_differential[round, 3, 3, 0, color] == distinguisher_differential[round, 2, 0, 1, color])
                model.addConstr(distinguisher_differential[round, 3, 3, 1, color] == distinguisher_differential[round, 2, 0, 2, color])
                model.addConstr(distinguisher_differential[round, 3, 3, 2, color] == distinguisher_differential[round, 2, 0, 3, color])
                model.addConstr(distinguisher_differential[round, 3, 3, 3, color] == distinguisher_differential[round, 2, 0, 0, color])
        
        #SB
        for round in range(distinguisher_size-1):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        model.addConstr(distinguisher_differential[round, 3, row, col, color] == distinguisher_differential[round+1, 0, row, col, color])
        
        #to be a valid disintguisher, the final state must have more 0 differences than annulation we used
        model.addConstr(end_distinguisher_zero >= propa_distinguisher+1)
        ### LINK Between distinguisher and differenial down ###
        
        for row in range(4):
            for col in range(4):
                for color in range(2):
                    model.addConstr(distinguisher_differential[distinguisher_size-1, 3, row, col, color] == MITM_down_differential[0, 0, row, col, color])
        
        #------------------------------------------------------------------------------------------------------------------------------------------
        ### MITM DOWN DIFFERENTIAL PROPAGATION ### ~forward propagation
        #------------------------------------------------------------------------------------------------------------------------------------------
        
        #We cannot have a state with no active differences 
        
        for round in range(MITM_down_size):
            for step in range(4):
                model.addConstr(gp.quicksum(MITM_down_differential[round, step, row, col, 0] for row in range(4) for col in range(4)) <= 15)
        
        #MC
        for round in range(MITM_down_size):
            for col in range(4):
                model.addConstr(MITM_down_differential[round, 1, 0, col, 0] == gp.and_(MITM_down_differential[round, 0, row, col, 0] for row in [0, 2, 3]))
                model.addConstr(MITM_down_differential[round, 1, 1, col, 0] == gp.and_(MITM_down_differential[round, 0, row, col, 0] for row in [1, 3]))
                model.addConstr(MITM_down_differential[round, 1, 2, col, 0] == MITM_down_differential[round, 0, 2, col, 0])
                model.addConstr(MITM_down_differential[round, 1, 3, col, 0] == MITM_down_differential[round, 0, 3, col, 0])
                
                model.addConstr((MITM_down_differential[round, 1, 0, col, 2] == 1) >> (gp.quicksum(MITM_down_differential[round, 0, row, col, 1] for row in [0, 2, 3]) >=2))
                model.addConstr((MITM_down_differential[round, 1, 1, col, 2] == 1) >> (gp.quicksum(MITM_down_differential[round, 0, row, col, 1] for row in [1, 3]) ==2))
                model.addConstr(MITM_down_differential[round, 1, 2, col, 2] == 0)
                model.addConstr(MITM_down_differential[round, 1, 3, col, 2] == 0)
                
        #Probabilistic key recovery is possible only after MC, so in step '1'
        for round in range(MITM_down_size):
            for step in [0,2,3]:
                for col in range(4):
                    for row in range(4):
                        model.addConstr(MITM_down_differential[round, step, row, col, 2] == 0)

        #AK guessed element with proba key recovery are 0 
        for round in range(MITM_down_size):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        model.addConstr((MITM_down_differential[round, 1, row, col, color] == 1) >> (MITM_down_differential[round, 2, row, col, color] == 1))
                    model.addConstr((MITM_down_differential[round, 1, row, col, 2] == 1) >> (MITM_down_differential[round, 2, row, col, 0] == 1))

        #Permutation
        for round in range(MITM_down_size):
            for color in range(2):
                model.addConstr(MITM_down_differential[round, 3, 0, 0, color] == MITM_down_differential[round, 2, 3, 3, color])
                model.addConstr(MITM_down_differential[round, 3, 0, 1, color] == MITM_down_differential[round, 2, 3, 0, color])
                model.addConstr(MITM_down_differential[round, 3, 0, 2, color] == MITM_down_differential[round, 2, 3, 1, color])
                model.addConstr(MITM_down_differential[round, 3, 0, 3, color] == MITM_down_differential[round, 2, 3, 2, color])

                model.addConstr(MITM_down_differential[round, 3, 1, 0, color] == MITM_down_differential[round, 2, 2, 2, color])
                model.addConstr(MITM_down_differential[round, 3, 1, 1, color] == MITM_down_differential[round, 2, 2, 1, color])
                model.addConstr(MITM_down_differential[round, 3, 1, 2, color] == MITM_down_differential[round, 2, 2, 0, color])
                model.addConstr(MITM_down_differential[round, 3, 1, 3, color] == MITM_down_differential[round, 2, 2, 3, color])
                    
                model.addConstr(MITM_down_differential[round, 3, 2, 0, color] == MITM_down_differential[round, 2, 1, 2, color])
                model.addConstr(MITM_down_differential[round, 3, 2, 1, color] == MITM_down_differential[round, 2, 1, 1, color])
                model.addConstr(MITM_down_differential[round, 3, 2, 2, color] == MITM_down_differential[round, 2, 1, 0, color])
                model.addConstr(MITM_down_differential[round, 3, 2, 3, color] == MITM_down_differential[round, 2, 1, 3, color])

                model.addConstr(MITM_down_differential[round, 3, 3, 0, color] == MITM_down_differential[round, 2, 0, 1, color])
                model.addConstr(MITM_down_differential[round, 3, 3, 1, color] == MITM_down_differential[round, 2, 0, 2, color])
                model.addConstr(MITM_down_differential[round, 3, 3, 2, color] == MITM_down_differential[round, 2, 0, 3, color])
                model.addConstr(MITM_down_differential[round, 3, 3, 3, color] == MITM_down_differential[round, 2, 0, 0, color])

        #SB
        for round in range(MITM_down_size-1):
            for row in range(4):
                for col in range(4):
                    for color in range(2):
                        model.addConstr(MITM_down_differential[round+1, 0, row, col, color] ==  MITM_down_differential[round, 3, row, col, color])

        #------------------------------------------------------------------------------------------------------------------------------------------
        ### MITM DOWN STATE PROPAGATION ### ~Backward Propagation
        #------------------------------------------------------------------------------------------------------------------------------------------
        
        #link between differential down and states
        for round in range(1,MITM_down_size):
            for row in range(4):
                for col in range(4):
                    model.addConstr((MITM_down_differential[round, 0, row, col, 1] == 1) >> (MITM_down_state[round, 0, row, col, 0] == 0))
        
        #Permutatiom
        for round in range(MITM_down_size):
            for color in range(2):
                model.addConstr(MITM_down_state[round, 3, 0, 0, color] == MITM_down_state[round, 2, 3, 3, color])
                model.addConstr(MITM_down_state[round, 3, 0, 1, color] == MITM_down_state[round, 2, 3, 0, color])
                model.addConstr(MITM_down_state[round, 3, 0, 2, color] == MITM_down_state[round, 2, 3, 1, color])
                model.addConstr(MITM_down_state[round, 3, 0, 3, color] == MITM_down_state[round, 2, 3, 2, color])

                model.addConstr(MITM_down_state[round, 3, 1, 0, color] == MITM_down_state[round, 2, 2, 2, color])
                model.addConstr(MITM_down_state[round, 3, 1, 1, color] == MITM_down_state[round, 2, 2, 1, color])
                model.addConstr(MITM_down_state[round, 3, 1, 2, color] == MITM_down_state[round, 2, 2, 0, color])
                model.addConstr(MITM_down_state[round, 3, 1, 3, color] == MITM_down_state[round, 2, 2, 3, color])
                    
                model.addConstr(MITM_down_state[round, 3, 2, 0, color] == MITM_down_state[round, 2, 1, 2, color])
                model.addConstr(MITM_down_state[round, 3, 2, 1, color] == MITM_down_state[round, 2, 1, 1, color])
                model.addConstr(MITM_down_state[round, 3, 2, 2, color] == MITM_down_state[round, 2, 1, 0, color])
                model.addConstr(MITM_down_state[round, 3, 2, 3, color] == MITM_down_state[round, 2, 1, 3, color])

                model.addConstr(MITM_down_state[round, 3, 3, 0, color] == MITM_down_state[round, 2, 0, 1, color])
                model.addConstr(MITM_down_state[round, 3, 3, 1, color] == MITM_down_state[round, 2, 0, 2, color])
                model.addConstr(MITM_down_state[round, 3, 3, 2, color] == MITM_down_state[round, 2, 0, 3, color])
                model.addConstr(MITM_down_state[round, 3, 3, 3, color] == MITM_down_state[round, 2, 0, 0, color])
        
        #AK
        for round in range(1,MITM_down_size):
            for row in range(4):
                for col in range(4):
                    model.addConstr(MITM_down_state[round, 1, row, col, 0] == gp.or_(MITM_down_state[round, 2, row, col, 0], key[total_round - MITM_down_size +round, row, col, 0], key[total_round - MITM_down_size +round, row, col, 2]))
        for row in range(4):
            for col in range(4):
                for color in range(2):
                    model.addConstr(MITM_down_state[0, 1, row, col, color] == MITM_down_state[0, 2, row, col, color])
       
        #MC
        for round in range(MITM_down_size):
            for col in range(4):
                model.addConstr(MITM_down_state[round, 0, 0, col, 1] == gp.and_(MITM_down_state[round, 1, row, col, 1] for row in [0, 2, 3]))
                model.addConstr(MITM_down_state[round, 0, 1, col, 1] == gp.and_(MITM_down_state[round, 1, row, col, 1] for row in [1, 3]))
                model.addConstr(MITM_down_state[round, 0, 2, col, 1] == MITM_down_state[round, 1, 2, col, 1])
                model.addConstr(MITM_down_state[round, 0, 3, col, 1] == MITM_down_state[round, 1, 3, col, 1])

        #SB, element can be state tested in '0'
        for round in range(1,MITM_down_size):
            for row in range(4):
                for col in range(4):
                        model.addConstr(MITM_down_state[round-1, 3, row, col, 0] == MITM_down_state[round, 0, row, col, 0])

        #state test are only performed after SB '0'
        for round in range(MITM_down_size):
            for step in range(1,4):
                for row in range(4):
                    for col in range(4):
                        model.addConstr(MITM_down_state[round, step, row, col, 2] == 0)
        
        #To use a state test, the difference must be known
        for round in range(MITM_down_size):
            for row in range(4):
                for col in range(4):
                    model.addConstr((MITM_down_state[round, 0, row, col, 2] == 1) >> (MITM_down_differential[round, 0, row, col, 1] == 1))

        #no state test in the final round
        for row in range(4):
            for col in range(4):
                model.addConstr(MITM_down_state[MITM_down_size-1, 0, row, col, 2] == 0)
        
        model.optimize()
        
        if model.Status == GRB.OPTIMAL:
            state_matrix = np.zeros([total_round, 4, 4, 4])
            differential_matrix = np.zeros([total_round, 4, 4, 4])
            key_matrix = np.zeros([total_round, 4, 4])

            for round in range(structure_size):
                for step in range(4):
                    for row in range(4): 
                        for col in range(4):
                            if structure_state[round, step, row, col, 0].X == 1.0 :
                                state_matrix[round, step, row, col] = 0
                            if structure_state[round, step, row, col, 1].X == 1.0 :
                                state_matrix[round, step, row, col] = 1
                            if structure_state[round, step, row, col, 2].X == 1.0 :
                                state_matrix[round, step, row, col] = 2
                            if structure_state[round, step, row, col, 3].X == 1.0 :
                                state_matrix[round, step, row, col] = 3
                            if structure_state[round, step, row, col, 4].X == 1.0 :
                                state_matrix[round, step, row, col] = -1

                            differential_matrix[round, step, row, col] = 0
            
            for round in range(MITM_up_size):
                for step in range(4):
                    for row in range(4): 
                        for col in range(4):
                            if MITM_up_state[round, step, row, col, 0].X == 1.0 :
                                state_matrix[round + structure_size, step, row, col] = 0
                            if MITM_up_state[round, step, row, col, 1].X == 1.0 :
                                state_matrix[round + structure_size, step, row, col] = 2
                            if MITM_up_state[round, step, row, col, 2].X == 1.0 :
                                state_matrix[round + structure_size, step, row, col] = -1
                            
                            if MITM_up_differential[round, step, row, col, 0].X == 1.0 :
                                differential_matrix[round + structure_size, step, row, col] = 0
                            if MITM_up_differential[round, step, row, col, 1].X == 1.0 :
                                differential_matrix[round + structure_size, step, row, col] = 2
                            if MITM_up_differential[round, step, row, col, 2].X == 1.0 :
                                differential_matrix[round + structure_size, step, row, col] = -1
            
            for round in range(distinguisher_size):
                for step in range(4):
                    for row in range(4):
                        for col in range(4):
                            state_matrix[round+ structure_size + MITM_up_size, step, row, col] = 0

                            if distinguisher_differential[round, step, row, col, 0].X == 1.0:
                                differential_matrix[round + structure_size + MITM_up_size, step, row, col] = 0
                            if distinguisher_differential[round, step, row, col, 1].X == 1.0:
                                differential_matrix[round + structure_size + MITM_up_size, step, row, col] = 3
                            if distinguisher_differential[round, step, row, col, 2].X == 1.0:
                                differential_matrix[round + structure_size + MITM_up_size, step, row, col] = -1
            
            for round in range(MITM_down_size):
                for step in range(4):
                    for row in range(4):
                        for col in range(4):
                            if MITM_down_state[round, step, row, col, 0].X == 1.0:
                                state_matrix[total_round-MITM_down_size+round, step, row, col] = 0
                            if MITM_down_state[round, step, row, col, 1].X == 1.0:
                                state_matrix[total_round-MITM_down_size+round, step, row, col] = 1
                            if MITM_down_state[round, step, row, col, 2].X == 1.0:
                                state_matrix[total_round-MITM_down_size+round, step, row, col] = -1
                            
                            if MITM_down_differential[round, step, row, col, 0].X == 1.0:
                                differential_matrix[total_round-MITM_down_size+round, step, row, col] = 0
                            if MITM_down_differential[round, step, row, col, 1].X == 1.0:
                                differential_matrix[total_round-MITM_down_size+round, step, row, col] = 1
                            if MITM_down_differential[round, step, row, col, 2].X == 1.0:
                                differential_matrix[total_round-MITM_down_size+round, step, row, col] = -1
                        
            for round in range(total_round):
                for row in range(4):
                    for col in range(4):
                        if key[round, row, col, 0].X == 1.0:
                            key_matrix[round, row, col] = 0
                        if key[round, row, col, 1].X == 1.0:
                            key_matrix[round, row, col] = 1
                        if key[round, row, col, 2].X == 1.0:
                            key_matrix[round, row, col] = 2
                        if key[round, row, col, 3].X == 1.0:
                            key_matrix[round, row, col] = 3\

            return([True, 
                   state_matrix, differential_matrix, key_matrix,
                   blue_key_guess.getValue(), red_key_guess.getValue(), purple_key_guess.getValue(),
                   state_test_up.getValue(), state_test_down.getValue(),
                   proba_diff_up.getValue(), proba_diff_down.getValue(),
                   propa_distinguisher.getValue(),
                   red_complexity.getValue(), blue_complexity.getValue(), match_complexity.getValue(), 
                   fix_number.getValue(), start_distinguisher_active.getValue(), end_distinguisher_active.getValue()])
       
        else :
            return([False])















