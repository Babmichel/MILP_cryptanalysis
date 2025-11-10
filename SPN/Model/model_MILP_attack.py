import gurobipy as gp
from sage.all import Matrix, GF
from itertools import combinations, product

class Model_MILP_attack():   
    def __init__(self, cipher_parameters, licence_parameters, model):  
        
        #Cipher name
        self.cipher_name = cipher_parameters.get('Cipher_name', 'SKINNY')
        
        #Block parameters
        self.block_size = cipher_parameters.get('block_size', 64)
        self.block_column_size = cipher_parameters.get('block_column_size', 4)
        self.block_row_size = cipher_parameters.get('block_row_size', 4)
        self.word_size = int(self.block_size/(self.block_column_size*self.block_row_size))
        
        #Operations parameters
        self.operation_order = cipher_parameters.get('operation_order', ['AK', 'SR', 'MC0', 'SB'])
        self.shift_rows = cipher_parameters.get('shift_rows', [0, 1, 2, 3])
        self.mix_columns = cipher_parameters.get('mix_columns')
        self.sbox_sizes = cipher_parameters.get('sbox_sizes', [1, 1])   
        
        #Extension of the given parameters
        self.state_number = len(self.shift_rows)+1
        self.shift_rows_inverse = [(self.block_column_size - shift) % self.block_column_size for shift in self.shift_rows]
        self.mix_columns_inverse = []
        for element in self.mix_columns : #Computing the inverse of the matrixes
            MC = Matrix(GF(2), element)
            MC_inv = MC.inverse()
            self.mix_columns_inverse.append([[int(MC_inv[j][i])for i in range(MC_inv.ncols())] for j in range(MC_inv.nrows())])
        self.model=model
        self.mc = [self.mix_columns, self.mix_columns_inverse]

        #MC objects
        self.column_range = [range(2)] * self.block_column_size
        self.column_possible_index = product(*(range(2) for _ in range(self.block_column_size)))
        self.possible_XORs_MC = [[],[]]
        for mc in self.mix_columns:
            self.possible_XORs_MC[0].append(self.unpack_possible_XORs_MC(mc))
        for mc in self.mix_columns_inverse:
            self.possible_XORs_MC[1].append(self.unpack_possible_XORs_MC(mc))

        #Model Creation
        if self.model==None:
            self.model = gp.Model(env=gp.Env(params={'WLSACCESSID': licence_parameters.get('WLSACCESSID'), 'WLSSECRET': licence_parameters.get('WLSSECRET'), 'LICENSEID': licence_parameters.get('LICENSEID')}))

            # Parameters of the Gurobi model
            self.model.params.FeasibilityTol = 1e-9
            self.model.params.OptimalityTol = 1e-9
            self.model.setParam("OutputFlag", 1) 
            self.model.setParam("LogToConsole", 1)
            self.model.setParam("IntFeasTol", 1e-9)
            
        
        # Double Check of cipher model
        self.everything_all_right = True
        self.optimized=False

    #Propagation of values OPERATORS
    def value_propagation_SR(self, part, attack_side_index, round_index, input_state_index, output_state_index, shift_rows):
        #an unknow value cannot turn to a value that can be computed.
        if input_state_index>output_state_index:
            sens = 1
        else :
            sens = 0
        self.model.addConstrs(((part[attack_side_index, sens, round_index, input_state_index, row, column, 0] == 1)
                                >> (part[attack_side_index, sens, round_index, output_state_index, row, (column+shift_rows[row])%self.block_column_size, 1] == 0)
                                for row in range(4) for column in range(4)),
                                name = "value_propagation_:_SR_0_not_to_1")
    
    def unpack_possible_XORs_vector(self, vector):# a refaire car fait avec le chat GPT
        """
        Version optimisée :
        - représentation des vecteurs comme entiers (bitmasks)
        - XOR logique
        - pas de chevauchement de bits entre vecteurs
        - suppression automatique des redondances
        """
        n = len(vector)
        # conversion du vecteur cible en entier (bitmask)
        target_mask = sum((1 << i) for i, v in enumerate(reversed(vector)) if v == 1)
        if target_mask == 0:
            return []

        # positions actives
        ones_positions = [i for i, v in enumerate(vector) if v == 1]
        k = len(ones_positions)

        # --- Génération de tous les sous-vecteurs valides ---
        valid_masks = []
        for mask in range(1, 1 << k):
            # reconstruire la position réelle du bitmask dans la taille totale n
            full_mask = 0
            for bit_index in range(k):
                if (mask >> bit_index) & 1:
                    full_mask |= 1 << (n - 1 - ones_positions[bit_index])
            valid_masks.append(full_mask)

        results = set()
        # --- Tester toutes les combinaisons sans chevauchement ---
        for r in range(1, k + 1):
            for combo in combinations(valid_masks, r):
                # Vérifier qu’ils ne se chevauchent pas
                union_mask = 0
                valid = True
                for m in combo:
                    if union_mask & m:
                        valid = False
                        break
                    union_mask |= m
                if not valid:
                    continue
                # Vérifier que le XOR donne la cible
                xor_sum = 0
                for m in combo:
                    xor_sum ^= m
                if xor_sum == target_mask:
                    results.add(tuple(sorted(combo)))

        # --- Conversion inverse en listes de 0/1 ---
        final_results = []
        for combo in results:
            combo_list = []
            for m in combo:
                bits = [(m >> i) & 1 for i in reversed(range(n))]
                combo_list.append(bits)
            final_results.append(combo_list)

        return final_results

    def unpack_possible_XORs_MC(self, mix_columns):
        possible_XOR_list = [[] for _ in range(self.block_row_size)]
        for row in range(self.block_row_size):
                possible_XOR_list[row]=self.unpack_possible_XORs_vector(mix_columns[row])
        return possible_XOR_list
    
    def value_propagation_MC(self, part, attack_side_index, round_index, input_state_index, output_state_index):
        if input_state_index>output_state_index:
            sens = 1
        else :
            sens = 0
        #if you have an unknow value in the input of the MC, all the possible XOR combinations included this value cannot be computed
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                c_vector = []
                for vector in product(*(range(2) for _ in range(self.block_column_size))):
                        if vector[row] == 1:
                            c_vector.append(tuple(vector))
                if attack_side_index == sens :
                    self.model.addConstrs(((part[attack_side_index, sens, round_index, input_state_index, row, column, 0] == 1) >> 
                                            (self.XOR_in_mc_values[(attack_side_index, sens, round_index, column) + c_vector_element + (1,)] == 0)
                                            for c_vector_element in c_vector),
                                            name=f"MC_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")


                
                else :
                    self.model.addConstrs(((part[attack_side_index, sens, round_index, input_state_index, row, column, 0] == 1) >> 
                                            (self.XOR_in_mc_values[(attack_side_index, sens, round_index, column) + c_vector_element + (1,)] == 0)
                                            for c_vector_element in c_vector),
                                            name=f"MC_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")

        #An output value in known if one of the possible XOR combinations leading to it is known
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MC[sens][round_index%(len(self.mix_columns))][row]:
                        or_var = self.model.addVar(vtype= gp.GRB.BINARY, name = f"or_var_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        not_or_var = self.model.addVar(vtype= gp.GRB.BINARY, name = f"not_or_var_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        if len(combination) >= 1:
                            self.model.addGenConstrOr(or_var, [self.XOR_in_mc_values[(attack_side_index, sens, round_index, column)+tuple(index)+(0,)] for index in combination], name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        else :
                            self.model.addConstr(or_var == self.XOR_in_mc_values[(attack_side_index, sens, round_index, column)+tuple(combination[0])+(0,)])
                        self.model.addConstr(not_or_var == 1-or_var)
                        or_vars.append(not_or_var)  

                self.model.addGenConstrOr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1], or_vars, name = f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
    
    def value_propagation_SB(self, part, attack_side_index, round_index, input_state_index, output_state_index, sbox_sizes):
        #if you have an unknow value in the input of the sbox all the outputs cannot be computed
        if input_state_index>output_state_index:
            sens = 1
        else :
            sens = 0
        self.model.addConstrs(((part[attack_side_index, sens, round_index, input_state_index, row_input, column_input, 0]==1)
                                 >> (part[attack_side_index, sens, round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 1]==0)
                                 for row_output in range(self.block_row_size//sbox_sizes[0])
                                 for column_output in range(self.block_column_size//sbox_sizes[1])
                                 for sbox_row in range(sbox_sizes[0])
                                 for sbox_column in range(sbox_sizes[1])
                                 for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                 for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])), 
                                 name='value_propagation_SB_:_0_not_to_1')

    def value_propagation_AK(self, part, attack_side_index, subkey_part, round_index, input_state_index, output_state_index):
        #if the state if not known before the AK it cannot be computed after
        if input_state_index>output_state_index:
            sens = 1
        else :
            sens = 0
        self.model.addConstrs((((part[attack_side_index, sens, round_index, input_state_index, row, column, 0]==1)
                                >> (part[attack_side_index, sens,round_index, output_state_index, row, column, 1]==0))
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_state_not_to_1')
        
        #if the key is not known, the state after AK cannot be computed
        self.model.addConstrs((((subkey_part[round_index, row, column]==0)
                                >> (part[attack_side_index, sens, round_index, output_state_index, row, column, 1]==0))
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_key_not_to_1')
        
    def value_propagation_NR(self, part, attack_side_index, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        if input_round_index < output_round_index:
            self.model.addConstrs(((part[attack_side_index, 0, input_round_index, self.state_number-1, row, column, 0]==1)
                                    >> (part[attack_side_index, 0, output_round_index, 0, row, column, 1]==0) for row in range(self.block_row_size) for column in range(self.block_column_size)), 
                                    name='value_propagation_NR_:_0_not_to_1')
        else :
            self.everything_all_right = False
            print("Error in value_propagation_NR: input_round_index should be inferior from output_round_index")
        
    def value_propagation_PR(self, part, attack_side_index, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        self.model.addConstrs(((part[attack_side_index, 1, input_round_index, 0, row, column, 0]==1)
                                >> (part[attack_side_index, 1, output_round_index, self.state_number-1, row, column, 1]==0) 
                                for row in range(self.block_row_size) 
                                for column in range(self.block_column_size)), 
                                name='value_propagation_PR_:_0_not_to_1')

    #Progation of values X-ROUND
    def forward_value_propagation(self, part, attack_side_index, first_round_index, last_round_index, subkey):
        for forward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR':
                    self.value_propagation_SR(part, attack_side_index, forward_round, state_index, state_index + 1, self.shift_rows)
                elif self.operation_order[state_index][0]+self.operation_order[state_index][1] == 'MC':
                    self.value_propagation_MC(part, attack_side_index, forward_round, state_index, state_index + 1)
                elif self.operation_order[state_index] == 'SB':
                    self.value_propagation_SB(part, attack_side_index, forward_round, state_index, state_index + 1, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    self.value_propagation_AK(part, attack_side_index, subkey, forward_round, state_index, state_index + 1)
                else :
                    self.everything_all_right = False
                    print("One of the round operator name is not recognized in the upper part value propagation")
            if forward_round != last_round_index:
                self.value_propagation_NR(part, attack_side_index, forward_round, forward_round+1)

    def backward_value_propagation(self, part, attack_side_index, first_round_index, last_round_index, subkey):
        for backward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if self.operation_order[state_index] == 'SR':
                    self.value_propagation_SR(part, attack_side_index, backward_round, state_index + 1, state_index, self.shift_rows_inverse)
                elif self.operation_order[state_index][0]+self.operation_order[state_index][1] == 'MC':
                    self.value_propagation_MC(part, attack_side_index, backward_round, state_index + 1, state_index)
                elif self.operation_order[state_index] == 'SB':
                    self.value_propagation_SB(part, attack_side_index, backward_round, state_index + 1, state_index, self.sbox_sizes)
                elif self.operation_order[state_index] == 'AK':
                    self.value_propagation_AK(part, attack_side_index, subkey, backward_round, state_index + 1, state_index)
                else :
                    self.everything_all_right = False
                    print("One of the round operator name is not recognized in the lower part value propagation")
            if backward_round != last_round_index:
                self.value_propagation_PR(part, attack_side_index, backward_round+1, backward_round)
   
    def optimize_the_model(self): 
        if self.everything_all_right:
            self.model.optimize()
            if self.model.Status != gp.GRB.INFEASIBLE :
                self.optimized=True
            else :
                self.model.computeIIS()
                self.model.write("model_infeasible.ilp")
        else : 
            print("Some error occured in assembling the model, please check the error(s) above.")



