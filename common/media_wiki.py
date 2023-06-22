import requests
# https://en.wikipedia.org/w/api.php


class MediaWiki(object):
    def __init__(self, wiki, lang='en'):
        if wiki is None:
            raise Exception('Wiki must be defined')
        self.wiki = wiki
        self.lang = lang
        self.url = f"https://{self.wiki}.fandom.com/{self.lang}/api.php"
        self.params = {"format": "json", "action": "query"}

    # Return an array of random pages
    def random_pages(self, pages=1):
        # Params are appended as url encoded query
        # rnnamespace refers to the content being queried. 0 is pages, 1 is talks, 2 is users, 6 is files, etc. Find more at the api docs
        # https://en.wikipedia.org/w/api.php?action=help&modules=query%2Brandom
        params = {"format": "json", "action": "query",
                  "list": "random", "rnlimit": pages, "rnnamespace": 0}
        try:
            res = requests.get(self.url, params=params)
            res = res.json()
            return res['query']['random']
        except Exception as e:
            print(e)

    # Get information about a page via its id
    def get_page_images(self, id):
        params = {**self.params, "prop": "images", "pageids": id}
        try:
            print(params)
            # Get list of available images
            res = requests.get(self.url, params=params)
            res = res.json()
            print(res)
            # Join titles of list as new request params
            images = res['query']['pages'][str(id)]['images']
            images = '|'.join([img['title'] for img in images])
            # Get info about each image | https://en.wikipedia.org/w/api.php?action=help&modules=query%2Bimageinfo
            image_details = requests.get(self.url, params={**self.params, "titles": images, "prop": "imageinfo", "iiprop": "url|size|dimensions"})
            image_details = image_details.json()
            image_details = [
              {
                'title': image_details['query']['pages'][str(img_id)]['title'],
                'id': img_id,
                **image_details['query']['pages'][str(img_id)]['imageinfo'][0]
              }
              for img_id in image_details['query']['pages']]

            return image_details
        except Exception as e:
            print('Error', e)


wiki = MediaWiki('fallout')

random_page = wiki.random_pages()[0]
#print(random_page)

id = random_page['id']
id = 530985
page_images = wiki.get_page_images(id)
print('pageinfo:', page_images)