import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Import Mage's decorator only if it isn't already loaded
if 'transformer' not in globals():
    try:
        from mage_ai.data_preparation.decorators import transformer
    except ImportError:
        def transformer(func):
            return func


@transformer
def evaluate(df, *args, **kwargs):
    """
    Evaluates classification performance across multiple metrics
    and generates a confusion matrix.
    """
    y_true = df['target']
    y_pred = df['predicted']

    print('Confusion matrix:')
    print(pd.crosstab(y_true, y_pred, rownames=['actual'], colnames=['predicted']))

    metrics = pd.DataFrame({
        'metric': ['accuracy', 'precision', 'recall', 'f1_score'],
        'value': [
            round(accuracy_score(y_true, y_pred), 3),
            round(precision_score(y_true, y_pred, average='macro'), 3),
            round(recall_score(y_true, y_pred, average='macro'), 3),
            round(f1_score(y_true, y_pred, average='macro'), 3),
        ]
    })
    print('\nMetrics Summary:')
    print(metrics)
    return metrics
