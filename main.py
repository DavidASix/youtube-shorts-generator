import page_classification.manually_classify_pages as manually_classify_pages
from page_classification.model_classify_pages import PageClassifier
#import train_algorithm
from common.media_wiki import MediaWiki
from generator.shorts_generator import ShortsGenerator

def main():
    fandom = 'fallout'
    page_classifier = PageClassifier(fandom)
    wiki = MediaWiki(fandom)
    """
    while True:
        id = wiki.random_pages()[0]['id']
        result = page_classifier.classify_page(id)
        print(f"Classification for id {id}: {result['rating_class']}")
        print(f"Title: {result['title']}")

        if result['rating_class'] in ['good', 'viral']:
            break
    """
    result = {
        'page_id': 480994, 
        'title': 'Darla (Fallout 4)', 
        'url': 'https://fallout.fandom.com/wiki/Darla_(Fallout_4)', 
        'categories': 'Fallout 4 human characters||Triggermen characters||Vault 114 characters', 'sections': 'background||interactions with the player character||inventory||appearances||references', 
        'non_english': False, 
        'file_page': 0, 
        'short_page': 0, 
        'total_length': 3609, 
        'target_words_in_section_titles': 1, 
        'section_count': 5, 
        'image_count': 10, 'audio_count': 1, 'category_count': 3, 
        'rating_class': 'viral'}

    print(f"Final classification for id {result['title']}: {result['rating_class']}")
    print(result)
    shorts_generator = ShortsGenerator(result['page_id'], result['title'], fandom)
    shorts_generator.get_google_images()


    

if __name__ == "__main__":
    main()