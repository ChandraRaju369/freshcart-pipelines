import pandas as pd
from sklearn.datasets import load_iris

# Import Mage's decorators only if they aren't already loaded
if 'data_loader' not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_loader
    except ImportError:
        def data_loader(func):
            return func

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


@data_loader
def load_data(*args, **kwargs):
    """
    Data Loader: Loads the built-in Iris dataset from scikit-learn as a pandas DataFrame.
    """
    iris = load_iris(as_frame=True)
    df = iris.frame                      # 4 feature columns + 'target'
    print('Rows loaded:', len(df))
    return df


@test
def test_output(output, *args):
    """
    Quality test: verifies exactly 150 records exist in Iris dataset.
    """
    assert len(output) == 150, 'Iris must have 150 rows'
