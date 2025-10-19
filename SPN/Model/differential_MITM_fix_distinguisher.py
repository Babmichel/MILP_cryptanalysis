from Model import model_MILP_attack
import gurobipy as gp
import random as rd

class Differential_MITM_fix_distinguisher(model_MILP_attack.Model_MILP_attack):
    def __init__(self, cipher_parameters, licence_parameters, attack_parameters,):
        super().__init__(cipher_parameters, licence_parameters)
        #Attack parameters
        self.structure_rounds = attack_parameters.get('structure_rounds', 4)
        self.upper_rounds = attack_parameters.get('upper_rounds', 2)
        self.lower_rounds = attack_parameters.get('lower_rounds', 2)
        self.distinguisher_rounds = attack_parameters.get('distinguisher_rounds', 4)
        self.total_rounds = self.structure_rounds + self.upper_rounds + self.lower_rounds + self.distinguisher_rounds

    def getdetails(self):
        print(self.cipher_name, self.block_size, '-', self.key_size)
    
    def part_initalisation(self):
        self.upper_subkey=self.model.addVars(range(self.upper_rounds), range(self.block_row_size), range(self.block_column_size), range(2), vtype=gp.GRB.BINARY, name='upper_key')
        self.model.addConstrs((gp.quicksum(self.upper_subkey[round_index, row, column, value] for value in range(2)) == 1 
                              for round_index in range(self.upper_rounds) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_upper_state_value_constraints')

        self.lower_subkey=self.model.addVars(range(self.lower_rounds), range(self.block_row_size), range(self.block_column_size), range(2), vtype=gp.GRB.BINARY, name='lower_key')
        self.model.addConstrs((gp.quicksum(self.lower_subkey[round_index, row, column, value] for value in range(2)) == 1 
                              for round_index in range(self.lower_rounds) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_lower_state_value_constraints')
        
        #upper_values[round, state index, row, column, value]; valeur{0=unknown, 1=can be computed, 2=state_tested}
        self.upper_values = self.model.addVars(range(self.upper_rounds), range(self.state_number), range(self.block_row_size), range(self.block_column_size), range(3), vtype=gp.GRB.BINARY, name='upper_state_values')
        self.model.addConstrs((gp.quicksum(self.upper_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.upper_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_upper_state_value_constraints')

        #lower_values[round, state index, row, column, value]; valeur{0=unknown, 1=can be computed, 2=state_tested}
        self.lower_values = self.model.addVars(range(self.lower_rounds), range(self.state_number), range(self.block_row_size), range(self.block_column_size), range(3), vtype=gp.GRB.BINARY, name='lower_state_values')
        self.model.addConstrs((gp.quicksum(self.lower_values[round_index, state_index, row, column, value] for value in range(3)) == 1 
                              for round_index in range(self.lower_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_lower_state_value_constraints')

        #upper_differences[round, state index, row, column, value]; valeur{0=unknown, 1=can be computed}
        self.upper_differences = self.model.addVars(range(self.upper_rounds), range(self.state_number), range(self.block_row_size), range(self.block_column_size), range(3), vtype=gp.GRB.BINARY, name='upper_state_differences')
        self.model.addConstrs((gp.quicksum(self.upper_differences[round_index, state_index, row, column, value] for value in range(2)) == 1 
                              for round_index in range(self.upper_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_upper_difference_value_constraints')

        #lower_differences[round, state index, row, column, value]; valeur{0=unknown, 1=can be computed}
        self.lower_differences = self.model.addVars(range(self.lower_rounds), range(self.state_number), range(self.block_row_size), range(self.block_column_size), range(3), vtype=gp.GRB.BINARY, name='lower_state_differences')
        self.model.addConstrs((gp.quicksum(self.lower_differences[round_index, state_index, row, column, value] for value in range(2)) == 1 
                              for round_index in range(self.lower_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)), 'unique_value_in_lower_difference_value_constraints')

    def upper_part_value_propagation(self):
        self.model.addConstrs(self.upper_values[0, 0, row, column, 1]==1 for row in range(self.block_row_size) for column in range(self.block_column_size))
        self.model.addConstrs(self.upper_subkey[round_index, row, column, 1]==rd.randint(0,1) for round_index in range(self.upper_rounds) for row in range(self.block_row_size) for column in range(self.block_column_size))

        for upper_round in range(self.upper_rounds):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR':
                    self.value_propagation_SR(self.upper_values, upper_round, state_index, state_index + 1, self.shift_rows)
                elif self.operation_order[state_index] == 'MC':
                    self.value_propagation_MC(self.upper_values, upper_round, state_index, state_index + 1, self.mix_columns)
                elif self.operation_order[state_index] == 'SB':
                    self.value_propagation_SB(self.upper_values, upper_round, state_index, state_index + 1, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    self.value_propagation_AK(self.upper_values, self.upper_subkey, upper_round, state_index, state_index + 1)
                else :
                    self.everything_all_right = False
                    print("One of the round operator name is not recognized in the upper part value propagation")
            if upper_round != self.upper_rounds-1:
                self.value_propagation_NR(self.upper_values, upper_round, upper_round+1)

    def lower_part_value_propagation(self):
        self.model.addConstrs(self.lower_values[self.lower_rounds-1, self.state_number-1, row, column, 1]==1 for row in range(self.block_row_size) for column in range(self.block_column_size))
        self.model.addConstrs(self.lower_subkey[round_index, row, column, 1]==rd.randint(0,1) for round_index in range(self.lower_rounds) for row in range(self.block_row_size) for column in range(self.block_column_size))

        for lower_round in range(self.lower_rounds):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR':
                    self.value_propagation_SR(self.lower_values, lower_round, state_index + 1, state_index, self.shift_rows_inverse)
                elif self.operation_order[state_index] == 'MC':
                    self.value_propagation_MC(self.lower_values, lower_round, state_index + 1, state_index, self.mix_columns_inverse)
                elif self.operation_order[state_index] == 'SB':
                    self.value_propagation_SB(self.lower_values, lower_round, state_index + 1, state_index, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    self.value_propagation_AK(self.lower_values, self.lower_subkey, lower_round, state_index + 1, state_index)
                else :
                    self.everything_all_right = False
                    print("One of the round operator name is not recognized in the lower part value propagation")
            if lower_round != self.lower_rounds-1:
                self.value_propagation_NR(self.lower_values, lower_round+1, lower_round)

            
    def objective_function(self):
        self.state_test_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "state_test_up")
        self.active_fin_up = self.model.addVar(vtype= gp.GRB.INTEGER, name = "active_fin")
        self.state_test_down = self.model.addVar(vtype= gp.GRB.INTEGER, name = "state_test_down")
        self.active_fin_down = self.model.addVar(vtype= gp.GRB.INTEGER, name = "active_fin_down")

        self.for_display = self.model.addVar(vtype= gp.GRB.INTEGER, name = "for_display")

        self.model.addConstr(self.state_test_up == (gp.quicksum(self.upper_values[round_index, state_index, row, column, 2] for round_index in range(self.upper_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))))
        self.model.addConstr(self.active_fin_up == (gp.quicksum(self.upper_values[self.upper_rounds-1, self.state_number-1, row, column, 1] for row in range(self.block_row_size) for column in range(self.block_column_size))))
        
        self.model.addConstr(self.state_test_down == (gp.quicksum(self.lower_values[round_index, state_index, row, column, 2] for round_index in range(self.lower_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))))
        self.model.addConstr(self.active_fin_down == (gp.quicksum(self.lower_values[0, 0, row, column, 1] for row in range(self.block_row_size) for column in range(self.block_column_size))))
        
        self.model.addConstr(self.for_display == gp.quicksum(self.upper_values[round_index, state_index, row, column, 1] for round_index in range(self.upper_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size))
                                     + gp.quicksum(self.lower_values[round_index, state_index, row, column, 1] for round_index in range(self.lower_rounds) for state_index in range(self.state_number) for row in range(self.block_row_size) for column in range(self.block_column_size)))
        
        self.model.setObjectiveN(self.state_test_up - self.active_fin_up, index=0, priority=10)
        self.model.setObjectiveN(self.state_test_down - self.active_fin_down, index=1, priority=9)
        self.model.setObjectiveN((-1)*self.for_display, index=2, priority=0)
    
    def getresults(self):
        if self.optimize:
            print(self.state_test_up)
            print(self.active_fin_up)
        else :
            print('The Model at no been optimize yet')

    def affichage_console(self):
        # Upper part display
        for round_index in range(self.upper_rounds):
            print("ROUND ", round_index)
            key_line = ""
            for row in range(self.block_row_size):
                key_line += "        |"
                for column in range(self.block_column_size):
                    if self.upper_subkey[round_index, row, column, 0].X == 1:
                        key_line += "\033[90m ■ \033[0m"
                    elif self.upper_subkey[round_index, row, column, 1].X == 1:
                        key_line += "\033[91m ■ \033[0m"
                    else :
                        key_line += " ? "
                key_line += "|\n"

            print(key_line)
            for row in range(self.block_row_size):
                line = ""
                for state_index in range(self.state_number):
                    line += "|"
                    for column in range(self.block_column_size):
                        if self.upper_values[round_index, state_index, row, column, 0].X == 1:
                            line += "\033[90m ■ \033[0m"
                        elif self.upper_values[round_index, state_index, row, column, 1].X == 1:
                            line += "\033[91m ■ \033[0m"
                        elif self.upper_values[round_index, state_index, row, column, 2].X == 1:
                            line += "\033[92m ■ \033[0m"
                        else :
                            print(self.upper_values[round_index, state_index, row, column, 0].X)
                            print(self.upper_values[round_index, state_index, row, column, 1].X)
                            print(self.upper_values[round_index, state_index, row, column, 2].X)
                            line += " ? "
                    line += "|"
                    if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                        line += f"{ self.operation_order[state_index]}"
                    elif row == self.block_row_size//2 and state_index != self.state_number -1:
                        line += "->"
                    else :
                        line += "  "
                print(line)
            print("\n")
    
        # Lower part display
        for round_index in range(self.lower_rounds):
            print("ROUND ", round_index)
            key_line = ""
            for row in range(self.block_row_size):
                key_line += "        |"
                for column in range(self.block_column_size):
                    if self.lower_subkey[round_index, row, column, 0].X == 1:
                        key_line += "\033[90m ■ \033[0m"
                    elif self.lower_subkey[round_index, row, column, 1].X == 1:
                        key_line += "\033[94m ■ \033[0m"
                    else :
                        key_line += " ? "
                key_line += "|\n"

            print(key_line)
            for row in range(self.block_row_size):
                line = ""
                for state_index in range(self.state_number):
                    line += "|"
                    for column in range(self.block_column_size):
                        if self.lower_values[round_index, state_index, row, column, 0].X == 1:
                            line += "\033[90m ■ \033[0m"
                        elif self.lower_values[round_index, state_index, row, column, 1].X == 1:
                            line += "\033[94m ■ \033[0m"
                        elif self.lower_values[round_index, state_index, row, column, 2].X == 1:
                            line += "\033[92m ■ \033[0m"
                        else :
                            line += " ? "
                    line += "|"
                    if row == self.block_row_size//2 - 1 and state_index != self.state_number -1:
                        line += f"{ self.operation_order[state_index]}"
                    elif row == self.block_row_size//2 and state_index != self.state_number -1:
                        line += "<-"
                    else :
                        line += "  "
                print(line)
            print("\n")
        
    
