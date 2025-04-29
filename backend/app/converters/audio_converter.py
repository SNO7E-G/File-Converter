from app.converters.base_converter import BaseConverter
import os
import traceback
import subprocess
import tempfile
import shutil

class AudioConverter(BaseConverter):
    """Converter for audio formats"""
    
    SUPPORTED_FORMATS = {
        'mp3': ['wav', 'ogg', 'flac', 'aac', 'm4a'],
        'wav': ['mp3', 'ogg', 'flac', 'aac', 'm4a'],
        'ogg': ['mp3', 'wav', 'flac', 'aac', 'm4a'],
        'flac': ['mp3', 'wav', 'ogg', 'aac', 'm4a'],
        'aac': ['mp3', 'wav', 'ogg', 'flac', 'm4a'],
        'm4a': ['mp3', 'wav', 'ogg', 'flac', 'aac'],
    }
    
    @classmethod
    def supports_target_format(cls, target_format):
        """Check if this converter supports converting to the target format"""
        source_formats = cls.SUPPORTED_FORMATS.keys()
        for source_format in source_formats:
            if target_format in cls.SUPPORTED_FORMATS[source_format]:
                return True
        return False
    
    def _check_ffmpeg_installed(self):
        """Check if FFmpeg is installed"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def convert(self, source_path, target_path, options=None):
        """
        Convert audio from source format to target format using FFmpeg
        
        Args:
            source_path (str): Path to the source file
            target_path (str): Path where the converted file should be saved
            options (dict, optional): Additional options for the conversion
                - bitrate (str): Target bitrate (e.g. '192k')
                - sample_rate (int): Sample rate in Hz
                - channels (int): Number of audio channels
                - volume (float): Volume adjustment (1.0 = original volume)
                - trim_start (float): Start time in seconds
                - trim_end (float): End time in seconds
                
        Returns:
            bool: True if the conversion was successful, False otherwise
        """
        if not options:
            options = {}
            
        # Check if FFmpeg is installed
        if not self._check_ffmpeg_installed():
            raise Exception("FFmpeg is not installed. Please install FFmpeg to convert audio files.")
            
        try:
            # Prepare FFmpeg command
            ffmpeg_cmd = ['ffmpeg', '-i', source_path]
            
            # Add audio filters if needed
            audio_filters = []
            
            # Volume adjustment
            if 'volume' in options:
                volume = float(options['volume'])
                audio_filters.append(f"volume={volume}")
            
            # Apply all audio filters if any
            if audio_filters:
                filter_string = ','.join(audio_filters)
                ffmpeg_cmd.extend(['-af', filter_string])
            
            # Add output options
            
            # Bitrate
            if 'bitrate' in options:
                ffmpeg_cmd.extend(['-b:a', options['bitrate']])
            
            # Sample rate
            if 'sample_rate' in options:
                ffmpeg_cmd.extend(['-ar', str(options['sample_rate'])])
            
            # Channels
            if 'channels' in options:
                ffmpeg_cmd.extend(['-ac', str(options['channels'])])
            
            # Trim audio (using ss and to)
            if 'trim_start' in options:
                ffmpeg_cmd.extend(['-ss', str(options['trim_start'])])
            
            if 'trim_end' in options:
                ffmpeg_cmd.extend(['-to', str(options['trim_end'])])
            
            # Output file
            ffmpeg_cmd.extend(['-y', target_path])
            
            # Run FFmpeg command
            process = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            # Check if output file exists
            if not os.path.exists(target_path):
                raise Exception(f"Failed to create output file: {target_path}")
                
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg error: {e.stderr.decode('utf-8', errors='replace')}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"Error converting audio: {str(e)}"
            traceback.print_exc()
            raise Exception(error_msg) 