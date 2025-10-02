# This file contains all the parameters for the MILP model and the display function
# that are used to find the attack against 24 rounds of SIMON 32-64

attack_parameters = {
    "block_size" :32,
    "key_size" : 64, 

    "distinguisher_size" : 14,
    "distinguisher_probability" : 30.06, 
    "distinguisher_active_input_bits" : [31],
    "distinguisher_active_output_bits" : [15],

    "structure_size" : 2,
    "upper_part_size" : 4,
    "lower_part_size" : 4,
    
    "first_branch_shift" : 0,
    "second_branch_shift" : 5, 
    "third_branch_shift" : 1,

    "key_schedule_linearity" : 0,
    "state_test" : 1,
    "probabilistic_key_recovery" : 1,

    "pdf_display" : 1,
    "pdf_name" : "24_rounds_SIMECK_32-64"
}
