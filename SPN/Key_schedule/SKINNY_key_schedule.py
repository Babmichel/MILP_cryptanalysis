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

        self.model.addConstrs(self.master_key[row, column, 0] + self.master_key[row, column, value] <= 1
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)
                              for value in [1,2])
        
        self.model.addConstrs(((gp.quicksum(self.master_key[row, column, value] for value in range(3)) >=1)
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), 
                              name = "master_key_bits_are_known_are_unknown")
        
        self.upper_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'upper_key_guess')
        self.lower_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'lower_key_guess')
        self.common_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'common_key_guess')
        
        self.model.addConstr(self.upper_key_guess <= self.key_size//self.word_size-1)
        self.model.addConstr(self.lower_key_guess <= self.key_size//self.word_size-1)


        # --- Linearisation of key guess counters (previously MIQCP due to BINARY*INTEGER products) ---
        #
        # upper_key_guess[r,c] = min(count1, tweakey_number)
        #   = tweakey_number*mk1 + (1-mk1)*count1
        #   = tweakey_number*mk1 + count1 - mk1*count1
        # Linearise mk1*count1 via w_upper[r,c] (McCormick BINARY x INTEGER).
        #
        # common_key_guess algebraic simplification:
        #   When mk1=mk2=1: count1_partial = count2_partial = 0, so the second term vanishes.
        #   This gives:
        #     tweakey_number*(mk1 AND mk2)
        #     + match*count1 - match*mk1*count1
        #     + match*count2 - match*mk2*count2
        #     - tweakey_number*match
        #     + tweakey_number*(mk1 AND mk2 AND match)
        #   Auxiliary variables needed (all McCormick):
        #     both_mk    = mk1 * mk2            (BINARY x BINARY)
        #     bm_match   = both_mk * match      (BINARY x BINARY)
        #     w_upper    = mk1 * count1         (BINARY x INTEGER)  [reused from upper_key_guess]
        #     w_lower    = mk2 * count2         (BINARY x INTEGER)  [reused from lower_key_guess]
        #     p1         = match * count1       (BINARY x INTEGER)
        #     p2         = match * count2       (BINARY x INTEGER)
        #     q1         = match * w_upper      (BINARY x INTEGER)
        #     q2         = match * w_lower      (BINARY x INTEGER)

        M_round = self.total_round
        R, C = range(self.block_row_size), range(self.block_column_size)

        # w_upper[r,c] = master_key[r,c,1] * master_key_count_guess[r,c,1]
        w_upper = self.model.addVars(R, C, lb=0, ub=M_round, vtype=gp.GRB.INTEGER, name='w_upper')
        self.model.addConstrs((w_upper[r,c] >= self.master_key_count_guess[r,c,1] - M_round*(1 - self.master_key[r,c,1])
                               for r in R for c in C), name='w_upper_lb')
        self.model.addConstrs((w_upper[r,c] <= self.master_key_count_guess[r,c,1]
                               for r in R for c in C), name='w_upper_ub_count')
        self.model.addConstrs((w_upper[r,c] <= M_round * self.master_key[r,c,1]
                               for r in R for c in C), name='w_upper_ub_mk')

        # w_lower[r,c] = master_key[r,c,2] * master_key_count_guess[r,c,2]
        w_lower = self.model.addVars(R, C, lb=0, ub=M_round, vtype=gp.GRB.INTEGER, name='w_lower')
        self.model.addConstrs((w_lower[r,c] >= self.master_key_count_guess[r,c,2] - M_round*(1 - self.master_key[r,c,2])
                               for r in R for c in C), name='w_lower_lb')
        self.model.addConstrs((w_lower[r,c] <= self.master_key_count_guess[r,c,2]
                               for r in R for c in C), name='w_lower_ub_count')
        self.model.addConstrs((w_lower[r,c] <= M_round * self.master_key[r,c,2]
                               for r in R for c in C), name='w_lower_ub_mk')

        self.model.addConstr(self.upper_key_guess ==
                             gp.quicksum(self.tweakey_number*self.master_key[r,c,1]
                                         + self.master_key_count_guess[r,c,1] - w_upper[r,c]
                                         for r in R for c in C),
                             name='upper_key_guess_counter')

        self.model.addConstr(self.lower_key_guess ==
                             gp.quicksum(self.tweakey_number*self.master_key[r,c,2]
                                         + self.master_key_count_guess[r,c,2] - w_lower[r,c]
                                         for r in R for c in C),
                             name='lower_key_guess_counter')

        # both_mk[r,c] = master_key[r,c,1] * master_key[r,c,2]  (BINARY x BINARY McCormick)
        both_mk = self.model.addVars(R, C, vtype=gp.GRB.BINARY, name='both_mk')
        self.model.addConstrs((both_mk[r,c] <= self.master_key[r,c,1] for r in R for c in C), name='both_mk_ub1')
        self.model.addConstrs((both_mk[r,c] <= self.master_key[r,c,2] for r in R for c in C), name='both_mk_ub2')
        self.model.addConstrs((both_mk[r,c] >= self.master_key[r,c,1] + self.master_key[r,c,2] - 1
                               for r in R for c in C), name='both_mk_lb')

        # bm_match[r,c] = both_mk[r,c] * master_key_count_guess_match[r,c]  (BINARY x BINARY McCormick)
        bm_match = self.model.addVars(R, C, vtype=gp.GRB.BINARY, name='bm_match')
        self.model.addConstrs((bm_match[r,c] <= both_mk[r,c]
                               for r in R for c in C), name='bm_match_ub1')
        self.model.addConstrs((bm_match[r,c] <= self.master_key_count_guess_match[r,c]
                               for r in R for c in C), name='bm_match_ub2')
        self.model.addConstrs((bm_match[r,c] >= both_mk[r,c] + self.master_key_count_guess_match[r,c] - 1
                               for r in R for c in C), name='bm_match_lb')

        # p1[r,c] = match[r,c] * count1[r,c]  (BINARY x INTEGER McCormick)
        p1 = self.model.addVars(R, C, lb=0, ub=M_round, vtype=gp.GRB.INTEGER, name='p1_match_count1')
        self.model.addConstrs((p1[r,c] >= self.master_key_count_guess[r,c,1] - M_round*(1 - self.master_key_count_guess_match[r,c])
                               for r in R for c in C), name='p1_lb')
        self.model.addConstrs((p1[r,c] <= self.master_key_count_guess[r,c,1]
                               for r in R for c in C), name='p1_ub_count')
        self.model.addConstrs((p1[r,c] <= M_round * self.master_key_count_guess_match[r,c]
                               for r in R for c in C), name='p1_ub_match')

        # p2[r,c] = match[r,c] * count2[r,c]  (BINARY x INTEGER McCormick)
        p2 = self.model.addVars(R, C, lb=0, ub=M_round, vtype=gp.GRB.INTEGER, name='p2_match_count2')
        self.model.addConstrs((p2[r,c] >= self.master_key_count_guess[r,c,2] - M_round*(1 - self.master_key_count_guess_match[r,c])
                               for r in R for c in C), name='p2_lb')
        self.model.addConstrs((p2[r,c] <= self.master_key_count_guess[r,c,2]
                               for r in R for c in C), name='p2_ub_count')
        self.model.addConstrs((p2[r,c] <= M_round * self.master_key_count_guess_match[r,c]
                               for r in R for c in C), name='p2_ub_match')

        # q1[r,c] = match[r,c] * w_upper[r,c]  (BINARY x INTEGER McCormick)
        q1 = self.model.addVars(R, C, lb=0, ub=M_round, vtype=gp.GRB.INTEGER, name='q1_match_w_upper')
        self.model.addConstrs((q1[r,c] >= w_upper[r,c] - M_round*(1 - self.master_key_count_guess_match[r,c])
                               for r in R for c in C), name='q1_lb')
        self.model.addConstrs((q1[r,c] <= w_upper[r,c]
                               for r in R for c in C), name='q1_ub_w')
        self.model.addConstrs((q1[r,c] <= M_round * self.master_key_count_guess_match[r,c]
                               for r in R for c in C), name='q1_ub_match')

        # q2[r,c] = match[r,c] * w_lower[r,c]  (BINARY x INTEGER McCormick)
        q2 = self.model.addVars(R, C, lb=0, ub=M_round, vtype=gp.GRB.INTEGER, name='q2_match_w_lower')
        self.model.addConstrs((q2[r,c] >= w_lower[r,c] - M_round*(1 - self.master_key_count_guess_match[r,c])
                               for r in R for c in C), name='q2_lb')
        self.model.addConstrs((q2[r,c] <= w_lower[r,c]
                               for r in R for c in C), name='q2_ub_w')
        self.model.addConstrs((q2[r,c] <= M_round * self.master_key_count_guess_match[r,c]
                               for r in R for c in C), name='q2_ub_match')

        # common_key_guess = sum_rc(
        #   tweakey_number * both_mk
        #   + (p1 - q1)                         = match*count1*(1-mk1)
        #   + (p2 - q2)                         = match*count2*(1-mk2)
        #   - tweakey_number * match
        #   + tweakey_number * bm_match          = tweakey_number * both_mk * match
        # )
        self.model.addConstr(self.common_key_guess ==
                             gp.quicksum(
                                 self.tweakey_number * both_mk[r,c]
                                 + p1[r,c] - q1[r,c]
                                 + p2[r,c] - q2[r,c]
                                 - self.tweakey_number * self.master_key_count_guess_match[r,c]
                                 + self.tweakey_number * bm_match[r,c]
                                 for r in R for c in C),
                             name='match_key_guess_counter')

        # key_filter counts how many key bits can be filtered during the match due to
        # excess guesses, with each part capped at tweakey_number:
        #   self.filter_excess[r,c] = (min(count_upper, TK) + min(count_lower, TK) - TK) * match
        #
        # min(count, TK) is already available as  TK*mk + count - w  (= TK when mk=1, count otherwise),
        # so the expression to linearise is:
        #   expr = TK*mk1 + count1 - w_upper + TK*mk2 + count2 - w_lower - TK
        #
        # Example: count_upper=4, count_lower=2, TK=3  =>  expr = 3+2-3 = 2  (not 4+2-3=3)
        #
        # max(expr) = TK (both parts fully capped), so big-M = TK.
        # Linearise  filter_excess = expr * match  (BINARY x INTEGER McCormick)
        #   match=0  =>  filter_excess = 0   (ub_match forces it)
        #   match=1  =>  filter_excess = expr            (lb + ub_count pin it)
        TK = self.tweakey_number
        self.filter_excess = self.model.addVars(R, C, lb=0, ub=TK, vtype=gp.GRB.INTEGER, name='filter_excess')
        self.model.addConstrs(
            (self.filter_excess[r,c] >= (TK*self.master_key[r,c,1] + self.master_key_count_guess[r,c,1] - w_upper[r,c]
                                    + TK*self.master_key[r,c,2] + self.master_key_count_guess[r,c,2] - w_lower[r,c]
                                    - TK)
             - TK*(1 - self.master_key_count_guess_match[r,c])
             for r in R for c in C), name='filter_excess_lb')
        self.model.addConstrs(
            (self.filter_excess[r,c] <= (TK*self.master_key[r,c,1] + self.master_key_count_guess[r,c,1] - w_upper[r,c]
                                    + TK*self.master_key[r,c,2] + self.master_key_count_guess[r,c,2] - w_lower[r,c]
                                    - TK)
             + TK*(1 - self.master_key_count_guess_match[r,c])
             for r in R for c in C), name='filter_excess_ub_count')
        self.model.addConstrs(
            (self.filter_excess[r,c] <= TK * self.master_key_count_guess_match[r,c]
             for r in R for c in C), name='filter_excess_ub_match')

        self.key_filter = self.model.addVar(vtype=gp.GRB.INTEGER, lb=0, name='key_filter')
        self.model.addConstr(self.key_filter == gp.quicksum(self.filter_excess[r,c] for r in R for c in C),
                             name='key_filter_counter')

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
        
        self.model.addConstrs((self.master_key_count_guess[row, column, attack_part] <= self.tweakey_number - 1 + self.total_round*self.master_key[row, column, attack_part]
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)
                                for attack_part in [1,2]), 
                                name = 'more than three guess on a same subkey bit imply known master key bits')   

        self.model.addConstrs((self.master_key_count_guess[row, column, 1] + self.master_key_count_guess[row, column, 2] <= self.tweakey_number+self.total_round*self.master_key_count_guess_match[row, column]
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
        print(f"Key filter total (excess guesses during match): {int(self.key_filter.X)}")
        print("Key filter per cell :")
        for row in range(self.block_row_size):
            line = '|'
            for column in range(self.block_column_size):
                line += f' {int(self.filter_excess[row, column].X)} '
            line += '|'
            print(line)



