while [ -t 1 ]; do
    PYTHONPATH=indico python -W ignore::DeprecationWarning tests/MaKaC_tests/tasks/inject.py
done
