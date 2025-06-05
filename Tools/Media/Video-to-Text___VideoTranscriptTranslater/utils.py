import ast
import datetime
import os
import re
import shutil
import subprocess
import sys

#################################################################
#                                                               #
#   Check: 1. Modules, 2. API_KEY, 3. Files                     #
#                                                               #
#################################################################
#
# 1. Dynamic check of all modules used in this script. It module do not exists, create instructions to install or error.
# 
def get_imported_modules(script_path):
    with open(script_path, "r") as file:
        tree = ast.parse(file.read(), filename=script_path)
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_name = alias.name.split('.')[0]  # Extract base package name
                imported_modules.append((alias.name, base_name))
        elif isinstance(node, ast.ImportFrom):
            base_name = node.module.split('.')[0]  # Extract base package name
            imported_modules.append((node.module, base_name))
    return imported_modules

def check_module_installed(import_name):
    try:
        result = subprocess.run([sys.executable, "-c", f"import {import_name}"], capture_output=True, text=True)
        __import__(import_name)
        return True
    except ImportError:
        return False

def check_required_modules(script_path):
    modules_to_check = get_imported_modules(script_path)
    missing_modules = [pkg_name for import_name, pkg_name in modules_to_check if not check_module_installed(import_name)]
    
    if missing_modules:
        print("The following modules are not installed:")
        for module in missing_modules:
            print(f"- {module}")
        print("\nTo install the missing modules, run the following command(s):")
        for module in missing_modules:
            print(f"pip install {module}")
        sys.exit("Script has been terminated due to missing modules.")
    #print("All required modules are installed.\n")

#
### 2. Check if API KEY is existing, if not create file and put default Key in - inform user where to get key and how to add it here.
# 
def check_api_key(APIKeyname, mode):
    env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    api_key = os.environ.get(APIKeyname)
    
    if not api_key or api_key == "Put_your_API_key_here":        
        if not os.path.exists(env_file_path):
            with open(env_file_path, 'w') as env_file:
                env_file.write(f'{APIKeyname}="Put_your_API_key_here"\n')
            print(f"\nCannot find the {APIKeyname} in your environment variables.\n")    
            print(f"The '.env' file has been created at {env_file_path}. Please add your OpenAI API key to the '.env' file.\n")
            sys.exit()
        else:
            print(f"\nThe '.env' file exists at {env_file_path}.\n")
            print(f"Please ensure your OpenAI API key is set in the '.env' file correctly like: {APIKeyname}=\"Put_your_API_key_here\"\n")
            sys.exit()
    if mode == "DEBUG":
        print("The " + APIKeyname + " environment variable seems to be correctly set.\n")
#
### 3. Check if the inputfile and the outputfolder exists, if not create it
# 
def check_and_create_files(inputfilename, outputfolder):
    if not os.path.exists(inputfilename):
        print(f"\nSorry, the file '{inputfilename}' is missing and is required for text processing and translation. Please check the file name and try again.\n\n")
        sys.exit()  # Exit the script with a non-zero exit code to indicate an error

    if not os.path.exists(outputfolder):
        os.makedirs(outputfolder)
        print(f"\nCreated folder '{outputfolder}' since it was not existing.\n\n")
#
### 3. move all files in outputfolder into the output\backup folder
# 
def move_files_to_backup(source_dir):
    # Define the backup directory
    backup_dir = os.path.join(source_dir, 'backup')

    # Create the backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Move all files from source to backup directory
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        destination_file = os.path.join(backup_dir, filename)
        
        # Only move files, not directories
        if os.path.isfile(source_file):
            shutil.move(source_file, destination_file)
    print("\nAll earlier output files have been moved to the backup folder.\n")



#################################################################
#                                                               #
#   Load File for processing prepare blocks to sent to api      #
#                                                               #
#################################################################
#
### Read the file and create list of blocks based on blocksize
# 

# Add ffmpeg to PATH
ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg", "bin")
os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.silence import detect_silence

def is_unwanted_line(line):
    if re.match(r'^\d+ ".+" \(\d+\)$', line):
        return True
    if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$', line):
        return True
    return False

def read_sentences_from_file(inputfilename, mode):
    with open(inputfilename, 'r', encoding='utf-8') as file:
        text = file.read()
    
    # Remove unwanted lines
    lines = text.split('\n')
    cleaned_text = ' '.join([line for line in lines if not is_unwanted_line(line)])
    
    # Split the text into sentences
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!|।)\s', cleaned_text)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    if mode == "DEBUG":
        for sentence in sentences:
            print(sentence + '\n')

    return sentences

