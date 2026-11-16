import pandas as pd

if 'transformer' not in globals():
    try:
        from mage_ai.data_preparation.decorators import transformer
    except ImportError:
        def transformer(func):
            return func

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


@transformer
def validate_data(df, *args, **kwargs):
    """
    Custom Quality Transformer (Part C4):
    Verifies that the raw Iris dataset contains zero missing values
    and exactly 3 distinct botanical target classes.
    """
    null_count = int(df.isnull().sum().sum())
    n_classes = int(df['target'].nunique())
    print(f'Data Quality Check: {null_count} missing values found across {len(df)} rows.')
    print(f'Target Distribution: {n_classes} classes identified.')
    return df


@test
def test_data_integrity(output, *args):
    """
    Quality gate: asserts zero missing values and exactly 3 Iris species.
    """
    assert output.isnull().sum().sum() == 0, 'Dataset contains unexpected missing values'
    assert output['target'].nunique() == 3, 'Dataset must contain exactly 3 species classes'
