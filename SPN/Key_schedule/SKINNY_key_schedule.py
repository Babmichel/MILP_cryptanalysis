from Model.Common_bricks_for_attacks import MILP_bricks
import gurobipy as gp
from itertools import product

class Model_MILP_key_schedule(MILP_bricks):
    def __init__(self, cipher_parameters, total_round, model):
        super().__init__(cipher_parameters, None, model)
        #Key parameters
        self.tweakey_number = cipher_parameters.get('tweakey_number', 3)
        self.key_size = cipher_parameters.get('key_size', 192)
        self.key_schedule_permutation = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]
        self.total_round = total_round
        self.intial_permutation = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ,10, 11 ,12, 13, 14, 15]

        self.model=model

    def one_permutation(self, input_list):
        return([input_list[self.key_schedule_permutation[i]] for i in range(len(input_list))])

    def x_permutation(self, input_list, x):
        output_permutation = input_list
        for _ in range(x):
            output_permutation = self.one_permutation(output_permutation)
        return(output_permutation)

    def master_key_initialisation(self): 
        self.master_key = self.model.addVars(range(self.block_row_size), 
                                             range(self.block_column_size), 
                                             range(3),
                                             vtype = gp.GRB.BINARY, 
                                             name  = 'master_key')
        
        self.master_key_count_guess = self.model.addVars(range(self.block_row_size), 
                                             range(self.block_column_size), range(3),
                                             vtype = gp.GRB.INTEGER, 
                                             name  = 'master_key_count_guess')
        
        self.master_key_count_guess_match = self.model.addVars(range(self.block_row_size), 
                                             range(self.block_column_size),
                                             vtype = gp.GRB.BINARY, 
                                             name  = 'master_key_count_guess_during_match')

        self.model.addConstrs((self.master_key[row, column, 0]==1) >> (self.master_key[row, column, value] == 0)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)
                              for value in [1,2])
        
        self.model.addConstrs(((gp.quicksum(self.master_key[row, column, value] for value in range(3)) >=1)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = "master_key_bits_are_known_are_unknown")
        
        self.upper_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'upper_key_guess')
        self.lower_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'lower_key_guess')
        self.common_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'lower_key_guess')
        
        self.model.addConstr(self.upper_key_guess <= self.key_size//self.word_size-1)
        self.model.addConstr(self.lower_key_guess <= self.key_size//self.word_size-1)


        self.model.addConstr(self.upper_key_guess == gp.quicksum(self.tweakey_number*self.master_key[row, column, 1] + (1-self.master_key[row, column, 1])*self.master_key_count_guess[row, column, 1]
                                                                   for row in range(self.block_row_size)
                                                                   for column in range(self.block_column_size)),
                                                                   name = 'upper_key_guess_counter')
        
        self.model.addConstr(self.lower_key_guess == gp.quicksum(self.tweakey_number*self.master_key[row, column, 2] + (1-self.master_key[row, column, 2])*self.master_key_count_guess[row, column, 2]
                                                                   for row in range(self.block_row_size)
                                                                   for column in range(self.block_column_size)),
                                                                   name = 'lower_key_guess_counter')
        
        self.model.addConstr(self.common_key_guess == gp.quicksum(self.tweakey_number*self.master_key[row, column, 2]*self.master_key[row, column, 1]
                                                                  + (1 - self.master_key[row, column, 2]*self.master_key[row, column, 1])*(self.master_key_count_guess[row, column, 1]*(1-self.master_key[row, column, 1]) + self.master_key_count_guess[row, column, 2]*(1-self.master_key[row, column, 2]))*self.master_key_count_guess_match[row, column]
                                                                  for row in range(self.block_row_size)
                                                                  for column in range(self.block_column_size)),
                                                                  name = 'match_key_guess_counter')

    def subkey_initialisation(self):
        self.upper_subkey = self.model.addVars(range(self.total_round), 
                                                    range(self.block_row_size), 
                                                    range(self.block_column_size), 
                                                    vtype = gp.GRB.BINARY, 
                                                    name = 'upper_subkey')
        
        self.lower_subkey = self.model.addVars(range(self.total_round), 
                                                    range(self.block_row_size), 
                                                    range(self.block_column_size), 
                                                    vtype = gp.GRB.BINARY, 
                                                    name = 'lower_subkey')

    def keyschedule(self):
        self.master_key_initialisation()
        self.subkey_initialisation()

        #only half of the state is added
        self.model.addConstrs((self.upper_subkey[round_index, row, column]==1
                              for round_index in range(self.total_round)
                              for row in range(self.block_row_size//2, self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = 'half_upper_subkey_addition_')

        self.model.addConstrs((self.lower_subkey[round_index, row, column]==1
                              for round_index in range(self.total_round)
                              for row in range(self.block_row_size//2, self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = 'half_lower_subkey_addition_')
        
        #Master_key_count_guess compte les guess a travers les subkey
        self.model.addConstrs(((gp.quicksum((1-(self.x_permutation(self.intial_permutation, round_index).index(row*4+column))//(self.block_column_size*self.block_row_size/2))
                                            *self.upper_subkey[round_index, 
                                                            (self.x_permutation(self.intial_permutation, round_index).index(row*4+column))//self.block_row_size, 
                                                            (self.x_permutation(self.intial_permutation, round_index).index(row*4+column))%self.block_column_size] 
                                            for round_index in range(self.total_round))
                                            == self.master_key_count_guess[row, column, 1])
                                    for row in range(self.block_row_size)
                                    for column in range(self.block_column_size)), 
                                    name = 'key_count_for_upper_master_key_active')
                              
        self.model.addConstrs(((gp.quicksum((1-(self.x_permutation(self.intial_permutation, round_index).index(row*4+column))//(self.block_column_size*self.block_row_size/2))
                                            *self.lower_subkey[round_index, 
                                                            (self.x_permutation(self.intial_permutation, round_index).index(row*4+column))//self.block_row_size, 
                                                            (self.x_permutation(self.intial_permutation, round_index).index(row*4+column))%self.block_column_size] 
                                            for round_index in range(self.total_round))
                                            == self.master_key_count_guess[row, column, 2])
                                    for row in range(self.block_row_size)
                                    for column in range(self.block_column_size)), 
                                    name = 'key_count_for_lower_master_key_active')
        
        #if a subkey is guess more than three time then all the master key bits are known
        self.model.addConstrs((self.master_key_count_guess[row, column, attack_part] >= self.tweakey_number*self.master_key[row, column, attack_part]
                         for row in range(self.block_row_size)
                         for column in range(self.block_column_size)
                         for attack_part in [1,2]), 
                         name = 'known master key bits imply more than three guess on a same subkey bit')
        
        self.model.addConstrs((self.master_key_count_guess[row, column, attack_part] <= 2 + self.total_round*self.master_key[row, column, attack_part]
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)
                                for attack_part in [1,2]), 
                                name = 'more than three guess on a same subkey bit imply known master key bits')   

        self.model.addConstrs((self.master_key_count_guess[row, column, 1] + self.master_key_count_guess[row, column, 2] <= 3+self.total_round*self.master_key_count_guess_match[row, column]
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = 'count of match in the match')
                               
    def display_master_key(self):
        print("Master keys :")
        for row in range(self.block_row_size):
            line=''
            line += '|'
            for column in range(self.block_row_size):
                if self.master_key[row, column, 0].X == 1:
                    line += "\033[90m ■ \033[0m"
                elif self.master_key[row, column, 1].X == 1 and self.master_key[row, column, 2].X == 0 :
                    line += "\033[91m ■ \033[0m"
                elif self.master_key[row, column, 1].X == 0 and self.master_key[row, column, 2].X == 1 :
                    line += "\033[94m ■ \033[0m"
                elif self.master_key[row, column, 1].X == 1 and self.master_key[row, column, 2].X == 1 :
                    line += "\033[95m ■ \033[0m"
                else :
                    line+='?'
            line += '| '
            print(line)
        print("Master keys upper guess :")
        for row in range(self.block_row_size):
            line=''
            line += '|'
            for column in range(self.block_column_size):
                line += f' {int(self.master_key_count_guess[row, column, 1].X)} '
            line += '| '
            print(line)
        print("Master keys lower guess :")
        for row in range(self.block_row_size):
            line=''
            line += '|'
            for column in range(self.block_column_size):
                line += f' {int(self.master_key_count_guess[row, column, 2].X)} '
            line += '| '
            print(line)


        