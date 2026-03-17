import os
import asyncio
import logging
import yt_dlp
from config import YDL_OPTIONS, DOWNLOAD_PATH, MAX_FILE_SIZE_BYTES

logger = logging.getLogger(__name__)

class DownloadError(Exception):
    pass

class DownloadService:
    def __init__(self):
        self.ydl_opts = YDL_OPTIONS.copy()
        if not os.path.exists(DOWNLOAD_PATH):
            os.makedirs(DOWNLOAD_PATH)

    async def download(self, url: str, unique_id: str) -> dict:
        """
        Download media from url.
        Returns dict with 'path', 'title', 'ext', 'filesize'.
        Raises DownloadError on failure.
        """
        opts = self.ydl_opts.copy()
        opts['outtmpl'] = os.path.join(DOWNLOAD_PATH, f'{unique_id}.%(ext)s')
        
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Extract info and download
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
                if info is None:
                    raise DownloadError("No info extracted")
                
                filename = ydl.prepare_filename(info)
                # Handle possible different extensions
                if not os.path.exists(filename):
                    # Try to find the actual file
                    for f in os.listdir(DOWNLOAD_PATH):
                        if f.startswith(unique_id):
                            filename = os.path.join(DOWNLOAD_PATH, f)
                            break
                    else:
                        raise DownloadError("File not found after download")
                
                filesize = os.path.getsize(filename)
                if filesize > MAX_FILE_SIZE_BYTES:
                    os.remove(filename)
                    raise DownloadError(f"File too large: {filesize} bytes > {MAX_FILE_SIZE_BYTES}")
                
                return {
                    'path': filename,
                    'title': info.get('title', 'Unknown'),
                    'ext': os.path.splitext(filename)[1][1:],
                    'filesize': filesize
                }
        except yt_dlp.utils.DownloadError as e:
            raise DownloadError(f"yt-dlp error: {str(e)}")
        except Exception as e:
            raise DownloadError(f"Unexpected error: {str(e)}")

    def cleanup(self, filepath: str):
        """Remove downloaded file."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.error(f"Failed to delete {filepath}: {e}")