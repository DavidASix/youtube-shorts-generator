# YouTube Shorts Generator
The great YouTube Shorts content by creators has slowly been diluted by more and more AI generated content. As companies like OpenAI make AI more approachable, we start to see more and more low effort content in the market.
As much as it would be nice to see this content extinguish, I don't think we can put that genie back in the bottle.

The old adage goes, if you can't beat 'em, join 'em.

Instead of taking a step backwards in the technological evolution of content, let's take a step forwards. I'm building this project to hopefully create higher effort & interesting AI generated content.

## The Idea
Create a program that can focus in on a niche and create specialized videos about that niches content.

## Project Sections
The project will be broken up into these loose sections:

### Getting an idea
* Scrape Fandom wiki's for ideas
* Train a model to select an interesting article from any fandom

### Create the script
* Summarize the article with GPT-4
* Store the summary and article information

### Source the assets and audio
* Create an 11 Labs Voice Clone
* Get an MP3 of the script
* Source video and image assets for the video

### Putting it all together
* Download assets
* Setting timestamps
* Create a video with FFMPEG

### Showing the world
* Utilize YouTube API to post the video
* Set up a CRON job to run the account on a server
