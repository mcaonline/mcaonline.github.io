import os
import utils

# Check required modules
utils.check_required_modules(os.path.abspath(__file__))

# Now import the rest of the modules
from openai import OpenAI
from moviepy.editor import VideoFileClip    # Actually only needed in utils.py need to figure out how to make module check working with two files.
from pydub import AudioSegment              # Actually only needed in utils.py
from pydub.silence import detect_silence    # Actually only needed in utils.py
from dotenv import load_dotenv

load_dotenv()  # Load all api key(s) from the .env file and set it as environment variable

# FFMPEG Needed! Use it from this git repo in this folder for winwdows or check https://phoenixnap.com/kb/ffmpeg-windows Download ffmpeg-git-full.7z:@ https://www.gyan.dev/ffmpeg/builds/
# Add FFMPEG Variable to the Windows Path (Envrionment) Variable check with CLI $env:Path e.g. with this in the PS: Add: D:\ffmpeg\bin e.g: $env:Path += ";D:\Github\cstauto\Video-to-Text___VideoTranscriptTranslater\ffmpeg\bin"

# Defintions
inputfilename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')   #no extension since it will look for .mp3 and .mp4
outputfolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
audio_block_size_in_ms = 300000                                                          # Target length for the audio chunks ms
audio_pause_min_silence_len_ms = 1000                                                    # Minimum length of silence to create an audio block ms
audio_silence_thresh_db = -50                                                            # Silence threshold db
audio_tolerance_ms = 60000                                                               # audio_tolerance_ms for the target length ms so add or remove 50 seconds to find a pause to break
systemprompt="ISE, GUI, Customer Success Specialist"                                     # Prompt on Speech to Text only acts like a dictionary.
APIKeyname = "OPENAI_API_KEY"
mode='PRD'

#################################################################
#   Load from utils.py:                                         #
#   Check Modules, API_KEY, Files + Load File + Create Blocks   #
#                                                               #
#################################################################

# Check existence of API key and file
utils.check_api_key(APIKeyname, mode)

# Check and or create necessary files and folders
audiofilename = utils.check_prepare_audio_video_files(inputfilename)
utils.move_files_to_backup(outputfolder)

audiofile_size_in_bytes = utils.get_file_size(audiofilename)

# Define mayx filesize
max_file_size_mb = 2.9
max_file_size_bytes = max_file_size_mb * 1_048_576

if audiofile_size_in_bytes > max_file_size_bytes:
    # Split audio into chunks for larger files
    print('No Audio Chunk Files generated since inputfile (or extracted audio) is smaller than 24,5 Megabyte')
    print('Silence timestamps are needed to create processing blocks in the audio file, cut not in the middle of a word')
    print('Searching silences - processing - please wait...')
    chunks = utils.split_audio_near_silences(audiofilename, audio_block_size_in_ms, audio_tolerance_ms, audio_pause_min_silence_len_ms, audio_silence_thresh_db)
    file_names = utils.export_audio_chunks(chunks, outputfolder)
else:
    # Use the whole file for smaller files
    file_names = [(audiofilename, os.path.basename(audiofilename).split('.')[0])]

#################################################################
#                                                               #
#   Pprocessing blocks - sent to api                            #
#                                                               #
#################################################################

def transcribe_audio_files(file_names, output_folder):
    client = OpenAI()
    all_transcriptions = []
    
    for file_path, base_name in file_names:
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="text",
                prompt=systemprompt
            )
            output_text_path = os.path.join(output_folder, f"{base_name}_transcriptchunk.txt")
            with open(output_text_path, "w", encoding="utf-8") as text_file:
                text_file.write(transcription)
            all_transcriptions.append(transcription)
            print(f"Transcription saved to {output_text_path}")
    
    combined_transcript = "\n".join(all_transcriptions)
    combined_transcript_path = os.path.join(output_folder, f"{base_name}_zout_complete_transcript.txt")
    with open(combined_transcript_path, "w", encoding="utf-8") as combined_file:
        combined_file.write(combined_transcript)
    print(f"Combined transcription saved to {combined_transcript_path}")

transcribe_audio_files(file_names, outputfolder)


