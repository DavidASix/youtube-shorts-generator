import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import os
load_dotenv()
from pprint import pprint
from pathlib import Path
from openai import OpenAI
from pydub import AudioSegment
from pydub.effects import speedup

class ShortsGenerator:
    def __init__(self, media_wiki_id, media_wiki_title, url, fandom):
        self.media_wiki_id = media_wiki_id
        self.media_wiki_title = media_wiki_title
        self.url = url
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
    
    def get_script(self):
        api_key = os.getenv('OPENAI_API_KEY')
        client = OpenAI(api_key=api_key)
        with open('./generator/assistant-instructions.txt', 'r') as f:
            assistant_instructions = f.read()
        # Call to Open AI for script
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=1280,
            temperature=1.4,
            messages=[
                {"role": "system", "content": assistant_instructions},
                {"role": "user", "content": self.url}
            ]
        )
        response = completion.choices[0].message.content
        response = response.replace("-", ",")

        return response

    def create_voice_over(self, script):
        print('Attempting to generate voiceover')
        # Get Audio
        api_key = os.getenv('OPENAI_API_KEY')
        client = OpenAI(api_key=api_key)

        speech_file_path = f'generator/assets/voiceover.mp3'
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="echo",
            input=script
        )

        response.stream_to_file(speech_file_path)

        # If required, shorten audio while maintaining pitch
        audio = AudioSegment.from_mp3("generator/assets/voiceover.mp3")
        # Check if the audio is longer than 55 seconds
        if audio.duration_seconds > 55:
            # Calculate the speedup factor
            speedup_factor = audio.duration_seconds / 55
            print(f'speed factor {speedup_factor}')
            # Speed up the audio
            audio = speedup(audio, playback_speed=speedup_factor)

        # Save the audio
        audio.export("generator/assets/voiceover.mp3", format="mp3")
