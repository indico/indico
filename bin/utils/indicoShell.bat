:: indicoShell.bat
:: Launches the indico shell
::
:: For emacs (.emacs):
::(setq ipython-command "/home/pferreir/projects/indico/dev-utils/indicoShell.sh")
::(setq py-python-command-args '("--production-database"))
@echo off

set INDICOPATH=~\workspace\cds-indico\indico
set SCRIPTDIR=%~dp0
set PYTHONPATH=%INDICOPATH%;%PYTHONPATH%

python "%SCRIPTDIR%indicoShell.py" %1