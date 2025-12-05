attack_parameters = {
    "Cipher": "GIFT",
    "Key_schedule": "GIFT",
    "attack_type": "Diff-MITM",
    "structure_rounds": 2,
    "upper_rounds": 4,
    "lower_rounds": 3,
    "distinguisher_probability" : 58,
    "distinguisher_rounds" : 18, 
    "key_space_size": 120,
    "distinguisher_inputs" : [[0, 18], [0, 19]],
    "distinguisher_outputs": [[0, 3], [0, 5], [0, 33], [0, 39]],
    "optimal_complexity": True,
    "truncated_differential" : False
}