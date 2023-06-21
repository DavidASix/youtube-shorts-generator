import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, ConfusionMatrixDisplay
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from scipy.stats import randint

from common.sql import sql


def get_sample_df():
    db_engine = sql()
    query = 'SELECT * FROM manual_page_classifications LIMIT 5000'
    df = pd.read_sql_query(query, db_engine.connection)
    print(df)
    feature_columns = [
        'total_length',
        'non_english',
        'file_page',
        'short_page',
        'first_section_length',
        'target_words_in_section_titles',
        'section_count',
        'image_count',
        'audio_count'
    ]
    # Split up features (x) and target (y)
    x = df[feature_columns]
    y = df['rating_class']

    # Split up training and test sets
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25)

    # Train the model
    print('Training Model')
    rf = RandomForestClassifier()
    rf.fit(x_train, y_train)

    # Predict test values
    print('Predict test set values')
    y_pred = rf.predict(x_test)

    # Check accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy:", accuracy)


def main():
    get_sample_df()