attack_parameters = {
    #Cipher parameters
    "Cipher": "ARADI",
    "Key_schedule": "ARADI",
    "attack_type": "Diff-MITM",
    "structure_position": "upper",

    #Attack sizes
    "structure_rounds": 2,
    "upper_rounds": 2,
    "lower_rounds": 2,

    #Distinguisher parameters
    "distinguisher_probability" : 123,
    "distinguisher_rounds" : 9,
    "key_space_size": 256,
    "distinguisher_inputs" : [[1, 0], [1, 19], [1, 30]],
    "distinguisher_outputs": [[0, 4], [0, 9], [0, 27]],

    #Use exponential complexity(can turn the search to impossible)
    "optimal_complexity": False,

    #Attack parameters
    "truncated_differential" : False,
    "state_test_use": False,
    "filter_state_test": True,

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
