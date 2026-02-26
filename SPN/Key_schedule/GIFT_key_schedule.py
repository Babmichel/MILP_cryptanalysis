from Model.Common_bricks_for_attacks import MILP_bricks
import gurobipy as gp

class Model_MILP_key_schedule(MILP_bricks):
    def __init__(self, cipher_parameters, total_round, model):
        super().__init__(cipher_parameters, None, model)
        #Key parameters
        self.key_size = cipher_parameters.get('key_size', 128)
        self.total_round = total_round
        self.model=model

    def master_key(self):
        self.master_key = self.model.addVars(range(8), range(16), range(3), vtype=gp.GRB.BINARY, name=f'master_key')

        self.model.addConstrs((gp.quicksum(self.master_key[key_index, bit_index, value] for value in range(3)) >= 1
                              for key_index in range(8)
                              for bit_index in range(16)), 
                              name="unique value in master key")
        
        self.model.addConstrs((self.master_key[key_index, bit_index, 0] + self.master_key[key_index, bit_index, value] <= 1
                              for value in range(1,3)
                              for key_index in range(8)
                              for bit_index in range(16)), 
                              name="unique value in master key")

    def subkey(self):
        self.upper_subkey = self.model.addVars(range(self.total_round), range(1), range(64), vtype=gp.GRB.BINARY, name=f'upper_subkey')
        self.lower_subkey = self.model.addVars(range(self.total_round), range(1), range(64), vtype=gp.GRB.BINARY, name=f'lower_subkey')

        self.model.addConstrs((self.upper_subkey[round_index, 0, index_1+index] == 1
                              for round_index in range(self.total_round)
                              for index_1 in range(0, 64, 4)
                              for index in range(2)), 
                              name = f'upper_subkey is not applied on the two first bit of each sbox')

        self.model.addConstrs((self.lower_subkey[round_index, 0, index_1+index] == 1
                              for round_index in range(self.total_round)
                              for index_1 in range(0, 64, 4)
                              for index in range(2)), 
                              name = f'upper_subkey is not applied on the two first bit of each sbox')

    def keyschedule(self):
        self.subkey()
        self.master_key()
       
       #link between subkey and master key
        self.model.addConstrs((self.upper_subkey[round_index,0,  (4*word_index - index +3 +4*(index*2+(1-index)*12)*(round_index//4))%64] == self.master_key[2*(round_index%4)+index, word_index, 1]
                              for round_index in range(self.total_round)
                              for word_index in range(16)
                              for index in range(2)), name='upper_subkey and master key direct link')
        
        self.model.addConstrs((self.lower_subkey[round_index, 0, (4*word_index - index +3 +4*(index*2+(1-index)*12)*(round_index//4))%64] == self.master_key[2*(round_index%4)+index, word_index, 2]
                              for round_index in range(self.total_round)
                              for word_index in range(16)
                              for index in range(2)), name='upper_subkey and master key direct link')

        #key count
        self.upper_key_guess = self.model.addVar(vtype=gp.GRB.INTEGER, name='upper_key_guess')
        self.lower_key_guess = self.model.addVar(vtype=gp.GRB.INTEGER, name='lower_key_guess')
        self.common_key_guess = self.model.addVar(vtype=gp.GRB.INTEGER, name='common_key_guess')

        self.model.addConstr(self.upper_key_guess == gp.quicksum(self.master_key[key_index, bit_index, 1] for key_index in range(8) for bit_index in range(16)))
        self.model.addConstr(self.lower_key_guess == gp.quicksum(self.master_key[key_index, bit_index, 2] for key_index in range(8) for bit_index in range(16)))

        #Here, we use McCormick constraints to count the common key bits without using multiplication and keeping a linear model
        self.common_key_guess_McCormick = self.model.addVars(range(8), range(16), vtype=gp.GRB.BINARY, name='common_key_guess_McCormick')

        self.model.addConstrs((self.common_key_guess_McCormick[key_index, bit_index] <= self.master_key[key_index, bit_index, 1]
                              for key_index in range(8)
                              for bit_index in range(16)), name='common_key_guess_McCormick upper key')
        self.model.addConstrs((self.common_key_guess_McCormick[key_index, bit_index] <= self.master_key[key_index, bit_index, 2]
                              for key_index in range(8)
                              for bit_index in range(16)), name='common_key_guess_McCormick lower key')
        self.model.addConstrs((self.common_key_guess_McCormick[key_index, bit_index] >= self.master_key[key_index, bit_index, 1] + self.master_key[key_index, bit_index, 2] - 1
                              for key_index in range(8)
                              for bit_index in range(16)), name='common_key_guess_McCormick both keys')
        
        self.model.addConstr(self.common_key_guess == gp.quicksum(self.common_key_guess_McCormick[key_index, bit_index] for key_index in range(8) for bit_index in range(16)))

    def display_master_key(self):
        print("Master keys :")
        for key_index in range(8):
            print(f'MK{key_index}')
            line=''
            line += '|'
            for bit_index in range(16):
                if self.master_key[key_index, bit_index, 0].X == 1:
                    line += "\033[90m ■ \033[0m"
                elif self.master_key[key_index, bit_index, 1].X == 1 and self.master_key[key_index, bit_index, 2].X == 0 :
                    line += "\033[91m ■ \033[0m"
                elif self.master_key[key_index, bit_index, 1].X == 0 and self.master_key[key_index, bit_index, 2].X == 1 :
                    line += "\033[94m ■ \033[0m"
                elif self.master_key[key_index, bit_index, 1].X == 1 and self.master_key[key_index, bit_index, 2].X == 1 :
                    line += "\033[95m ■ \033[0m"
                else :
                    line+='?'
            line += '| '
            print(line)