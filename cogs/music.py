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
