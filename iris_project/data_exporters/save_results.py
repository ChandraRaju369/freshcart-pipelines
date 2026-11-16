# Import Mage's decorator only if it isn't already loaded
if 'data_exporter' not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_exporter
    except ImportError:
        def data_exporter(func):
            return func


@data_exporter
def export_data(df, *args, **kwargs):
    """
    Data Exporter: Saves test predictions to iris_predictions.csv.
    """
    df.to_csv('iris_predictions.csv', index=False)
    print('Saved', len(df), 'predictions to iris_predictions.csv')