def create_bigblocks(sentences, blocksize, mode):
    bigblocks = []
    current_block = ''
    for sentence in sentences:
        if len(current_block) + len(sentence) <= blocksize:
            current_block += sentence + ' '
        else:
            if current_block:
                bigblocks.append(current_block.strip())
            current_block = sentence + ' '
    if current_block:
        bigblocks.append(current_block.strip())

    if mode == "DEBUG":
            for bigblock in bigblocks:
                print(bigblock + '\n')

    return bigblocks

def save_blocks_and_sentences(bigblocks, sentences, outputfolder, apivoicename):
    timestamped = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    blockssentencesfile = os.path.join(outputfolder, f"{timestamped}_000_{apivoicename}_all_blocks_and_all_sencences.txt")
    with open(blockssentencesfile, 'w', encoding='utf-8') as f:
        f.write("\nBig Blocks with Newline:\n\n")
        for block in bigblocks:
            f.write(block + "\n\n")
        f.write("\n\n\n\n\nSentences with Newline:\n\n")
        for sentence in sentences:
            f.write(sentence + "\n\n")
        f.write("\n\n\n\n\nBig Blocks:\n\n")
        for block in bigblocks:
            f.write(block + "\n")
        f.write("\n\n\n\n\nSentences:\n\n")
        for sentence in sentences:
            f.write(sentence + "\n")



#################################################################
#                                                               #
#   Load Audio for processing prepare blocks to sent to api     #
#                                                               #
#################################################################
#
### Read the file and create list of blocks based on blocksize
#
def get_file_size(file_path):
    return os.path.getsize(file_path)

def check_prepare_audio_video_files(base_filename):
    mp4_filename = f"{base_filename}.mp4"
    mp3_filename = f"{base_filename}.mp3"

    mp4_exists = os.path.isfile(mp4_filename)
    mp3_exists = os.path.isfile(mp3_filename)

    if mp4_exists and not mp3_exists:
        print(f"\nThe file '{mp4_filename}' exists and will be used.")
        # Load the MP4 video file
        video = VideoFileClip(mp4_filename)
        # Extract and save the audio to an MP3 file
        output_filename = f"{base_filename}_extracted.mp3"
        video.audio.write_audiofile(output_filename)
        return output_filename  # Return the name of the extracted MP3 file

    elif mp3_exists:
        print(f"\nThe file '{mp3_filename}' exists and will be used.")
        return mp3_filename  # Return the name of the existing MP3 file

    else:
        print(f"\nSorry, the file '{mp4_filename} OR {mp3_filename}' is missing and is required for processing. Please check the file name and try again.\n\n")
        sys.exit(1)  # Exit the script with a non-zero exit code to indicate an error

def find_near_silences(audio, min_silence_len, silence_thresh, target_length, tolerance):
    silences = detect_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )
    print(f"Detected silences: {silences}")

    near_silences = []
    for start, end in silences:
        silence_mid = (start + end) // 2
        if abs(silence_mid - target_length) <= tolerance:
            near_silences.append((start, end))

    print(f"Near silences: {near_silences}")
    return near_silences

def split_audio_near_silences(audio_path, target_length, tolerance, min_silence_len, silence_thresh):
    audio = AudioSegment.from_mp3(audio_path)
    total_length = len(audio)
    silences = detect_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )

    print(f"Detected silences: {silences}")
    chunks = []
    start_time = 0

    for silence in silences:
        start, end = silence
        if start - start_time >= target_length - tolerance:
            chunks.append(audio[start_time:start])
            start_time = start

    if start_time < total_length:
        chunks.append(audio[start_time:])

    # Combine small chunks if they are too short
    final_chunks = []
    current_chunk = AudioSegment.empty()
    for chunk in chunks:
        if len(current_chunk) + len(chunk) <= target_length + tolerance:
            current_chunk += chunk
        else:
            if len(current_chunk) > 0:
                final_chunks.append(current_chunk)
            current_chunk = chunk

    if len(current_chunk) > 0:
        final_chunks.append(current_chunk)

    print(f"Number of final chunks created: {len(final_chunks)}")
    for i, chunk in enumerate(final_chunks):
        print(f"Chunk {i+1} length: {len(chunk)} ms")

    return final_chunks

def export_audio_chunks(chunks, outputfolder):
    file_names = []
    for i, chunk in enumerate(chunks):
        timestamped = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(outputfolder, f"{timestamped}_{i+1:03d}_audio_chunk.mp3")
        chunk.export(output_path, format="mp3")
        file_names.append((output_path, f"{timestamped}_{i+1:03d}"))
        print(f"Exported {output_path}")

    return file_names
