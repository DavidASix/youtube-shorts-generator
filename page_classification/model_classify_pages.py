import page_classification.manually_classify_pages as manually_classify_pages
import pickle
import sqlite3
import questionary
import pandas as pd
import os

def get_classified_pages():
    # Load the manually_classify_pages module
    pages = manually_classify_pages.get_viable_pages(1)

    # Get the dataframe from the pages
    df = manually_classify_pages.get_pages_df(pages)

    # Add a new column 'category_count' that contains the count of the substring '||' in the 'categories' column plus one
    df['category_count'] = df['categories'].apply(lambda x: x.count('||') + 1)

    # Specify the feature columns
    feature_columns = [
        'total_length',
        'file_page',
        'target_words_in_section_titles',
        'category_count',
        'image_count',
    ]
    dir_path = os.path.dirname(os.path.realpath(__file__))
    model_path = os.path.join(dir_path, 'random_forest_model.pkl')
    # Load the random forest model from the pickle file
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    # Run the dataframe through the model
    predictions = model.predict(df[feature_columns])

    # Print the predictions
    print(predictions)
    df['rating_class'] = predictions
    return df

# Function to add DF to model_page_classifications table
def add_df_to_table(df):
    # Connect to the database
    try:
        print(df)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        parent_dir_path = os.path.dirname(dir_path)
        dataset_path = os.path.join(parent_dir_path, 'ytsg-dataset.db')
        conn = sqlite3.connect(dataset_path)
        df.to_sql("model_page_classifications", conn, if_exists="append", index=False)
        conn.commit()
        conn.close()
    except Exception as e:
        print('Error inputting data', e)

# Function to rerun the script based on user input
def conditionally_rerun_script():
    answer = questionary.confirm("Do you want to rerun the script?").ask()
    if answer:
        # Call the main function again
        main()
    else:
        print("Script not rerun.")

def main():
    df = get_classified_pages()
    add_df_to_table(df)
    conditionally_rerun_script()

if __name__  == "__main__":
    main()
