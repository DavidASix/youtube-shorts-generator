import requests
import re
from bs4 import BeautifulSoup
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
      """
      This function returns an array of random pages
      Args:
        pages: number of random pages to find, default to one.
      """
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
    """
      This function returns the basic barebones information about a media_wiki page
      Args:
        id: a media wiki page id
    """
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
  
  def parse_page_classification_information(self, id):
    """
      This returns the information needed to classify it by the ML engine
      Args:
        id: Media wiki page id
    """
    ##############
    # This initial parse gets basic information, from a previous iteration of the project
    ##############
    output_page = {}
    page = self.get_page_information(id)
    # Pages should be long enough for a 30 second video, and should not be about game files
    short_page = page['length'] < 1000
    # Find pages with titles like 'abc.mp3' to avoid file related pages
    file_page = re.match(r".+\..{2,}", page['title']) != None
    # Get page content
    page_content = self.get_page_content(id)
    page_images = self.get_page_images(id)
    page_audio = self.get_page_audio_files(id)

    # Start adding to output file object
    output_page.update({
        'id': id,
        'lang': 'en',
        'title': page['title'], 
        'url': page['url'], 
        'sections': page['sections'],
        'categories': page['categories'],
        'short_page': short_page,
        'file_page': file_page,
        'plain_text': page_content['content'], 
        'infobox': page_content['infobox'], 
        'images': page_images,
        'audio': page_audio
    })
    
    ##############
    # This second pass aggregates the information for entry into a database
    # These two steps should be done one, but I wrote them seperately and don't want 
    # to combine them right now
    ##############

    #section_concat = ''.join(v for k, v in p['section_text'].items() if k.lower() != 'references')
    #overview_length = len(p['plain_text']) - len(section_concat)
    #first_section_title = p['sections'][0] if len(p['sections']) > 0 else ''
    #first_section_length = 0#len(p['section_text'].get(first_section_title, ''))
    # Search the section titles for words that indicate the section might be rich in content creation text.
    
    targetted_section_words = ['background', 'description', 'lore', 'biography', 'overview', 'personality', 'history', 'context', 'backstory', 'origins', 'explanation', 'summary', 'synopsis', 'introduction']
    target_words_in_section_titles = 0
    for w in targetted_section_words:
        if w in '|'.join(output_page['sections']).lower():
            target_words_in_section_titles += 1

    output_page = {
        'page_id': output_page['id'],
        'title': output_page['title'],
        'url': output_page['url'], 
        'categories': '||'.join(output_page['categories']),
        'sections': '||'.join(output_page['sections']).lower(),
        'non_english': output_page['lang'] != 'en' * 1,
        'file_page': output_page['file_page'] * 1,
        'short_page': output_page['short_page'] * 1,
        'total_length': len(output_page['plain_text']) if output_page['plain_text'] else 0,  
        'target_words_in_section_titles': target_words_in_section_titles, 
        'section_count': len(output_page['sections']) if output_page['sections'] else 0, 
        'image_count': len(output_page['images']) if output_page['images'] else 0,
        'audio_count': len(output_page['audio']) if output_page['audio'] else 0
    }

    return output_page

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

        return {'infobox': infoBox, 'content': content}
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
        print(e)
        
  def get_page_audio_files(self, id):
    try:
      page = self.get_page_information(id)
      res = requests.get(page['url'])
      soup = BeautifulSoup(res.text, 'html.parser')
      # Audio file urls
      audio = soup.find_all('audio')
      return [a['src'] for a in audio]
    except Exception as e:
      print('error', e)
