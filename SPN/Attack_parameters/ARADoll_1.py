attack_parameters = {
    "Cipher": "ARADoll",
    "Key_schedule": "ARADI",
    "attack_type": "Diff-MITM",
    "structure_rounds": 2,
    "upper_rounds": 2,
    "lower_rounds": 2,
    "distinguisher_probability" : 8,
    "distinguisher_rounds" : 2, 
    "key_space_size": 64,
    "distinguisher_inputs" : [[0, 3],[0, 4],[0, 5]],
    "distinguisher_outputs": [[0, 0], [0, 5], [0, 6]],
    "optimal_complexity": False,
    "truncated_differential" : False,
    "filter_state_test": True
}