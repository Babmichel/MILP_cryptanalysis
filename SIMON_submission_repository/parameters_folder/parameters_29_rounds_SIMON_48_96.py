# This file contains all the parameters for the MILP model and the display function
# that are used to find the attack against 29 rounds of SIMON 48-96

attack_parameters = {
    "block_size" :48,
    "key_size" : 96, 

    "distinguisher_size" : 17,
    "distinguisher_probability" : 45.49, 
    "distinguisher_active_input_bits" : [24],
    "distinguisher_active_output_bits" : [0],

    "structure_size" : 3,
    "upper_part_size" : 5,
    "lower_part_size" : 4,
    
    "first_branch_shift" : 8,
    "second_branch_shift" : 1, 
    "third_branch_shift" : 2,

    "key_schedule_linearity" : 1,
    "state_test" : 1,
    "probabilistic_key_recovery" : 1,

    "pdf_display" : 1,
    "pdf_name" : "29_rounds_SIMON_48-96"
}
