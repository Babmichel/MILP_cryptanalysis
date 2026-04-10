cipher_parameters = {
    #cipher parameters
    "Cipher_name": 'RECTANGLE',

    #block parameters
    "block_size": 64,
    "column_size": 16,
    "row_size": 4,

    #key parameters
    "key_size": 128,
    "key_column_size": 16,
    "key_row_size": 4,

    #Round function parameters
    "operation_order": ['AK', 'SB', 'SR'],
    "shift_rows": [0, 1, 2, 3],
    "sbox_sizes": [4,1]
}    