import gurobipy as gp
from sage.all import Matrix, GF
from itertools import combinations
import numpy as np

class MILP_bricks():   
    def __init__(self, cipher_parameters, licence_parameters, model):  
        
        #Cipher name
        self.cipher_name = cipher_parameters.get('Cipher_name', 'SKINNY')
        
        #Block parameters
        self.block_size = cipher_parameters.get('block_size', 64)
        self.block_column_size = cipher_parameters.get('column_size', 4)
        self.block_row_size = cipher_parameters.get('row_size', 4)
        self.word_size = int(self.block_size/(self.block_column_size*self.block_row_size))

        #rounds parameters
        self.alpha_reflection = cipher_parameters.get('alpha_reflection_construction', False)
        
        #Operations parameters
        _op_order_default = cipher_parameters.get('operation_order', None)
        self.operation_order_up   = cipher_parameters.get('operation_order_up',   _op_order_default)
        self.operation_order_down = cipher_parameters.get('operation_order_down', _op_order_default)
        assert len(self.operation_order_up) == len(self.operation_order_down), \
            "operation_order_up and operation_order_down must have the same length"
        self.shift_rows = cipher_parameters.get('shift_rows', None)
        matrixes = cipher_parameters.get('matrixes', None)
        self.sbox_sizes = cipher_parameters.get('sbox_sizes', None)   
        self.permutations = cipher_parameters.get('permutations', None)
        
        #Extension of the given parameters
        self.state_number = len(self.operation_order_up)+1
        if self.permutations !=None:
            self.permutations_inverse = [[0 for i in range(len(self.permutations[i]))] for i in range(len(self.permutations))]
            for i in range(len(self.permutations)):
                for j in range(len(self.permutations[i])):
                    self.permutations_inverse[i][j]=self.permutations[i].index(j)

        if self.shift_rows != None :
            self.shift_rows_inverse = [(self.block_column_size - shift) % self.block_column_size for shift in self.shift_rows]
        
        if matrixes != None:
            matrixes_inverses = []
            for element in matrixes : #Computing the inverse of the matrixes
                M = Matrix(GF(2), element)
                M_inv = M.inverse()
                matrixes_inverses.append([[int(M_inv[j][i])for i in range(M_inv.ncols())] for j in range(M_inv.nrows())])
            self.matrixes = [matrixes, matrixes_inverses]

            self.matrixes_sets = {s: [set(map(tuple, round_mc)) for round_mc in self.matrixes[s]]for s in (0,1)}
            self.matrixes_index_map = {s: [{tuple(v): idx for idx, v in enumerate(round_mc)}for round_mc in self.matrixes[s]]for s in (0,1)}

            if 'MC' in self.operation_order_up or 'MC' in self.operation_order_down:
                self.column_range = [[set() for _ in range(len(self.matrixes[0]))], [set() for _ in range(len(self.matrixes[1]))]]
                self.possible_XORs_MC = [[],[]]
                for m in self.matrixes[0]:
                    self.possible_XORs_MC[0].append(self.unpack_possible_XORs_M(m))
                for m in self.matrixes[1]:
                    self.possible_XORs_MC[1].append(self.unpack_possible_XORs_M(m))
                for i in range(2):
                    for m_index, m in enumerate(self.possible_XORs_MC[i]):
                        for row in m:
                            for vector_combination in row:
                                for vector in vector_combination:
                                    self.column_range[i][m_index].add(tuple(vector))
                                    self.column_range[not(i)][m_index].add(tuple(map(int,np.bitwise_xor.reduce(np.array(vector)[:,None]*np.array(self.matrixes[not(i)][m_index]), axis=0))))

            if 'MR' in self.operation_order_up or 'MR' in self.operation_order_down:
                self.row_range = [[set() for _ in range(len(self.matrixes[0]))], [set() for _ in range(len(self.matrixes[1]))]]
                self.possible_XORs_MR = [[],[]]
                for m in self.matrixes[0]:
                    self.possible_XORs_MR[0].append(self.unpack_possible_XORs_M(m))
                for m in self.matrixes[1]:
                    self.possible_XORs_MR[1].append(self.unpack_possible_XORs_M(m))
                for i in range(2):
                    for m_index, m in enumerate(self.possible_XORs_MR[i]):
                        for row in m:
                            for vector_combination in row:
                                for vector in vector_combination:
                                    self.row_range[i][m_index].add(tuple(vector))
                                    self.row_range[not(i)][m_index].add(tuple(map(int,np.bitwise_xor.reduce(np.array(vector)[:,None]*np.array(self.matrixes[not(i)][m_index]), axis=0))))

        #Model Creation
        self.model=model
        if self.model==None:
            self.model = gp.Model(env=gp.Env(params={'WLSACCESSID': licence_parameters.get('WLSACCESSID'), 'WLSSECRET': licence_parameters.get('WLSSECRET'), 'LICENSEID': licence_parameters.get('LICENSEID')}))

            # Parameters of the Gurobi model
            self.model.setParam("IntFeasTol",    1e-9)
            self.model.setParam("Presolve",    2)    # aggressive presolve
            self.model.setParam("Cuts",        3)    # aggressive cuts for dense logic models
            self.model.setParam("Heuristics",  0.50) # high heuristics to keep exploring new solutions
            self.model.setParam("VarBranch",   -1)   # auto branching: Gurobi picks the best strategy per node
            self.model.setParam("Aggregate",   2)    # AND and OR constraints aggregation
            self.model.setParam("MIPFocus",    1)    # focus on finding better feasible solutions
            self.model.setParam("ConcurrentMIP", 4)  # 4 diverse strategies: increases chance of finding better solutions
            self.model.setParam("NoRelHeurTime", 30) # 30s of no-relaxation heuristics at start: escapes early local optima
            self.model.setParam("MIPGap",      0.0)   # rely on MIPGapAbs for termination
            self.model.setParam("MIPGapAbs",   0.99)  # stop within 1 unit of optimal (safe for INTEGER time_complexity)
            self.model.setParam("TimeLimit",   7200*12) # 2h max to avoid infinite runs


        # Double Check of cipher model
        self.everything_all_right = True
        self.optimized=False

    #Tool functions
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

    def unpack_possible_XORs_M(self, matrixe):
        possible_XOR_list = [[] for _ in range(len(matrixe))]
        for row in range(len(matrixe)):
                possible_XOR_list[row]=self.unpack_possible_XORs_vector(matrixe[row])
        return possible_XOR_list
            
    #Propagation of VALUES through ORPERATIONS
    def propagation_SR_values(self, part, attack_side_index, round_index, input_state_index, output_state_index, shift_rows):
        #an unknow value cannot turn to a value that can be computed.
        sens = int(input_state_index > output_state_index)
        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                                + part[attack_side_index, sens, round_index, output_state_index, row, (column+shift_rows[row])%self.block_column_size, 1] <= 1
                                for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                name = "value_propagation_:_SR_0_not_to_1")
   
    def propagation_MC_values(self, part, XOR_in_part, attack_side_index, round_index, input_state_index, output_state_index, column_range):
        sens = int(input_state_index > output_state_index)
        mc_index = round_index % len(self.matrixes[sens])

        #First we fix to 0 all the input XOR that cannot be computed
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                for c_vector_element in column_range[mc_index]:
                    if c_vector_element[row] == 1:
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, column) + c_vector_element + (1,)]
                        #If propagation is forward in the upper part of bacward for the lower part : we can use the opposite propagation
                        if attack_side_index == sens:
                            # if the considered vector is in MC than we check if it is known form the opposite propagation
                            if c_vector_element in self.matrixes_sets[sens][mc_index]:
                                AND_elements = [part[attack_side_index, sens, round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, output_state_index, self.matrixes_index_map[sens][mc_index][c_vector_element], column, 0]]
                            else:
                                AND_elements = [part[attack_side_index, sens, round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, input_state_index, row, column, 0]]

                            and_var = self.model.addVar(vtype=gp.GRB.BINARY, name=f"and_var_MC_side{attack_side_index}_r{round_index}_row{row}_col{column}")

                            # AND constraint with only linear constraints
                            for element in AND_elements:
                                self.model.addConstr(and_var <= element)
                            self.model.addConstr(and_var >= gp.quicksum(AND_elements) - (len(AND_elements) - 1))

                            # XOR is not known only if all the AND elements are unknown
                            self.model.addConstr(XOR_var <= 1 - and_var, name=f"MC_fix_value_0_not_to_1")

                        # in the other setup : forward/lower and backward/upper, we are not using the opposite propagation
                        else:
                            input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                            self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_value_0_not_to_1 (opposite sens)")

        # An output value is known if one of the possible XOR combinations leading to it is known.
        # or_var = 1 iff combination i has at least one unknown input (not computable).
        # 1-or_var = 1 iff combination i is fully computable.
        # output[...,1] = OR(1-or_var_i): output computable iff any combination fully computable.
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MC[sens][round_index%(len(self.matrixes[0]))][row]:
                        or_var = self.model.addVar(vtype=gp.GRB.BINARY, name=f"or_var_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        self.model.addGenConstrOr(or_var, [XOR_in_part[(attack_side_index, sens, round_index, column)+tuple(element)+(0,)] for element in combination], name=f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        or_vars.append(1-or_var)
                for elements in or_vars:
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1] >= elements, name=f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1] <= gp.quicksum(or_vars), name=f"OR_MC_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
    
    def propagation_MR_values(self, part, XOR_in_part, attack_side_index, round_index, input_state_index, output_state_index, row_range):
        sens = int(input_state_index > output_state_index)
        m_index = round_index % len(self.matrixes[sens])

        #First we fix to 0 all the input XOR that cannot be computed
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                for c_vector_element in row_range[m_index]:
                    if c_vector_element[column] == 1:
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, row) + c_vector_element + (1,)]
                        #If propagation is forward in the upper part of bacward for the lower part : we can use the opposite propagation
                        if attack_side_index == sens:
                            # if the considered vector is in MC than we check if it is known form the opposite propagation
                            if c_vector_element in self.matrixes_sets[sens][m_index]:
                                AND_elements = [part[attack_side_index, sens, round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, output_state_index, row, self.matrixes_index_map[sens][m_index][c_vector_element] , 0]]
                            else:
                                AND_elements = [part[attack_side_index, sens, round_index, input_state_index, row, column, 0],
                                            part[attack_side_index, not(sens), round_index, input_state_index, row, column, 0]]

                            and_var = self.model.addVar(vtype=gp.GRB.BINARY, name=f"and_var_MR_side{attack_side_index}_r{round_index}_row{row}_col{column}")

                            # AND constraint with only linear constraints
                            for element in AND_elements:
                                self.model.addConstr(and_var <= element)
                            self.model.addConstr(and_var >= gp.quicksum(AND_elements) - (len(AND_elements) - 1))

                            # XOR is not known only if all the AND elements are unknown
                            self.model.addConstr(XOR_var <= 1 - and_var, name=f"MR_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")

                        # in the other setup : forward/lower and backward/upper, we are not using the opposite propagation
                        else:
                            input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                            self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MR_fix_input_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")

        # An output value is known if one of the possible XOR combinations leading to it is known.
        # or_var = 1 iff combination i has at least one unknown input (not computable).
        # 1-or_var = 1 iff combination i is fully computable.
        # output[...,1] = OR(1-or_var_i): output computable iff any combination fully computable.
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MR[sens][round_index%(len(self.matrixes[0]))][column]:
                        or_var = self.model.addVar(vtype=gp.GRB.BINARY, name=f"or_var_MR_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        self.model.addGenConstrOr(or_var, [XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(index)+(0,)] for index in combination], name=f"OR_MR_part_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        or_vars.append(1-or_var)
                for elements in or_vars:
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1] >= elements, name=f"OR_MR_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1]<= gp.quicksum(or_vars), name = f"OR_MR_part_side{attack_side_index}_r{round_index}_row{row}_col{column}_0_not_to_1")
    
    def propagation_AK(self, part, attack_side_index, subkey_part, round_index, input_state_index, output_state_index):
        #if the state if not known before the AK it cannot be computed after
        sens = int(input_state_index > output_state_index)

        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row, column, 0] +
                                part[attack_side_index, sens,round_index, output_state_index, row, column, 1] <= 1
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_state_not_to_1')
        
        #if the key is not known, the state after AK cannot be computed
        self.model.addConstrs(( part[attack_side_index, sens, round_index, output_state_index, row, column, 1] <= subkey_part[round_index, row, column]
                                for row in range(self.block_row_size) for column in range(self.block_column_size))
                                ,name = 'value_propagation_SK_:_0_in_key_not_to_1')
        
    def propagation_SB_values(self, part, attack_side_index, round_index, input_state_index, output_state_index, sbox_sizes):
        #if you have an unknow value in the input of the sbox all the outputs cannot be computed
        sens = int(input_state_index > output_state_index)

        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row_input, column_input, 0]
                                 + part[attack_side_index, sens, round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 1] <= 1
                                 for row_output in range(self.block_row_size//sbox_sizes[0])
                                 for column_output in range(self.block_column_size//sbox_sizes[1])
                                 for sbox_row in range(sbox_sizes[0])
                                 for sbox_column in range(sbox_sizes[1])
                                 for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                 for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])), 
                                 name='value_propagation_SB_:_0_not_to_1')

    def propagation_values_NR(self, part, attack_side_index, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        if input_round_index < output_round_index:
            self.model.addConstrs((part[attack_side_index, 0, input_round_index, self.state_number-1, row, column, 0]
                                    + part[attack_side_index, 0, output_round_index, 0, row, column, 1] <= 1
                                      for row in range(self.block_row_size) for column in range(self.block_column_size)), 
                                    name='value_propagation_NR_:_0_not_to_1')
        else :
            self.everything_all_right = False
            print("Error in value_propagation_NR: input_round_index should be inferior from output_round_index")

    def propagation_values_PR(self, part, attack_side_index, input_round_index, output_round_index):
        #an unknown value cannot lead to a value that can be computed
        self.model.addConstrs((part[attack_side_index, 1, input_round_index, 0, row, column, 0]
                                + part[attack_side_index, 1, output_round_index, self.state_number-1, row, column, 1] <= 1
                                for row in range(self.block_row_size) 
                                for column in range(self.block_column_size)), 
                                name='value_propagation_PR_:_0_not_to_1')

    def propagation_PB_values(self, part, attack_side_index, round_index, input_state_index, output_state_index, permutation):
        sens = int(input_state_index > output_state_index)
        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                                + part[attack_side_index, sens, round_index, output_state_index, permutation[row*self.block_column_size + column]//self.block_column_size, permutation[row*self.block_column_size + column]%self.block_column_size , 1] <= 1
                                for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                name = "value_propagation_:_PB_0_not_to_1")

    #Propagation of DIFFERENCES through OPERATIONS
    def propagation_SR_differences(self, part, attack_side_index, round_index, input_state_index, output_state_index, shift_rows, propagate_diff_known=True):
        sens = int(input_state_index > output_state_index)
        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row, column, 1]
                                == part[attack_side_index, sens, round_index, output_state_index, row, (column+shift_rows[row])%self.block_column_size, 1]
                                for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                name = "differential propagation :_SR_1_not_to_1")
        if propagate_diff_known:
            # y is conserved (SR is a bijection)
            self.model.addConstrs((self.diff_known[attack_side_index, sens, round_index, input_state_index, row, column]
                                    == self.diff_known[attack_side_index, sens, round_index, output_state_index, row, (column+shift_rows[row])%self.block_column_size]
                                    for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                    name="diff_known_propagation_SR")
    
    def propagation_MC_differences(self, part, XOR_in_part, attack_side_index, round_index, input_state_index, output_state_index, column_range):
        sens = int(input_state_index > output_state_index)
        mc_index = round_index % len(self.matrixes[sens])
        
        #First we fix to 0 all the input XOR that cannot be computed
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                for c_vector_element in column_range[mc_index]:
                    if c_vector_element[row] == 1:
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, column) + c_vector_element + (0,)]
                        input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 1]
                        self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_differences_1_not_to_0")
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, column) + c_vector_element + (2,)]
                        input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 1]
                        self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_differences_1_not_to_2")
                        
        # output[...,1] (inactive) = OR(or_var_i): output is inactive iff any combination is inactive or cancelled.
        # or_var = 1 iff combination i has at least one inactive (value=1) or cancelled (value=2) input.
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MC[sens][round_index%(len(self.matrixes[0]))][row]:
                        or_var = self.model.addVar(vtype=gp.GRB.BINARY, name=f"or_var_MC_diff_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        self.model.addGenConstrOr(or_var, [XOR_in_part[(attack_side_index, sens, round_index, column)+tuple(element)+(1,)] for element in combination] + [XOR_in_part[(attack_side_index, sens, round_index, column)+tuple(element)+(2,)] for element in combination], name=f"OR_MC_diff_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        or_vars.append(or_var)
                for elements in or_vars:
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1] >= elements, name=f"OR_MC_diff_side{attack_side_index}_r{round_index}_row{row}_col{column}_inactive")
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1] <= gp.quicksum(or_vars), name=f"OR_MC_diff_side{attack_side_index}_r{round_index}_row{row}_col{column}_inactive_sum")

        # y propagation through MC:
        # A = physical "before MC" state (min state index), B = "after MC" state (max state index).
        # sens=0 (forward, lower part, differences A→B):
        #   A[a_row] = XOR(B[b_row] for M⁻¹[a_row][b_row]==1)
        #   If A null/y=1 → all contributing B must be known: y(B[b_row]) >= 1-x(A[a_row]) and >= y(A[a_row])
        #   Uses matrixes[1] (M⁻¹), constrains b_state.
        # sens=1 (backward, upper part, differences B→A):
        #   B[b_row] = XOR(A[a_row] for M[b_row][a_row]==1)
        #   If B null/y=1 → all contributing A must be known: y(A[a_row]) >= 1-x(B[b_row]) and >= y(B[b_row])
        #   Uses matrixes[0] (M), constrains a_state.
        a_state = min(input_state_index, output_state_index)
        b_state = max(input_state_index, output_state_index)
        if sens == 0:
            mc_y_idx = round_index % len(self.matrixes[1])
            mc_y_matrix = self.matrixes[1][mc_y_idx]  # M⁻¹
            for a_row in range(self.block_row_size):
                for b_row in range(self.block_row_size):
                    if mc_y_matrix[a_row][b_row] == 1:
                        for column in range(self.block_column_size):
                            self.model.addConstr(
                                self.diff_known[attack_side_index, sens, round_index, b_state, b_row, column] >=
                                1 - part[attack_side_index, sens, round_index, a_state, a_row, column, 1],
                                name=f"diff_known_MC_null_r{round_index}_ar{a_row}_br{b_row}_c{column}")
                            self.model.addConstr(
                                self.diff_known[attack_side_index, sens, round_index, b_state, b_row, column] >=
                                self.diff_known[attack_side_index, sens, round_index, a_state, a_row, column],
                                name=f"diff_known_MC_y_r{round_index}_ar{a_row}_br{b_row}_c{column}")
        else:  # sens == 1
            mc_y_idx = round_index % len(self.matrixes[0])
            mc_y_matrix = self.matrixes[0][mc_y_idx]  # M (forward)
            for b_row in range(self.block_row_size):
                for a_row in range(self.block_row_size):
                    if mc_y_matrix[b_row][a_row] == 1:
                        for column in range(self.block_column_size):
                            self.model.addConstr(
                                self.diff_known[attack_side_index, sens, round_index, a_state, a_row, column] >=
                                1 - part[attack_side_index, sens, round_index, b_state, b_row, column, 1],
                                name=f"diff_known_MC_null_r{round_index}_br{b_row}_ar{a_row}_c{column}")
                            self.model.addConstr(
                                self.diff_known[attack_side_index, sens, round_index, a_state, a_row, column] >=
                                self.diff_known[attack_side_index, sens, round_index, b_state, b_row, column],
                                name=f"diff_known_MC_y_r{round_index}_br{b_row}_ar{a_row}_c{column}")

    def propagation_MR_differences(self, part, XOR_in_part, attack_side_index, round_index, input_state_index, output_state_index, row_range):
        sens = int(input_state_index > output_state_index)
        mr_index = round_index % len(self.matrixes[sens])
        
        #First we fix to 0 all the input XOR that cannot be computed
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                for c_vector_element in row_range[mr_index]:
                    if c_vector_element[column] == 1:
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, row) + c_vector_element + (0,)]
                        input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 1]
                        self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_input_1_not_to_0")
                        XOR_var = XOR_in_part[(attack_side_index, sens, round_index, row) + c_vector_element + (2,)]
                        input_var = part[attack_side_index, sens, round_index, input_state_index, row, column, 1]
                        self.model.addConstr(input_var + XOR_var <= 1,
                                                name=f"MC_fix_input_1_not_to_2")

        # output[..., 1] (inactive) is constrained here.
        # output[..., 0] (active) is deduced automatically via the one-hot constraint
        # differences[..., 0] + differences[..., 1] == 1 from difference_variables_initialisation.
        # or_var = 1 iff combination i has at least one inactive (value=1) or cancelled (value=2) input.
        for row in range(self.block_row_size):
            for column in range(self.block_column_size):
                or_vars = []
                for combination in self.possible_XORs_MR[sens][round_index%(len(self.matrixes[0]))][column]:
                        or_var = self.model.addVar(vtype=gp.GRB.BINARY, name=f"or_var_MR_diff_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        self.model.addGenConstrOr(or_var, [XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(element)+(1,)] for element in combination] + [XOR_in_part[(attack_side_index, sens, round_index, row)+tuple(element)+(2,)] for element in combination], name=f"OR_MR_diff_side{attack_side_index}_r{round_index}_row{row}_col{column}")
                        or_vars.append(or_var)
                for elements in or_vars:
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1] >= elements, name=f"OR_MR_diff_side{attack_side_index}_r{round_index}_row{row}_col{column}_inactive")
                    self.model.addConstr(part[attack_side_index, sens, round_index, output_state_index, row, column, 1] <= gp.quicksum(or_vars), name=f"OR_MR_diff_side{attack_side_index}_r{round_index}_row{row}_col{column}_inactive_sum")

        # y propagation through MR (symmetric to MC fix, but on columns):
        # A = physical "before MR" state (min state index), B = "after MR" state (max state index).
        # sens=0 (forward, lower part, differences A→B):
        #   A[row][a_col] = XOR(B[row][b_col] for M⁻¹[a_col][b_col]==1)
        #   If A null/y=1 → all contributing B must be known: y(B[b_col]) >= 1-x(A[a_col]) and >= y(A[a_col])
        #   Uses matrixes[1] (M⁻¹), constrains b_state.
        # sens=1 (backward, upper part, differences B→A):
        #   B[row][b_col] = XOR(A[row][a_col] for M[b_col][a_col]==1)
        #   If B null/y=1 → all contributing A must be known: y(A[a_col]) >= 1-x(B[b_col]) and >= y(B[b_col])
        #   Uses matrixes[0] (M), constrains a_state.
        a_state = min(input_state_index, output_state_index)
        b_state = max(input_state_index, output_state_index)
        if sens == 0:
            mr_y_idx = round_index % len(self.matrixes[1])
            mr_y_matrix = self.matrixes[1][mr_y_idx]  # M⁻¹
            for a_col in range(self.block_column_size):
                for b_col in range(self.block_column_size):
                    if mr_y_matrix[a_col][b_col] == 1:
                        for row in range(self.block_row_size):
                            self.model.addConstr(
                                self.diff_known[attack_side_index, sens, round_index, b_state, row, b_col] >=
                                1 - part[attack_side_index, sens, round_index, a_state, row, a_col, 1],
                                name=f"diff_known_MR_null_r{round_index}_ac{a_col}_bc{b_col}_row{row}")
                            self.model.addConstr(
                                self.diff_known[attack_side_index, sens, round_index, b_state, row, b_col] >=
                                self.diff_known[attack_side_index, sens, round_index, a_state, row, a_col],
                                name=f"diff_known_MR_y_r{round_index}_ac{a_col}_bc{b_col}_row{row}")
        else:  # sens == 1
            mr_y_idx = round_index % len(self.matrixes[0])
            mr_y_matrix = self.matrixes[0][mr_y_idx]  # M (forward)
            for b_col in range(self.block_column_size):
                for a_col in range(self.block_column_size):
                    if mr_y_matrix[b_col][a_col] == 1:
                        for row in range(self.block_row_size):
                            self.model.addConstr(
                                self.diff_known[attack_side_index, sens, round_index, a_state, row, a_col] >=
                                1 - part[attack_side_index, sens, round_index, b_state, row, b_col, 1],
                                name=f"diff_known_MR_null_r{round_index}_bc{b_col}_ac{a_col}_row{row}")
                            self.model.addConstr(
                                self.diff_known[attack_side_index, sens, round_index, a_state, row, a_col] >=
                                self.diff_known[attack_side_index, sens, round_index, b_state, row, b_col],
                                name=f"diff_known_MR_y_r{round_index}_bc{b_col}_ac{a_col}_row{row}")

    def propagation_SB_differences(self, part, attack_side_index, round_index, input_state_index, output_state_index, sbox_sizes):
        #if you have an unknow value in the input of the sbox all the outputs cannot be computed
        sens = int(input_state_index > output_state_index)
        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row_input, column_input, 1]
                                    <= part[attack_side_index, sens, round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 1]
                                    for row_output in range(self.block_row_size//sbox_sizes[0])
                                    for column_output in range(self.block_column_size//sbox_sizes[1])
                                    for sbox_row in range(sbox_sizes[0])
                                    for sbox_column in range(sbox_sizes[1])
                                    for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                    for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])), 
                                    name='value_propagation_SB_:_0_not_to_1')

        # If y=1 for an output word of a SBox AND the corresponding input word is active,
        # then the input word's value must be known in the opposite direction (known or state_test).
        # Linearized form of: diff_known[out] * part[in, active] <= values[opposite, in, 1] + values[opposite, in, 2]
        # → diff_known[out] + part[in, active] - 1 <= values[opposite, in, 1] + values[opposite, in, 2]
        # Applied to ALL (output word, input word) pairs within the same SBox group.
        self.model.addConstrs((
                                self.diff_known[attack_side_index, sens, round_index, output_state_index,
                                               sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_col]
                                + part[attack_side_index, sens, round_index, input_state_index,
                                       sbox_sizes[0]*row_output + in_row, sbox_sizes[1]*column_output + in_col, 1]
                                - 1
                                <=
                                self.values[attack_side_index, not(sens), round_index, input_state_index,
                                            sbox_sizes[0]*row_output + in_row, sbox_sizes[1]*column_output + in_col, 1]
                                + self.values[attack_side_index, not(sens), round_index, input_state_index,
                                              sbox_sizes[0]*row_output + in_row, sbox_sizes[1]*column_output + in_col, 2]
                                for row_output in range(self.block_row_size // sbox_sizes[0])
                                for column_output in range(self.block_column_size // sbox_sizes[1])
                                for sbox_row in range(sbox_sizes[0])
                                for sbox_col in range(sbox_sizes[1])
                                for in_row in range(sbox_sizes[0])
                                for in_col in range(sbox_sizes[1])),
                                name='diff_known_SB_requires_value')
        
        # y is conserved through SB (bijection within each sbox group)
        self.model.addConstrs((self.diff_known[attack_side_index, sens, round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column] >=
                                self.diff_known[attack_side_index, sens, round_index, input_state_index, sbox_sizes[0]*row_output + input_row, sbox_sizes[1]*column_output + input_column]
                                for row_output in range(self.block_row_size//sbox_sizes[0])
                                for column_output in range(self.block_column_size//sbox_sizes[1])
                                for sbox_row in range(sbox_sizes[0])
                                for sbox_column in range(sbox_sizes[1])
                                for input_row in range(sbox_sizes[0])
                                for input_column in range(sbox_sizes[1])),
                                name='diff_known_propagation_SB')
    
    def propagation_SB_differences_structure(self, part, attack_side_index, round_index, input_state_index, output_state_index, sbox_sizes, propagate_diff_known=True):
        #if you have an unknow value in the input of the sbox all the outputs cannot be computed
        sens = int(input_state_index > output_state_index)

        self.model.addConstrs((part[attack_side_index, sens, round_index, output_state_index, row_input, column_input, 0]
                                >= part[attack_side_index, sens, round_index, input_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 0]
                                for row_output in range(self.block_row_size//sbox_sizes[0])
                                for column_output in range(self.block_column_size//sbox_sizes[1])
                                for sbox_row in range(sbox_sizes[0])
                                for sbox_column in range(sbox_sizes[1])
                                for row_input in range(sbox_sizes[0]*row_output, sbox_sizes[0]*row_output + sbox_sizes[0])
                                for column_input in range(sbox_sizes[1]*column_output, sbox_sizes[1]*column_output+sbox_sizes[1])),
                                name='value_propagation_SB_:_0_not_to_1')

        # Unconditional: active output difference requires knowing ALL input values of the SBox group.
        # Without this, differences could propagate through SBox without value knowledge.
        self.model.addConstrs((
                                part[attack_side_index, sens, round_index, output_state_index,
                                     sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_col, 1]
                                <=
                                self.value_in_structure[attack_side_index, not(attack_side_index), round_index, input_state_index,
                                                        sbox_sizes[0]*row_output + in_row, sbox_sizes[1]*column_output + in_col, 1]
                                + self.value_in_structure[attack_side_index, not(attack_side_index), round_index, input_state_index,
                                                          sbox_sizes[0]*row_output + in_row, sbox_sizes[1]*column_output + in_col, 2]
                                for row_output in range(self.block_row_size // sbox_sizes[0])
                                for column_output in range(self.block_column_size // sbox_sizes[1])
                                for sbox_row in range(sbox_sizes[0])
                                for sbox_col in range(sbox_sizes[1])
                                for in_row in range(sbox_sizes[0])
                                for in_col in range(sbox_sizes[1])),
                                name='active_diff_requires_known_value_structure')

        if propagate_diff_known:
            # If y=1 for a word at SB output (in structure), its value must be known from the matching direction
            self.model.addConstrs((self.diff_known[attack_side_index, sens, round_index, output_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column] <=
                                    self.value_in_structure[attack_side_index, not(attack_side_index), round_index, input_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 1]
                                    + self.values[attack_side_index, sens, round_index, input_state_index, sbox_sizes[0]*row_output + sbox_row, sbox_sizes[1]*column_output + sbox_column, 2]
                                    for row_output in range(self.block_row_size//sbox_sizes[0])
                                    for column_output in range(self.block_column_size//sbox_sizes[1])
                                    for sbox_row in range(sbox_sizes[0])
                                    for sbox_column in range(sbox_sizes[1])),
                                    name='diff_known_SB_structure_requires_value')
            # y is conserved through SB (bijection)
            self.model.addConstrs((self.diff_known[attack_side_index, sens, round_index, output_state_index, row, column] ==
                                    self.diff_known[attack_side_index, sens, round_index, input_state_index, row, column]
                                    for row in range(self.block_row_size)
                                    for column in range(self.block_column_size)),
                                    name='diff_known_propagation_SB_structure')

    def propagation_differences_NR(self, part, attack_side_index, input_round_index, output_round_index, propagate_diff_known=True):
        #an unknown value cannot lead to a value that can be computed
        if input_round_index < output_round_index:
            self.model.addConstrs((part[attack_side_index, 0, input_round_index, self.state_number-1, row, column, 1]
                                    == part[attack_side_index, 0, output_round_index, 0, row, column, 1]
                                      for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                    name='value_propagation_NR_:_0_not_to_1')
            if propagate_diff_known:
                # y is conserved between rounds (forward)
                self.model.addConstrs((self.diff_known[attack_side_index, 0, input_round_index, self.state_number-1, row, column]
                                        == self.diff_known[attack_side_index, 0, output_round_index, 0, row, column]
                                          for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                        name='diff_known_propagation_NR')
        else :
            self.everything_all_right = False
            print("Error in value_propagation_NR: input_round_index should be inferior from output_round_index")

    def propagation_differences_PR(self, part, attack_side_index, input_round_index, output_round_index, propagate_diff_known=True):
        #an unknown value cannot lead to a value that can be computed
        self.model.addConstrs((part[attack_side_index, 1, input_round_index, 0, row, column, 1]
                                == part[attack_side_index, 1, output_round_index, self.state_number-1, row, column, 1]
                                for row in range(self.block_row_size)
                                for column in range(self.block_column_size)),
                                name='value_propagation_PR_:_0_not_to_1')
        if propagate_diff_known:
            # y is conserved between rounds (backward)
            self.model.addConstrs((self.diff_known[attack_side_index, 1, input_round_index, 0, row, column]
                                    == self.diff_known[attack_side_index, 1, output_round_index, self.state_number-1, row, column]
                                    for row in range(self.block_row_size)
                                    for column in range(self.block_column_size)),
                                    name='diff_known_propagation_PR')

    def free_propagation(self, part, attack_side_index, round_index, input_state_index, output_state_index, propagate_diff_known=True):
        sens = int(input_state_index > output_state_index)
        self.model.addConstrs((part[attack_side_index, sens, round_index, output_state_index, row, column, 0]
                               == part[attack_side_index, sens, round_index, input_state_index, row, column, 0]
                              for row in range(self.block_row_size)
                              for column in range(self.block_column_size)), name="propagation_simple")
        if propagate_diff_known:
            # y is conserved through AK (free propagation = bijection)
            self.model.addConstrs((self.diff_known[attack_side_index, sens, round_index, output_state_index, row, column]
                                   == self.diff_known[attack_side_index, sens, round_index, input_state_index, row, column]
                                  for row in range(self.block_row_size)
                                  for column in range(self.block_column_size)), name="diff_known_propagation_AK")

    def propagation_PB_differences(self, part, attack_side_index, round_index, input_state_index, output_state_index, permutation, propagate_diff_known=True):
        sens = int(input_state_index > output_state_index)
        self.model.addConstrs((part[attack_side_index, sens, round_index, input_state_index, row, column, 1]
                                == part[attack_side_index, sens, round_index, output_state_index, permutation[row*self.block_column_size + column]//self.block_column_size, permutation[row*self.block_column_size + column]%self.block_column_size , 1]
                                for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                name = "differential_propagation_:_PB_0_not_to_1")
        if propagate_diff_known:
            # y is conserved through PB (bijection)
            self.model.addConstrs((self.diff_known[attack_side_index, sens, round_index, input_state_index, row, column]
                                    == self.diff_known[attack_side_index, sens, round_index, output_state_index, permutation[row*self.block_column_size + column]//self.block_column_size, permutation[row*self.block_column_size + column]%self.block_column_size]
                                    for row in range(self.block_row_size) for column in range(self.block_column_size)),
                                    name="diff_known_propagation_PB")
        
    #Propagation of values in rounds
    def forward_values_propagation(self, attack_side_index, first_round_index, last_round_index, subkey):
        op_order = self.operation_order_up if attack_side_index == 0 else self.operation_order_down
        condition = False
        if self.alpha_reflection and first_round_index > self.total_rounds:
            if 'SR' in op_order:
                shift_rows = self.shift_rows_inverse
            if 'PB' in op_order:
                permutations = self.permutations_inverse
            if 'MC' in op_order or 'MR' in op_order:
                sens = 1
        else :
            if 'SR' in op_order:
                shift_rows = self.shift_rows
            if 'PB' in op_order:
                permutations = self.permutations
            if 'MC' in op_order or 'MR' in op_order:
                sens = 0
        for forward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if op_order[state_index] == 'SR' and condition:
                    self.propagation_SR_values(self.values, attack_side_index, forward_round, state_index, state_index + 1, shift_rows)
                elif op_order[state_index] == 'PB' and condition:
                    self.propagation_PB_values(self.values, attack_side_index, forward_round, state_index, state_index + 1, permutations[forward_round%len(self.permutations)])
                elif op_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.values, self.XOR_in_mc_values, attack_side_index, forward_round, state_index, state_index + 1, self.column_range[sens])
                elif op_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.values, self.XOR_in_mr_values, attack_side_index, forward_round, state_index, state_index + 1, self.row_range[sens])
                elif op_order[state_index] == 'SB' and condition:
                    self.propagation_SB_values(self.values, attack_side_index, forward_round, state_index, state_index + 1, self.sbox_sizes)
                elif op_order[state_index] == 'AK':
                    if forward_round == first_round_index :
                        condition = True
                    if forward_round == last_round_index :
                        condition = False
                    self.propagation_AK(self.values, attack_side_index, subkey, forward_round, state_index, state_index + 1)
               #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the upper part value propagation")
            if forward_round != last_round_index:
                self.propagation_values_NR(self.values, attack_side_index, forward_round, forward_round+1)

    def backward_values_propagation(self, attack_side_index, first_round_index, last_round_index, subkey):
        op_order = self.operation_order_up if attack_side_index == 0 else self.operation_order_down
        if self.alpha_reflection and first_round_index > self.total_rounds:
            if 'SR' in op_order:
                shift_rows = self.shift_rows
            if 'PB' in op_order:
                permutations = self.permutations
            if 'MC' in op_order or 'MR' in op_order:
                sens = 0
        else :
            if 'SR' in op_order:
                shift_rows = self.shift_rows_inverse
            if 'PB' in op_order:
                permutations = self.permutations_inverse
            if 'MC' in op_order or 'MR' in op_order:
                sens = 1
        condition = False
        for backward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if op_order[state_index] == 'SR' and condition:
                    self.propagation_SR_values(self.values, attack_side_index, backward_round, state_index + 1, state_index, shift_rows)
                elif op_order[state_index] == 'PB' and condition:
                    self.propagation_PB_values(self.values, attack_side_index, backward_round, state_index + 1, state_index, permutations[backward_round%len(self.permutations)])
                elif op_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.values, self.XOR_in_mc_values, attack_side_index, backward_round, state_index + 1, state_index, self.column_range[sens])
                elif op_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.values, self.XOR_in_mr_values, attack_side_index, backward_round, state_index + 1, state_index, self.row_range[sens])
                elif op_order[state_index] == 'SB' and condition:
                    self.propagation_SB_values(self.values, attack_side_index, backward_round, state_index + 1, state_index, self.sbox_sizes)
                elif op_order[state_index] == 'AK':
                    if backward_round == first_round_index :
                        condition = True
                    if backward_round == last_round_index :
                        condition = False
                    self.propagation_AK(self.values, attack_side_index, subkey, backward_round, state_index + 1, state_index)
                #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the lower part value propagation")
            if backward_round != last_round_index:
                self.propagation_values_PR(self.values, attack_side_index, backward_round+1, backward_round)
    
    def forward_values_propagation_in_structure(self, attack_side_index, first_round_index, last_round_index, subkey):
        op_order = self.operation_order_up if attack_side_index == 0 else self.operation_order_down
        if self.alpha_reflection and first_round_index > self.total_rounds:
            if 'SR' in op_order:
                shift_rows = self.shift_rows_inverse
            if 'PB' in op_order:
                permutations = self.permutations_inverse
            if 'MC' in op_order or 'MR' in op_order:
                sens = 1
        else :
            if 'SR' in op_order:
                shift_rows = self.shift_rows
            if 'PB' in op_order:
                permutations = self.permutations
            if 'MC' in op_order or 'MR' in op_order:
                sens = 0
        condition = False
        for forward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if op_order[state_index] == 'SR' and condition:
                    self.propagation_SR_values(self.value_in_structure, attack_side_index, forward_round, state_index, state_index + 1, shift_rows)
                elif op_order[state_index] == 'PB' and condition:
                    self.propagation_PB_values(self.value_in_structure, attack_side_index, forward_round, state_index, state_index + 1, permutations[forward_round%len(self.permutations)])
                elif op_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.value_in_structure, self.XOR_in_mc_values, attack_side_index, forward_round, state_index, state_index + 1, self.column_range[sens])
                elif op_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.value_in_structure, self.XOR_in_mr_values, attack_side_index, forward_round, state_index, state_index + 1, self.row_range[sens])
                elif op_order[state_index] == 'SB' and condition:
                    self.propagation_SB_values(self.value_in_structure, attack_side_index, forward_round, state_index, state_index + 1, self.sbox_sizes)
                elif op_order[state_index] == 'AK':
                    if forward_round == first_round_index :
                        condition = True
                    if forward_round == last_round_index :
                        condition = False
                    self.propagation_AK(self.value_in_structure, attack_side_index, subkey, forward_round, state_index, state_index + 1)
               #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the upper part value propagation")
            if forward_round != last_round_index:
                self.propagation_values_NR(self.value_in_structure, attack_side_index, forward_round, forward_round+1)

    def backward_values_propagation_in_structure(self, attack_side_index, first_round_index, last_round_index, subkey):
        op_order = self.operation_order_up if attack_side_index == 0 else self.operation_order_down
        if self.alpha_reflection and first_round_index > self.total_rounds:
            if 'SR' in op_order:
                shift_rows = self.shift_rows
            if 'PB' in op_order:
                permutations = self.permutations
            if 'MC' in op_order or 'MR' in op_order:
                sens = 0
        else :
            if 'SR' in op_order:
                shift_rows = self.shift_rows_inverse
            if 'PB' in op_order:
                permutations = self.permutations_inverse
            if 'MC' in op_order or 'MR' in op_order:
                sens = 1
        condition = False
        for backward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if op_order[state_index] == 'SR' and condition:
                    self.propagation_SR_values(self.value_in_structure, attack_side_index, backward_round, state_index + 1, state_index, shift_rows)
                elif op_order[state_index] == 'PB' and condition:
                    self.propagation_PB_values(self.value_in_structure, attack_side_index, backward_round, state_index + 1, state_index, permutations[backward_round%len(self.permutations)])
                elif op_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.value_in_structure, self.XOR_in_mc_values, attack_side_index, backward_round, state_index + 1, state_index, self.column_range[sens])
                elif op_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.value_in_structure, self.XOR_in_mr_values, attack_side_index, backward_round, state_index + 1, state_index, self.row_range[sens])
                elif op_order[state_index] == 'SB' and condition:
                    self.propagation_SB_values(self.value_in_structure, attack_side_index, backward_round, state_index + 1, state_index, self.sbox_sizes)
                elif op_order[state_index] == 'AK':
                    if backward_round == first_round_index :
                        condition = True
                    if backward_round == last_round_index :
                        condition = False
                    self.propagation_AK(self.value_in_structure, attack_side_index, subkey, backward_round, state_index + 1, state_index)
                #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the lower part value propagation")
            if backward_round != last_round_index:
                self.propagation_values_PR(self.value_in_structure, attack_side_index, backward_round+1, backward_round)
    
    #Propagation of differences in upper and lower parts
    def forward_differences_propagation(self, attack_side_index, first_round_index, last_round_index):
        op_order = self.operation_order_up if attack_side_index == 0 else self.operation_order_down
        if self.alpha_reflection and first_round_index > self.total_rounds:
            if 'SR' in op_order:
                shift_rows = self.shift_rows_inverse
            if 'PB' in op_order:
                permutations = self.permutations_inverse
            if 'MC' in op_order or 'MR' in op_order:
                sens = 1
        else :
            if 'SR' in op_order:
                shift_rows = self.shift_rows
            if 'PB' in op_order:
                permutations = self.permutations
            if 'MC' in op_order or 'MR' in op_order:
                sens = 0
        condition = False
        for forward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if op_order[state_index] == 'SR' and condition:
                    self.propagation_SR_differences(self.differences, attack_side_index, forward_round, state_index, state_index + 1, shift_rows)
                elif op_order[state_index] == 'PB' and condition:
                    self.propagation_PB_differences(self.differences, attack_side_index, forward_round, state_index, state_index +1, permutations[forward_round%len(self.permutations)])
                elif op_order[state_index] == 'MC' and condition:
                    self.propagation_MC_differences(self.differences, self.XOR_in_mc_differences, attack_side_index, forward_round, state_index, state_index + 1, self.column_range[sens])
                elif op_order[state_index] == 'MR' and condition:
                    self.propagation_MR_differences(self.differences, self.XOR_in_mr_differences, attack_side_index, forward_round, state_index, state_index + 1, self.row_range[sens])
                elif op_order[state_index] == 'SB':
                    if forward_round == first_round_index :
                        condition = True
                    if forward_round == last_round_index :
                        condition = False
                    self.propagation_SB_differences(self.differences, attack_side_index, forward_round, state_index, state_index + 1, self.sbox_sizes)
                elif op_order[state_index] == 'AK' and condition:
                    self.free_propagation(self.differences, attack_side_index, forward_round, state_index, state_index + 1)
               #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the upper part value propagation")
            if forward_round != last_round_index:
                self.propagation_differences_NR(self.differences, attack_side_index, forward_round, forward_round+1)
    
    def backward_differences_propagation(self, attack_side_index, first_round_index, last_round_index):
        op_order = self.operation_order_up if attack_side_index == 0 else self.operation_order_down
        if self.alpha_reflection and first_round_index > self.total_rounds:
            if 'SR' in op_order:
                shift_rows = self.shift_rows
            if 'PB' in op_order:
                permutations = self.permutations
            if 'MC' in op_order or 'MR' in op_order:
                sens = 0
        else :
            if 'SR' in op_order:
                shift_rows = self.shift_rows_inverse
            if 'PB' in op_order:
                permutations = self.permutations_inverse
            if 'MC' in op_order or 'MR' in op_order:
                sens = 1
        condition = False
        for backward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if op_order[state_index] == 'SR' and condition:
                    self.propagation_SR_differences(self.differences, attack_side_index, backward_round, state_index + 1, state_index, shift_rows)
                elif op_order[state_index] == 'PB' and condition:
                    self.propagation_PB_differences(self.differences, attack_side_index, backward_round, state_index +1, state_index, permutations[backward_round%len(self.permutations)])
                elif op_order[state_index] == 'MC' and condition:
                    self.propagation_MC_differences(self.differences, self.XOR_in_mc_differences, attack_side_index, backward_round, state_index + 1, state_index, self.column_range[sens])
                elif op_order[state_index] == 'MR' and condition:
                    self.propagation_MR_differences(self.differences, self.XOR_in_mr_differences, attack_side_index, backward_round, state_index + 1, state_index, self.row_range[sens])
                elif op_order[state_index] == 'SB' :
                    if backward_round == first_round_index :
                        condition = True
                    if backward_round == last_round_index :
                        condition = False
                    if backward_round != self.upper_part_last_round:
                        self.propagation_SB_differences(self.differences, attack_side_index, backward_round, state_index + 1, state_index, self.sbox_sizes)
                elif op_order[state_index] == 'AK' and condition:
                    self.free_propagation(self.differences, attack_side_index, backward_round, state_index + 1, state_index)
                #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the lower part value propagation")
            if backward_round != last_round_index:
                self.propagation_differences_PR(self.differences, attack_side_index, backward_round+1, backward_round)
    
    #Propagation of differences in structure :
    def forward_differences_propagation_in_structure(self, attack_side_index, first_round_index, last_round_index):
        op_order = self.operation_order_up if attack_side_index == 0 else self.operation_order_down
        if self.alpha_reflection and first_round_index > self.total_rounds:
            if 'SR' in op_order:
                shift_rows = self.shift_rows_inverse
            if 'PB' in op_order:
                permutations = self.permutations_inverse
            if 'MC' in op_order or 'MR' in op_order:
                sens = 1
        else :
            if 'SR' in op_order:
                shift_rows = self.shift_rows
            if 'PB' in op_order:
                permutations = self.permutations
            if 'MC' in op_order or 'MR' in op_order:
                sens = 0
        condition = False
        for forward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if op_order[state_index] == 'SR' and condition:
                    self.propagation_SR_differences(self.differences, attack_side_index, forward_round, state_index, state_index + 1, shift_rows, propagate_diff_known=False)
                elif op_order[state_index] == 'PB' and condition:
                    self.propagation_PB_differences(self.differences, attack_side_index, forward_round, state_index, state_index +1, permutations[forward_round%len(self.permutations)], propagate_diff_known=False)
                elif op_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.differences, self.XOR_in_mc_differences, attack_side_index, forward_round, state_index, state_index + 1, self.column_range[sens])
                elif op_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.differences, self.XOR_in_mr_differences, attack_side_index, forward_round, state_index, state_index + 1, self.row_range[sens])
                elif op_order[state_index] == 'SB' and condition:
                    self.propagation_SB_differences_structure(self.differences, attack_side_index, forward_round, state_index, state_index + 1, self.sbox_sizes, propagate_diff_known=False)
                elif op_order[state_index] == 'AK':
                    if forward_round == first_round_index :
                        condition = True
                    if forward_round == last_round_index :
                        condition = False
                    self.free_propagation(self.differences, attack_side_index, forward_round, state_index, state_index + 1, propagate_diff_known=False)
               #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the upper part value propagation")
            if forward_round != last_round_index:
                self.propagation_differences_NR(self.differences, attack_side_index, forward_round, forward_round+1, propagate_diff_known=False)
    
    def backward_differences_propagation_in_structure(self, attack_side_index, first_round_index, last_round_index):
        op_order = self.operation_order_up if attack_side_index == 0 else self.operation_order_down
        if self.alpha_reflection and first_round_index > self.total_rounds:
            if 'SR' in op_order:
                shift_rows = self.shift_rows
            if 'PB' in op_order:
                permutations = self.permutations
            if 'MC' in op_order or 'MR' in op_order:
                sens = 0
        else :
            if 'SR' in op_order:
                shift_rows = self.shift_rows_inverse
            if 'PB' in op_order:
                permutations = self.permutations_inverse
            if 'MC' in op_order or 'MR' in op_order:
                sens = 1
        condition = False
        for backward_round in range(first_round_index, last_round_index+1):
            for state_index in range(self.state_number-1):
                if op_order[state_index] == 'SR' and condition:
                    self.propagation_SR_differences(self.differences, attack_side_index, backward_round, state_index + 1, state_index, shift_rows, propagate_diff_known=False)
                elif op_order[state_index] == 'PB' and condition:
                    self.propagation_PB_differences(self.differences, attack_side_index, backward_round, state_index+1, state_index, permutations[backward_round%len(self.permutations)], propagate_diff_known=False)
                elif op_order[state_index] == 'MC' and condition:
                    self.propagation_MC_values(self.differences, self.XOR_in_mc_differences, attack_side_index, backward_round, state_index + 1, state_index, self.column_range[sens])
                elif op_order[state_index] == 'MR' and condition:
                    self.propagation_MR_values(self.differences, self.XOR_in_mr_differences, attack_side_index, backward_round, state_index + 1, state_index, self.row_range[sens])
                elif op_order[state_index] == 'SB' and condition:
                    self.propagation_SB_differences_structure(self.differences, attack_side_index, backward_round, state_index + 1, state_index, self.sbox_sizes, propagate_diff_known=False)
                elif op_order[state_index] == 'AK':
                    if backward_round == first_round_index :
                        condition = True
                    if backward_round == last_round_index :
                        condition = False
                    self.free_propagation(self.differences, attack_side_index, backward_round, state_index + 1, state_index, propagate_diff_known=False)
                #else :
                    #self.everything_all_right = False
                    #print("One of the round operator name is not recognized in the lower part value propagation")
            if backward_round != last_round_index:
                self.propagation_differences_PR(self.differences, attack_side_index, backward_round+1, backward_round, propagate_diff_known=False)

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



