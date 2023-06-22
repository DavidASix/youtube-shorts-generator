import requests
import re
# https://en.wikipedia.org/w/api.php
import common.utils as u

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

    def get_page_information(self, id):
      params = {**self.params, "pageids": id, "prop": "info", "inprop": "displaytitle|url"}
      page = {}
      # Get basic information about the page
      try:
          res = requests.get(self.url, params=params)
          res = res.json()
          res = res['query']['pages'][str(id)]
          page.update({
            'id': res['pageid'],
            'title': res['displaytitle'],
            'url': res['fullurl'],
            'length': res['length']
          })
      except Exception as e:
          print('Error', e)
      # Get the categories for this article
      params = {**self.params, "action": "query", "pageids": id, "prop": "categories"}
      try:
        res = requests.get(self.url, params=params)
        res = res.json()
        res = res['query']['pages'][str(id)]['categories']
        res = [cat['title'][9:] for cat in res]
        page.update({'categories': res})
      except Exception as e:
        print('Error', e)
      
      # Get the sections for this article
      # Drop any subsections, only look for top level sections
      params = {**self.params, "action": "parse", "pageid": id, "prop": "sections"}
      try:
        res = requests.get(self.url, params=params)
        res = res.json()
        res = res['parse']['sections']
        res = [sec['line'] for sec in res if sec['toclevel'] == 1]
        page.update({'sections': res})
      except Exception as e:
        print('Error', e)
      return page
    
    def get_infobox(self, id):
      params = {**self.params, "pageids": id, "prop": "revisions", "rvprop": "content"}
      # Get the target pages most recent revision & content
      try:
          # Get list of available images
          res = requests.get(self.url, params=params)
          res = res.json()
          content = res['query']['pages'][str(id)]['revisions'][0]["*"]
      except Exception as e:
          print('Error', e)
          return None
      # Get the contents of the infoBox if one exists
      if "{{Infobox" in content:
        # Parse the content for infobox details:
        infoBoxStartInd = "{{Infobox"
        infoBoxString = content[content.find(infoBoxStartInd):]
        infoBoxString = u.get_curly_content(infoBoxString)
        infoBoxString = u.get_curly_content(infoBoxString)
        # Parse infobox data into dictionary
        result = {}
        # Find all | chars that are not contained within curly brackets
        pattern = r'\|(?![^{}]*})'
        # Replace delimiter bars with new delimiter
        delimiter = '|||'
        infoBoxString = re.sub(pattern, delimiter, infoBoxString)  
        pairs = infoBoxString.split(delimiter)
        # Loop through the KV pairs and add to the dictionary
        for pair in pairs:
            # Split each pair by '='
            p = pair.split('=', 1)
            if len(p) < 2:
              # Key does not have a value pair, or parsing failed on this pair
              # Should raise a warning?
              continue
            key, value = p
            # remove trailing white spaces
            key = key.strip()
            value = value.strip().strip('\n')
            result[key] = value
        return result
      else:
        return None

    def get_page_content(self, id):
      params = {**self.params, "pageids": id, "prop": "revisions", "rvprop": "content"}
      # Get the target pages most recent revision & content
      try:
          # Get list of available images
          res = requests.get(self.url, params=params)
          res = res.json()
          content = res['query']['pages'][str(id)]['revisions'][0]["*"]
          # check if there is an info box. If so, grab it's information and delete it from the content
          infoBox = None
          if "{{Infobox" in content:
            infoBox = self.get_infobox(id)
            # Parse the content for infobox details:
            infoBoxStartInd = "{{Infobox"
            infoBoxString = content[content.find(infoBoxStartInd):]
            infoBoxString = u.get_curly_content(infoBoxString)
            infoBoxString = u.get_curly_content(infoBoxString)
            content = content.replace('{{'+infoBoxString+'}}', '')

          return {'infoBox': infoBox, 'content': content}
      except Exception as e:
          print('Error', e)

    # Get information about a page via its id
    def get_page_images(self, id):
        params = {**self.params, "prop": "images", "pageids": id}
        try:
            # Get list of available images
            res = requests.get(self.url, params=params)
            res = res.json()
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
