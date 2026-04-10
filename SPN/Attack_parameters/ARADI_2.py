attack_parameters = {
    #Cipher parameters
    "Cipher": "ARADI",
    "Key_schedule": "ARADI",
    "attack_type": "MITM",
    "structure_position": "upper",

    #Attack sizes
    "structure_rounds": 1,
    "upper_rounds": 2,
    "lower_rounds": 2,

    #Distinguisher parameters
    "distinguisher_probability" : 60.5,
    "distinguisher_rounds" : 15,
    "key_space_size": 128,
    "distinguisher_inputs" : [[0, 5], [0, 12], [1, 5]],
    "distinguisher_outputs": [[0, 6]],

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
