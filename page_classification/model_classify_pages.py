import pickle
import sqlite3
import os

from common.media_wiki import MediaWiki
fandom_title = 'fallout'

class PageClassifier:
    def __init__(self, fandom_title='fallout'):
        self.fandom_title = fandom_title
        self.model = None
        self.feature_columns = [
            'total_length',
            'file_page',
            'target_words_in_section_titles',
            'category_count',
            'image_count',
        ]
        self.load_model()

    def load_model(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        model_path = os.path.join(dir_path, 'random_forest_model.pkl')
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    def classify_page(self, id):
        wiki = MediaWiki(self.fandom_title, 'en')
        output_page = wiki.parse_page_classification_information(id)

        output_page['category_count'] = output_page['categories'].count('||') + 1

        predictions = self.model.predict([[output_page[col] for col in self.feature_columns]])
        print(predictions)
        output_page['rating_class'] = predictions[0]
        return output_page

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
