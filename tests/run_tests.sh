# TODO make tutorial_dev_spectral_libraries.ipynb work
INCLUDED_NBS=$(find ../docs/nbs -name "*.ipynb" | grep -v tutorial_dev_spectral_libraries.ipynb)
python -m pytest --nbmake $(echo $INCLUDED_NBS)

# TODO make test_isotope_mp.ipynb work
# Note: multiprocessing in ipynb sometimes suspended on some versions of Windows, ignore the
# corresponding notebook(s) if this occurs again
# INCLUDED_NBS=$(find ../nbs_tests -name "*.ipynb" | grep -v test_isotope_mp.ipynb)

INCLUDED_NBS=$(find ../nbs_tests -name "*.ipynb")
python -m pytest --nbmake $(echo $INCLUDED_NBS)

python -m pytest test_smiles.py
