# In the search_song function, replace the YTDL_OPTS usage:
async def search_song(self, query):
    """Search for a song on YouTube"""
    try:
        # Updated YouTube DL options to handle cookie issues
        ytdl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
        }
        
        loop = asyncio.get_event_loop()
        ytdl = yt_dlp.YoutubeDL(ytdl_opts)
        data = await loop.run_in_executor(
            None, 
            lambda: ytdl.extract_info(f"ytsearch:{query}", download=False)
        )
        
        if data and 'entries' in data and len(data['entries']) > 0:
            return data['entries'][0]
        return None
    except Exception as e:
        print(f"Error searching song: {e}")
        return None

+32
        return self.queues[guild_id]
    
    async def search_song(self, query):
        """Search for a song on YouTube"""
        """Search for a song on YouTube using YouTube API"""
        try:
            # First try YouTube API search
            youtube_api_key = os.getenv('YOUTUBE_API_KEY')
            if youtube_api_key:
                async with aiohttp.ClientSession() as session:
                    search_url = f"https://www.googleapis.com/youtube/v3/search"
                    params = {
                        'part': 'snippet',
                        'q': query,
                        'type': 'video',
                        'maxResults': 1,
                        'key': youtube_api_key
                    }
                    
                    async with session.get(search_url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if 'items' in data and len(data['items']) > 0:
                                video = data['items'][0]
                                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                                
                                # Get video details using yt-dlp
                                loop = asyncio.get_event_loop()
                                info = await loop.run_in_executor(
                                    None,
                                    lambda: self.ytdl.extract_info(video_url, download=False)
                                )
                                
                                if info:
                                    return info
            
            # Fallback to direct yt-dlp search if API fails
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
