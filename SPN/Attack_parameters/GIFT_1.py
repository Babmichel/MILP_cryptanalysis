attack_parameters = {
    #Cipher parameters
    "Cipher": "GIFT",
    "Key_schedule": "GIFT",
    "attack_type": "Diff-MITM",
    "structure_position": "upper",

    #Attack sizes
    "structure_rounds": 2,
    "upper_rounds": 4,
    "lower_rounds": 3,

    #Distinguisher parameters
    "distinguisher_probability" : 57.82,
    "distinguisher_rounds" : 13,
    "key_space_size": 124,
    "distinguisher_inputs" : [[0, 54], [0, 62]],
    "distinguisher_outputs": [[0, 31], [0, 29], [0, 63], [0, 61]],

    #Use exponential complexity(can turn the search to impossible)
    "optimal_complexity": False,

    #Attack parameters
    "truncated_differential" : False,
    "state_test_use": False,
    "filter_state_test": False,

    #Upper bound parameters
    "use_upper_bound" : False,
    "known_upper_bound" : 64,

    #Specific Solution search
    "specific_solution_search" : False,
    "solution_value" : 64,

    #Filter extra key guess
    "filter_extra_key_guess" : False,

    #specific key filtering
    "specific_key_filtering" : False,
}
