from Model.Common_bricks_for_attacks import MILP_bricks
import gurobipy as gp

class Model_MILP_key_schedule(MILP_bricks):
    def __init__(self, cipher_parameters, total_round, model):
        super().__init__(cipher_parameters, None, model)
        #Key parameters
        self.key_size = cipher_parameters.get('key_size', 128)
        self.total_round = total_round
        self.model = model

    def master_key(self):
        # master_key[round, row, col, value] with:
        #   value=0: unknown, value=1: known by upper, value=2: known by lower
        # The master key state is a 4x32 matrix, tracked at each round.
        self.master_key = self.model.addVars(
            range(self.total_round), range(4), range(32), range(3),
            vtype=gp.GRB.BINARY, name='master_key')
        
        self.master_key_tamp = self.model.addVars(
            range(self.total_round), range(4), range(32), range(3),
            vtype=gp.GRB.BINARY, name='master_key')

        self.model.addConstrs(
            (gp.quicksum(self.master_key[r, row, col, v] for v in range(3)) >= 1
             for r in range(self.total_round)
             for row in range(4)
             for col in range(32)),
            name='master_key_at_least_one_state')

        self.model.addConstrs(
            (self.master_key[r, row, col, 0] + self.master_key[r, row, col, v] <= 1
             for v in [1, 2]
             for r in range(self.total_round)
             for row in range(4)
             for col in range(32)),
            name='master_key_unknown_excludes_known')
        
        self.model.addConstrs(
            (gp.quicksum(self.master_key_tamp[r, row, col, v] for v in range(3)) >= 1
             for r in range(self.total_round)
             for row in range(4)
             for col in range(32)),
            name='master_key_at_least_one_state')

        
        self.model.addConstrs(
            (self.master_key_tamp[r, row, col, 0] + self.master_key_tamp[r, row, col, v] <= 1
             for v in [1, 2]
             for r in range(self.total_round)
             for row in range(4)
             for col in range(32)),
            name='master_key_unknown_excludes_known')
        
        
        self.model.addConstrs((self.master_key[round, row, col, 0] ==1 for round in range(self.total_round) for row in range(4) for col in range(16)), name='master_key_tamp_initially_unknown')

        self.model.addConstrs((self.master_key_tamp[0, row, col, 0] ==1 for row in range(4) for col in range(32)), name='master_key_tamp_initially_unknown')

    def subkey(self):
        # The subkey at each round is the 16 rightmost columns (cols 16..31) of the master key.
        self.upper_subkey = self.model.addVars(
            range(self.total_round), range(4), range(16),
            vtype=gp.GRB.BINARY, name='upper_subkey')
        self.lower_subkey = self.model.addVars(
            range(self.total_round), range(4), range(16),
            vtype=gp.GRB.BINARY, name='lower_subkey')

        self.model.addConstrs(
            (self.upper_subkey[r, row, col] == self.master_key[r, row, col + 16, 1]
             for r in range(self.total_round)
             for row in range(4)
             for col in range(16)), 
            name='upper_subkey_is_right_16_cols_of_master_key')

        self.model.addConstrs(
            (self.lower_subkey[r, row, col] == self.master_key[r, row, col + 16, 2]
             for r in range(self.total_round)
             for row in range(4)
             for col in range(16)),
            name='lower_subkey_is_right_16_cols_of_master_key')
        

    def keyschedule(self):
        self.master_key()
        self.subkey()

        for r in range(self.total_round - 1):
            for col in range(32):
                for v in [1, 2]:
                    # Row 0[r+1][col] = (Row 0[r] <<< 8)[col] XOR Row 1[r][col]
                    # Bit at col in the shifted row came from (col+8)%32 in row 0.
                    # XOR is known by party v iff BOTH inputs are known by party v (AND).
                    src0 = self.master_key[r, 0, (col + 8) % 32, v]
                    src1 = self.master_key[r, 1, col, v]
                    dst0 = self.master_key_tamp[r + 1, 0, col, v]
                    self.model.addConstr(dst0 <= src0,
                        name=f'ks_row0_xor_ub1_v{v}_r{r}_c{col}')
                    self.model.addConstr(dst0 <= src1,
                        name=f'ks_row0_xor_ub2_v{v}_r{r}_c{col}')
                    self.model.addConstr(dst0 >= src0 + src1 - 1,
                        name=f'ks_row0_xor_lb_v{v}_r{r}_c{col}')

                    # Row 2[r+1][col] = (Row 2[r] <<< 16)[col] XOR Row 3[r][col]
                    src2 = self.master_key[r, 2, (col + 16) % 32, v]
                    src3 = self.master_key[r, 3, col, v]
                    dst2 = self.master_key_tamp[r + 1, 2, col, v]
                    self.model.addConstr(dst2 <= src2,
                        name=f'ks_row2_xor_ub1_v{v}_r{r}_c{col}')
                    self.model.addConstr(dst2 <= src3,
                        name=f'ks_row2_xor_ub2_v{v}_r{r}_c{col}')
                    self.model.addConstr(dst2 >= src2 + src3 - 1,
                        name=f'ks_row2_xor_lb_v{v}_r{r}_c{col}')

                # Row 1[r+1] = Row 2[r]  (copy, no XOR)
                self.model.addConstrs(
                    (self.master_key_tamp[r + 1, 1, col, v] == self.master_key[r, 2, col, v]
                     for v in range(3)),
                    name=f'ks_row1_copy_r{r}_c{col}')

                # Row 3[r+1] = Row 0[r]  (copy, no XOR)
                self.model.addConstrs(
                    (self.master_key_tamp[r + 1, 3, col, v] == self.master_key[r, 0, col, v]
                     for v in range(3)),
                    name=f'ks_row3_copy_r{r}_c{col}')
                
                
                
        self.upper_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'upper_key_guess')
        self.lower_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'lower_key_guess')
        self.common_key_guess = self.model.addVar(vtype = gp.GRB.INTEGER, name = 'common_key_guess')

        self.model.addConstr(self.upper_key_guess == gp.quicksum(self.upper_subkey[round, row, col] - self.upper_subkey[round, row, col]*self.master_key_tamp[round, row, col, 1] for round in range(self.total_round) for row in range(4) for col in range(16)), name='upper_key_guess_def')
        self.model.addConstr(self.lower_key_guess == gp.quicksum(self.lower_subkey[round, row, col] - self.lower_subkey[round, row, col]*self.master_key_tamp[round, row, col, 2] for round in range(self.total_round) for row in range(4) for col in range(16)), name='lower_key_guess_def')
        self.model.addConstr(self.common_key_guess == gp.quicksum(self.lower_subkey[round, row, col]*self.upper_subkey[round, row, col] - self.lower_subkey[round, row, col]*self.master_key_tamp[round, row, col, 1]*self.upper_subkey[round, row, col]*self.master_key_tamp[round, row, col, 1] for round in range(self.total_round) for row in range(4) for col in range(16)), name='common_key_guess_def')
    
    def display_master_key(self):
        print("upper key :                 Lower key :                    Master key states :              Master key states (tamp) :")
        for r in range(self.total_round):
            print(f"Round {r}:")
            for row in range(4):
                line = '|'
                for col in range(16):
                    if self.upper_subkey[r, row, col].X == 0:
                        line += "\033[90m ■\033[0m"
                    elif self.upper_subkey[r, row, col].X == 1:
                        line += "\033[91m ■\033[0m"
                    else:
                        line += '?'
                line += '|  '

                line += '|'
                for col in range(16):
                    if self.lower_subkey[r, row, col].X == 0:
                        line += "\033[90m ■\033[0m"
                    elif self.lower_subkey[r, row, col].X == 1:
                        line += "\033[94m ■\033[0m"
                    else:
                        line += '?'
                line += '|  '

                line += '|'
                for col in range(32):
                    if self.master_key[r, row, col, 0].X == 1:
                        line += "\033[90m ■\033[0m"
                    elif self.master_key[r, row, col, 1].X == 1 and self.master_key[r, row, col, 2].X == 0:
                        line += "\033[91m ■\033[0m"
                    elif self.master_key[r, row, col, 1].X == 0 and self.master_key[r, row, col, 2].X == 1:
                        line += "\033[94m ■\033[0m"
                    elif self.master_key[r, row, col, 1].X == 1 and self.master_key[r, row, col, 2].X == 1:
                        line += "\033[95m ■\033[0m"
                    else:
                        line += '?'
                line += '|  '
            
                line += '|'
                for col in range(32):
                    if self.master_key_tamp[r, row, col, 0].X == 1:
                        line += "\033[90m ■\033[0m"
                    elif self.master_key_tamp[r, row, col, 1].X == 1 and self.master_key_tamp[r, row, col, 2].X == 0:
                        line += "\033[91m ■\033[0m"
                    elif self.master_key_tamp[r, row, col, 1].X == 0 and self.master_key_tamp[r, row, col, 2].X == 1:
                        line += "\033[94m ■\033[0m"
                    elif self.master_key_tamp[r, row, col, 1].X == 1 and self.master_key_tamp[r, row, col, 2].X == 1:
                        line += "\033[95m ■\033[0m"
                    else:
                        line += '?'
                line += '|  '
                print(line)
