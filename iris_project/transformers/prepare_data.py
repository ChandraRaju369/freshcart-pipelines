import pandas as pd
from sklearn.model_selection import train_test_split

# Import Mage decorators if present; fallback to identity decorators if outside Mage
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
def transform(df, *args, **kwargs):
    """
    Transforms the 150-row Iris dataset by splitting it 80/20 into train/test sets,
    attaching a 'split' indicator column to each partition.
    """
    train_df, test_df = train_test_split(df, test_size=0.3, random_state=42)

    train_df = train_df.copy()
    test_df = test_df.copy()
    train_df['split'] = 'train'
    test_df['split'] = 'test'

    result = pd.concat([train_df, test_df])
    print(f'Train rows: {len(train_df)} | Test rows: {len(test_df)}')
    return result


@test
def test_output(output, *args):
    """
    Mage quality gate test: ensures the 'split' column was generated.
    """
    assert 'split' in output.columns, 'split column missing'
