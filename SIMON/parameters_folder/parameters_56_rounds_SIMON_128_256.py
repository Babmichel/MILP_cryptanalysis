# This file contains all the parameters for the MILP model and the display function
# that are used to find the attack against 36 rounds of SIMON 64-128

attack_parameters = {
    "block_size" :128,
    "key_size" : 256, 

    "distinguisher_size" : 41,
    "distinguisher_probability" : 113, 
    "distinguisher_active_input_bits" : [6, 64, 68, 72],
    "distinguisher_active_output_bits" : [0, 4, 8, 70],

    "structure_size" : 3,
    "upper_part_size" : 6,
    "lower_part_size" : 6,
    
    "first_branch_shift" : 8,
    "second_branch_shift" : 1, 
    "third_branch_shift" : 2,

    "key_schedule_linearity" : 1,
    "state_test" : 1,
    "probabilistic_key_recovery" : 1,
    "non_free_access_model" : 1,

    "pdf_display" : 1,
    "pdf_name" : "56_rounds_SIMON_128-256"
}