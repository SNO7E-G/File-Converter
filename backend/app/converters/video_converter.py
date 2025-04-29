from app.converters.base_converter import BaseConverter
import os
import traceback
import subprocess
import json
import tempfile

class VideoConverter(BaseConverter):
    """Converter for video formats"""
    
    SUPPORTED_FORMATS = {
        'mp4': ['avi', 'mov', 'mkv', 'webm', 'gif', 'wmv'],
        'avi': ['mp4', 'mov', 'mkv', 'webm', 'gif', 'wmv'],
        'mov': ['mp4', 'avi', 'mkv', 'webm', 'gif', 'wmv'],
        'mkv': ['mp4', 'avi', 'mov', 'webm', 'gif', 'wmv'],
        'webm': ['mp4', 'avi', 'mov', 'mkv', 'gif', 'wmv'],
        'wmv': ['mp4', 'avi', 'mov', 'mkv', 'webm', 'gif'],
    }
    
    # Codec preferences for different formats
    FORMAT_CODECS = {
        'mp4': {'video': 'libx264', 'audio': 'aac'},
        'avi': {'video': 'mpeg4', 'audio': 'mp3'},
        'mov': {'video': 'libx264', 'audio': 'aac'},
        'mkv': {'video': 'libx264', 'audio': 'aac'},
        'webm': {'video': 'libvpx-vp9', 'audio': 'libopus'},
        'wmv': {'video': 'wmv2', 'audio': 'wmav2'},
        'gif': {'video': 'gif', 'audio': None},
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

    def _get_video_info(self, file_path):
        """Get video information using FFprobe"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return json.loads(result.stdout)
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            print(f"Error getting video info: {str(e)}")
            return {}
    
    def convert(self, source_path, target_path, options=None):
        """
        Convert video from source format to target format using FFmpeg
        
        Args:
            source_path (str): Path to the source file
            target_path (str): Path where the converted file should be saved
            options (dict, optional): Additional options for the conversion
                - resolution (str): Target resolution (e.g. '1920x1080')
                - bitrate (str): Target video bitrate (e.g. '2M')
                - audio_bitrate (str): Target audio bitrate (e.g. '192k')
                - fps (int): Target frames per second
                - trim_start (float): Start time in seconds
                - trim_end (float): End time in seconds
                - codec (str): Specific video codec
                - preset (str): Encoding preset (e.g. 'fast', 'medium', 'slow')
                - crf (int): Constant Rate Factor (quality, lower is better)
                - format (str): Force specific format
                
        Returns:
            bool: True if the conversion was successful, False otherwise
        """
        if not options:
            options = {}
            
        # Check if FFmpeg is installed
        if not self._check_ffmpeg_installed():
            raise Exception("FFmpeg is not installed. Please install FFmpeg to convert video files.")
            
        try:
            # Get video info
            video_info = self._get_video_info(source_path)
            
            # Prepare FFmpeg command
            ffmpeg_cmd = ['ffmpeg', '-i', source_path]
            
            # Add video codec
            codec_info = self.FORMAT_CODECS.get(self.target_format, {'video': 'libx264', 'audio': 'aac'})
            
            # Override codec if specified in options
            video_codec = options.get('codec', codec_info['video'])
            ffmpeg_cmd.extend(['-c:v', video_codec])
            
            # Add audio codec if applicable
            if codec_info['audio'] and self.target_format != 'gif':
                ffmpeg_cmd.extend(['-c:a', codec_info['audio']])
            elif self.target_format == 'gif':
                # For GIF, we need to remove audio
                ffmpeg_cmd.extend(['-an'])
            
            # Add preset if specified
            if 'preset' in options:
                ffmpeg_cmd.extend(['-preset', options['preset']])
            
            # Add CRF if specified
            if 'crf' in options:
                ffmpeg_cmd.extend(['-crf', str(options['crf'])])
                
            # Add resolution if specified
            if 'resolution' in options:
                ffmpeg_cmd.extend(['-s', options['resolution']])
            
            # Add video bitrate if specified
            if 'bitrate' in options:
                ffmpeg_cmd.extend(['-b:v', options['bitrate']])
            
            # Add audio bitrate if specified and not a GIF
            if 'audio_bitrate' in options and self.target_format != 'gif':
                ffmpeg_cmd.extend(['-b:a', options['audio_bitrate']])
            
            # Add FPS if specified
            if 'fps' in options:
                ffmpeg_cmd.extend(['-r', str(options['fps'])])
            
            # Trim video (using ss and to)
            if 'trim_start' in options:
                ffmpeg_cmd.extend(['-ss', str(options['trim_start'])])
            
            if 'trim_end' in options:
                ffmpeg_cmd.extend(['-to', str(options['trim_end'])])
            
            # Special case for GIF
            if self.target_format == 'gif':
                # Generate a palette for better quality
                palette_path = tempfile.mktemp(suffix='.png')
                
                # First pass to generate palette
                palette_cmd = ['ffmpeg', '-i', source_path]
                
                # Add filters for palette generation
                palette_filters = []
                if 'fps' in options:
                    palette_filters.append(f"fps={options['fps']}")
                if 'resolution' in options:
                    palette_filters.append(f"scale={options['resolution'].replace('x', ':')}")
                palette_filters.append("palettegen")
                
                palette_cmd.extend(['-vf', ','.join(palette_filters), '-y', palette_path])
                
                # Run palette generation
                subprocess.run(palette_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                
                # Use palette for conversion
                output_filters = []
                if 'fps' in options:
                    output_filters.append(f"fps={options['fps']}")
                if 'resolution' in options:
                    output_filters.append(f"scale={options['resolution'].replace('x', ':')}")
                output_filters.append(f"paletteuse=dither=sierra2_4a")
                
                ffmpeg_cmd.extend(['-i', palette_path, '-lavfi', ','.join(output_filters)])
                
                try:
                    # Add output file
                    ffmpeg_cmd.extend(['-y', target_path])
                    
                    # Run FFmpeg command
                    process = subprocess.run(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                finally:
                    # Clean up palette file
                    if os.path.exists(palette_path):
                        os.remove(palette_path)
            else:
                # Regular video conversion
                
                # Add output file
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
            error_msg = f"Error converting video: {str(e)}"
            traceback.print_exc()
            raise Exception(error_msg) 