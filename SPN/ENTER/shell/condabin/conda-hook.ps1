$Env:CONDA_EXE = "/home/bamichel/Documents/MILP_cryptanalysis/SPN/ENTER/bin/conda"
$Env:_CONDA_EXE = "/home/bamichel/Documents/MILP_cryptanalysis/SPN/ENTER/bin/conda"
$Env:_CE_M = $null
$Env:_CE_CONDA = $null
$Env:CONDA_PYTHON_EXE = "/home/bamichel/Documents/MILP_cryptanalysis/SPN/ENTER/bin/python"
$Env:_CONDA_ROOT = "/home/bamichel/Documents/MILP_cryptanalysis/SPN/ENTER"
$CondaModuleArgs = @{ChangePs1 = $True}

Import-Module "$Env:_CONDA_ROOT\shell\condabin\Conda.psm1" -ArgumentList $CondaModuleArgs

Remove-Variable CondaModuleArgs