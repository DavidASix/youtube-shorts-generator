import page_classification.manually_classify_pages as manually_classify_pages
from page_classification.model_classify_pages import PageClassifier
#import train_algorithm
from common.media_wiki import MediaWiki

def main():
    fandom = 'fallout'
    page_classifier = PageClassifier(fandom)
    wiki = MediaWiki(fandom)

    while True:
        id = wiki.random_pages()[0]['id']
        result = page_classifier.classify_page(id)
        print(f"Classification for id {id}: {result['rating_class']}")
        print(f"Title: {result['title']}")

        if result['rating_class'] in ['good', 'viral']:
            break

    print(f"Final classification for id {result['title']}: {result['rating_class']}")
    print(result)

    

if __name__ == "__main__":
    main()