import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import os
load_dotenv()
from pprint import pprint

class ShortsGenerator:
    def __init__(self, media_wiki_id, media_wiki_title, fandom):
        self.media_wiki_id = media_wiki_id
        self.media_wiki_title = media_wiki_title
        self.fandom = fandom

        self.google_images = None

    def extract_url_file_name(self, url):
        parts = url.split('/')[3:]
        filtered_parts = [part.split('?')[0].split('#')[0] for part in parts if '.' in part]
        filtered_parts = [part for part in filtered_parts if len(part.split('.')[-1]) == 3]
        return filtered_parts[0]
    
    def get_media_wiki_images(self):
        # Implement logic to get images from MediaWiki using self.media_wiki_id and self.media_wiki_title
        pass

    def get_google_images(self):
        print('getting google images')
        # Use Google API to get the top 10 google images for self.media_wiki_title and self.fandom
        api_key = os.getenv('GOOGLE_API_KEY')
        search_engine = os.getenv('SEARCH_ENGINE')
        search_string = f'{self.fandom} - {self.media_wiki_title} -ytimg.com -reddit.com'
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'q': search_string,
            'key': api_key,
            'cx': search_engine,
            'searchType': 'image',
            'imgSize': 'XXLARGE',
            #'imgType': 'stock',
            #'imgColorType': 'trans'
        }
        
        try:
            response = requests.get(url, params=params)
            if (response.status_code != 200):
                return ValueError('Could not connnect to Google Images')
            results = response.json()
            # Find the largest image
            links = [item['link'] for item in results['items']]
            links = [link for link in links if '.svg' not in link.lower()]
            pprint(links)
            self.google_images = links
        except Exception as e:
            print(e)

        for i, link in enumerate(links):
            image_name = self.extract_url_file_name(link)
            image_path = f'generator/assets/{i+1}_{image_name}'
            response = requests.get(link)
            img = Image.open(BytesIO(response.content))
            img = img.convert('RGB')
            img.save(image_path)