#Trunc diff MITM MILP model for CRAFT
import gurobipy as gp
from gurobipy import GRB
import numpy as np

def attack(structure_size, MITM_up_size, distinguisher_size, MITM_down_size):
    options = {
    "WLSACCESSID" : "bb41a17b-b3b2-40d7-8c1c-01d90a2e2170",
    "WLSSECRET" : "4db1c96a-1e47-4fc9-83eb-28a57d08879f",
    "LICENSEID" : 2534357
    }
    with gp.Env(params=options) as env, gp.Model(env=env) as model:
        
        #CONSTRAINTS INITIALISATION
        total_round = structure_size+MITM_up_size+distinguisher_size+MITM_down_size

        structure_state = np.zeros([structure_size, 4, 4, 4, 5], dtype = "object") #[round, step, row, col , color]
        for round in range(structure_size):
            for step in range(4):
                for row in range(4):
                    for col in range(4):
                        for color in range(5):
                            structure_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"Structure state {round} {step} {row} {col} {color}")
        
        MITM_up_state = np.zeros([MITM_up_size, 4, 4, 4, 3], dtype = "object") #[round, step, row, col, color : 0=unknow 1=know 2 statetested]
        MITM_up_differential = np.zeros([MITM_up_size, 4, 4, 4, 3], dtype = "object") #[round, step, row, col, color : 0=unknow 1=know 2 probabilisitc anulation]
        for round in range(MITM_up_size):
            for step in range(4):
                for row in range(4):
                    for col in range(4):
                        for color in range(3):
                            MITM_up_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM up state {round} {step} {row} {col} {color}")
                            MITM_up_differential[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM up differnential {round} {step} {row} {col} {color}")

        distinguisher_differential = np.zeros([distinguisher_size, 4, 4, 4, 3], dtype = object) #[round, step, row, col , color : 0=null 1=know, 2=cancel]
        for round in range(distinguisher_size):
            for step in range(4):
                for row in range(4):
                    for col in range(4):
                        for color in range(3):
                            distinguisher_differential[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"distiguisher {round} {step} {row} {col} {color}")
        
        MITM_down_state = np.zeros([MITM_down_size, 4, 4, 4, 3], dtype = "object") #[round, step, row, col, color : 0=unknow 1=know 2 statetested]
        MITM_down_differential = np.zeros([MITM_down_size, 4, 4, 4, 3], dtype = "object") #[round, step, row, col, color : 0=unknow 1=know 2 probabilisitc anulation]
        for round in range(MITM_down_size):
            for step in range(4):
                for row in range(4):
                    for col in range(4):
                        for color in range(3):
                            MITM_down_state[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM down state {round} {step} {row} {col} {color}")
                            MITM_down_differential[round, step, row, col, color] = model.addVar(vtype = GRB.BINARY, name = f"MITM down differnential {round} {step} {row} {col} {color}")
        
        key = np.zeros([total_round, 4, 4, 4])