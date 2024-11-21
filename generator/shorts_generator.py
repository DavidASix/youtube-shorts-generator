import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import os
import subprocess
load_dotenv()
from pprint import pprint
from pathlib import Path
import pickle
from openai import OpenAI
# Audio Generation
from pydub import AudioSegment
from pydub.effects import speedup
# Video Generation
import moviepy.editor as mp
from moviepy.editor import TextClip, CompositeVideoClip, ImageClip
import cv2
import numpy as np

class ShortsGenerator:
    def __init__(self, media_wiki_id, media_wiki_title, url, fandom):
        self.media_wiki_id = media_wiki_id
        self.media_wiki_title = media_wiki_title
        self.url = url
        self.fandom = fandom

        self.google_images = None
        self.voice_over_file = "generator/assets/voiceover.mp3"
        self.timestamps = None

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
        except Exception as e:
            print(e)

        self.google_images = []
        for i, link in enumerate(links):
            image_name = self.extract_url_file_name(link)
            image_path = f'generator/assets/images/{i+1}_{image_name}'
            response = requests.get(link)
            img = Image.open(BytesIO(response.content))
            img = img.convert('RGB')
            img.save(image_path)
            self.google_images.append(image_path)
    
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
        vo_file = "generator/assets/voiceover.mp3"

        # If required, shorten audio while maintaining pitch
        audio = AudioSegment.from_mp3(vo_file)
        # Check if the audio is longer than 55 seconds
        if audio.duration_seconds > 55:
            # Calculate the speedup factor
            speedup_factor = audio.duration_seconds / 55
            print(f'speed factor {speedup_factor}')
            # Speed up the audio
            audio = speedup(audio, playback_speed=speedup_factor)

        # Save the audio
        audio.export(vo_file, format="mp3")
        self.voice_over_file = vo_file

    def get_timestamps(self):
        print('Getting audio timestamps')
        if not os.path.exists(self.voice_over_file):
            print(f"{self.voice_over_file} does not exist. Returning early.")
            return  # early return if the file doesn't exist
        """
        client = OpenAI()

        with open(self.voice_over_file, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
        with open("generator/assets/timestamps.pkl", "wb") as f:
            pickle.dump(transcript.words, f)
        
        self.timestamps = transcript.words
        """
        with open("generator/assets/timestamps.pkl", "rb") as f:
            self.timestamps = pickle.load(f)

    def create_video(self):
        audio = mp.AudioFileClip(self.voice_over_file)
        subtitles = []

        image_clips = []
        image_duration = audio.duration / len(self.google_images)

        for i, image_path in enumerate(self.google_images):
            image_clip = ImageClip(image_path).set_duration(image_duration)
            image_clip = image_clip.set_start(i * image_duration)
            
            # Center the image
            width, height = image_clip.size
            new_width = 720 - 40  # assuming the screen width is 720
            ratio = new_width / width
            new_height = int(height * ratio)
            image_clip = image_clip.set_pos(((720 - new_width) / 2, (1280 - new_height) / 2))
            image_clip = image_clip.resize((new_width, new_height))
                      
            image_clips.append(image_clip)

        # Create a composite video clip with the images
        image_clips = CompositeVideoClip(image_clips, size=(720, 1280))

        for timestamp in self.timestamps:
            text = TextClip(timestamp['word'], fontsize=110, color='white', font='BaronNeue', stroke_color='black', stroke_width=3)
            text = text.set_pos(('center', 'bottom')).set_duration(timestamp['end'] - timestamp['start'])
            text = text.set_start(timestamp['start'])
            if text.w > 715:
                text = text.resize(width=720)
            subtitles.append(text)
        # Create a composite video clip with the subtitles
        subtitle_clips = CompositeVideoClip(subtitles, size=(720, 1280))

        # Create a video clip with the audio
        video = mp.ColorClip(size=(720, 1280), color=(255, 165, 0), duration=audio.duration)
        video = video.set_audio(audio)

        # Add the subtitles and images to the video clip
        video = mp.CompositeVideoClip([video, subtitle_clips, image_clips])

        video.write_videofile("output.mp4", fps=24)