cipher_parameters = {
    #cipher parameters
    "Cipher_name": 'SKINNY',

    #block parameters
    "block_size": 64,
    "column_size": 4,
    "row_size": 4,

    #key parameters
    "key_size": 192,
    "key_column_size": 4,
    "key_row_size": 4,

    #Round function parameters
    "operation_order": ['AK', 'SR', 'MC', 'SB'],
    "shift_rows": [0, 1, 2, 3],
    "mix_columns": [[1, 0, 1, 1], [1, 0, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0]],
    "sbox_sizes": [1, 1]
}    