from Model.Common_bricks_for_attacks import MILP_bricks
import gurobipy as gp

class Model_MILP_key_schedule(MILP_bricks):
    def __init__(self, cipher_parameters, total_round, model):
        super().__init__(cipher_parameters, None, model)
        #Key parameters
        self.key_size = cipher_parameters.get('key_size', 256)
        self.total_round = total_round
        self.model=model
        self.a = 1
        self.b = 3
        self.c = 9
        self.d = 28

    def master_key_initialisation(self):
        self.master_key = self.model.addVars(range(self.total_round), range(8), range(self.key_size//8), range(3),
                           vtype=gp.GRB.BINARY, name="master_key")
        
        self.model.addConstrs((gp.quicksum(self.master_key[round_index, row, column, value] for value in range(3)) >= 1 
                             for round_index in range(self.total_round)
                             for row in range(8) 
                             for column in range(self.key_size//8)),
                             name='master_key_known_or_unknown')

        self.model.addConstrs((self.master_key[round_index, row, column, 0] + self.master_key[round_index, row, column, value] <=1
                              for round_index in range(self.total_round)
                              for row in range(8)
                              for column in range(32)
                              for value in [1, 2]), 
                              name = "master_key_cannot_be_known_and_unknown")

        self.upper_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'upper_key_guess')
        self.lower_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'lower_key_guess')
        self.common_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'lower_key_guess')
    
    def round_key_initialisation(self):
        #round_keys
        self.upper_subkey = self.model.addVars(range(self.total_round), range(4), range(self.key_size//8),
                           vtype=gp.GRB.BINARY, name="round_key")
        
        self.lower_subkey = self.model.addVars(range(self.total_round), range(4), range(self.key_size//8),
                           vtype=gp.GRB.BINARY, name="round_key")
        
    def keyschedule(self):
        self.master_key_initialisation()
        self.round_key_initialisation()
        
        for round_index in range(1, self.total_round):
            if round_index % 2 == 1:
                    for column in range(self.key_size//8):
                        for value in [1,2]:
                            self.model.addConstr(self.master_key[round_index, 0, column, value] == gp.and_(self.master_key[round_index-1, 0, (column-self.a)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 1, column, value]))
                            self.model.addConstr(self.master_key[round_index, 1, column, value] == gp.and_(self.master_key[round_index-1, 2, (column-self.c)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 3, column, value]))
                            self.model.addConstr(self.master_key[round_index, 2, column, value] == gp.and_(self.master_key[round_index-1, 0, (column-self.a)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 1, column, value], self.master_key[round_index-1, 1, (column-self.b)%(self.key_size//8), value]))
                            self.model.addConstr(self.master_key[round_index, 3, column, value] == gp.and_(self.master_key[round_index-1, 2, (column-self.c)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 3, column, value], self.master_key[round_index-1, 3, (column-self.d)%(self.key_size//8), value]))
                            
                            self.model.addConstr(self.master_key[round_index, 4, column, value] == gp.and_(self.master_key[round_index-1, 4, (column-self.a)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 5, column, value]))
                            self.model.addConstr(self.master_key[round_index, 5, column, value] == gp.and_(self.master_key[round_index-1, 6, (column-self.c)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 7, column, value]))
                            self.model.addConstr(self.master_key[round_index, 6, column, value] == gp.and_(self.master_key[round_index-1, 4, (column-self.a)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 5, column, value], self.master_key[round_index-1, 5, (column-self.b)%(self.key_size//8), value]))
                            self.model.addConstr(self.master_key[round_index, 7, column, value] == gp.and_(self.master_key[round_index-1, 6, (column-self.c)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 7, column, value], self.master_key[round_index-1, 7, (column-self.d)%(self.key_size//8), value]))
                            
            else :
                 for column in range(self.key_size//8):
                        for value in [1, 2]:
                            self.model.addConstr(self.master_key[round_index, 0, column, value] == gp.and_(self.master_key[round_index-1, 0, (column-self.a)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 1, column, value]))
                            self.model.addConstr(self.master_key[round_index, 4, column, value] == gp.and_(self.master_key[round_index-1, 2, (column-self.c)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 3, column, value]))
                            self.model.addConstr(self.master_key[round_index, 2, column, value] == gp.and_(self.master_key[round_index-1, 0, (column-self.a)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 1, column, value], self.master_key[round_index-1, 1, (column-self.b)%(self.key_size//8), value]))
                            self.model.addConstr(self.master_key[round_index, 6, column, value] == gp.and_(self.master_key[round_index-1, 2, (column-self.c)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 3, column, value], self.master_key[round_index-1, 3, (column-self.d)%(self.key_size//8), value]))
                            
                            self.model.addConstr(self.master_key[round_index, 1, column, value] == gp.and_(self.master_key[round_index-1, 4, (column-self.a)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 5, column, value]))
                            self.model.addConstr(self.master_key[round_index, 5, column, value] == gp.and_(self.master_key[round_index-1, 6, (column-self.c)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 7, column, value]))
                            self.model.addConstr(self.master_key[round_index, 3, column, value] == gp.and_(self.master_key[round_index-1, 4, (column-self.a)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 5, column, value], self.master_key[round_index-1, 5, (column-self.b)%(self.key_size//8), value]))
                            self.model.addConstr(self.master_key[round_index, 7, column, value] == gp.and_(self.master_key[round_index-1, 6, (column-self.c)%(self.key_size//8), value],
                                                                                                self.master_key[round_index-1, 7, column, value], self.master_key[round_index-1, 7, (column-self.d)%(self.key_size//8), value]))
        
        self.model.addConstrs((self.upper_subkey[round_index, row, column] == self.master_key[round_index, 4*(round_index%2) + row, column, 1]
                              for round_index in range(2)
                              for row in range(4)
                              for column in range(self.key_size//8)),
                              name='upper_subkey_and_master_key_start')
        
        self.model.addConstrs((self.lower_subkey[round_index, row, column] == self.master_key[round_index, 4*(round_index%2) + row, column, 2]
                              for round_index in range(2)
                              for row in range(4)
                              for column in range(self.key_size//8)),
                              name='lower_subkey_and_master_key_start')

        self.model.addConstr(self.upper_key_guess == gp.quicksum(self.upper_subkey[round_index, row, column] for round_index in range(self.total_round) for row in range(4) for column in range(self.key_size//8))
                              - gp.quicksum(self.upper_subkey[round_index, row, column]*self.master_key[round_index, 4*(round_index%2) + row, column, 1] for round_index in range(2, self.total_round+1) for row in range(4) for column in range(self.key_size//8)),
                              name='upper_key_guess')
        
        self.model.addConstr(self.lower_key_guess == gp.quicksum(self.lower_subkey[round_index, row, column] for round_index in range(self.total_round) for row in range(4) for column in range(self.key_size//8))
                              - gp.quicksum(self.lower_subkey[round_index, row, column]*self.master_key[round_index, 4*(round_index%2) + row, column, 2] for round_index in range(2, self.total_round+1) for row in range(4) for column in range(self.key_size//8)),
                              name='lower_key_guess')

        self.model.addConstr(self.common_key_guess == gp.quicksum(self.lower_subkey[round_index, row, column]*self.upper_subkey[round_index, row, column]*self.master_key[0, row, column, 1]*self.master_key[0, row, column,2] for row in range(4) for column in range(self.key_size//8)),
                                name='common_key_guess')
        
        self.model.addConstr(self.upper_key_guess <= self.key_size-1)

        self.model.addConstr(self.lower_key_guess <= self.key_size-1)
        
    def display_master_key(self):
        print("Master keys :")
        for round_index in range(self.total_round):
            for row in range(8):
                line=''
                line += '|'
                for column in range(32):
                    if self.master_key[round_index, row, column, 0].X == 1:
                        line += "\033[90m ■ \033[0m"
                    elif self.master_key[round_index, row, column, 1].X == 1 and self.master_key[round_index, row, column, 2].X == 0 :
                        line += "\033[91m ■ \033[0m"
                    elif self.master_key[round_index, row, column, 1].X == 0 and self.master_key[round_index,  row, column, 2].X == 1 :
                        line += "\033[94m ■ \033[0m"
                    elif self.master_key[round_index, row, column, 1].X == 1 and self.master_key[round_index, row, column, 2].X == 1 :
                        line += "\033[95m ■ \033[0m"
                    else :
                        line+='?'

                line += '| '
                if row==3 or row==7:
                    line+='\n'
                print(line)