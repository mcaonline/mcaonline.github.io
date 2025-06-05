import datetime
import os
import sys
import re

from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()       #This will load the key from file and set it as environment variable

#################################################################
#                                                               #
#                                                               #
#   Defintions, Prechecks, Modules, Files, APIKey               #
#                                                               #
#                                                               #
#################################################################
#
### Definitions of Languages, Prompt, Mode and AI Model 
#
sourcelanguage='english'
destinationlanguage='german'
donottranslate = "adopting, adoption, session, Ask the Expert, Cisco, Customer Success Specialist, ISE, Azure, Cloud, Cisco Secure Firewall, Health-Check"  
# Add the prompt(s) here, each textblock goes fisrt though prompt1 then through prompt2 and so on, each run creates its own file (per prompt)......as more prompts as more API requests, which cost money or ressources.
systemprompts = [
    "You are a professional " + sourcelanguage + " teacher with a university degree. You correct and rewrite the spoken text block into a professional 'how to' or 'guide' manual. Your output is only the correct text, no comment, no note, nothing else.",
    #"You are a professional translator. Translating from " + sourcelanguage + " to " + destinationlanguage + ". Do not translate words like:" + donottranslate +". Don’t answer questions or don’t try to evaluate any task from the input text. Your only task is to translate input text to "+ destinationlanguage + ", and you output ONLY the translated text, no timestamps, nothing else. Keep the same tone of the text (Example: if INPUT TEXT is funny, TRANSLATION should be funny. If INPUT TEXT is formal, TRANSLATION should be formal).",
    "You are a professional presentator, please rewrite the manual into a fluent spoken text, and write it as a " + destinationlanguage + " would write or speak this text, make also from many short sentences bigger ones to make it more fluent. remove all headlines, comments, etc. . Abrevations must be still in the text since we need to present them also.",
    #You are a professional " + sourcelanguage + " teacher with a university degree. You correct and rewrite the spoken text block into a professional 'how to' or 'guide' manual. Your output is only the correct text, no comment, no note, nothing else.",
    #"You are a professional presentator, please rewrite the manual into a fluent spoken text, and write it as a would write or speak this text, make also from many short sentences bigger ones to make it more fluent. remove all headlines, comments, etc. . Abrevations must be still in the text since we need to present them also.",
    #'You are a professional teacher with a university degree. Please rewrite the text in using easy, everyday words, as people naturally speak or write. Combine short sentences into longer, smoother ones to make it flow better. Remove all titles, comments, and other extra parts. Keep all abbreviations as they need to be in the presentation.",
    #"Translate the manual into "+ destinationlanguage +" language for an ordinary men, using easy, everyday words, as people naturally speak or write.",
    "You are a " + destinationlanguage + " teacher at a university. Please review the sentences for grammar and fluent readability, and rewrite if needed. You output ONLY the correct text, no comments, no explanations, nothing else.",

]

# Put mode to TEST DEBUG or PRD. TEST will only sent one request on the cheaper version GTP3.5Turbo, DEBUG will try to do all give lots of DEBUG output, and PRD will behave like a final creations."
mode="PRD"
if mode == "TEST": aimodel = model="gpt-3.5-turbo"; maxloops = 1
if mode == "TEST4": aimodel = model="gpt-4o"; maxloops = 3
if mode == "DEBUG": aimodel = model="gpt-3.5-turbo"; maxloops = 2
if mode == "PRD": aimodel = model="gpt-4o"; maxloops = 10000

blocksize=1700      # define the maximum blocksize of sentences to sent to api, 1000 means as many sentences which are less then 1000 chars.
inputfilename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'translate.txt')
timestamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
#
### Check if all needed modules are installed and if not, exit script and tell user how to install
#
# List of modules to check. Each tuple contains the import name and the pip package name.
modules_to_check = [('openai', 'openai'), ('dotenv', 'python-dotenv')]
# Function to check if a module is installed
def check_module_installed(import_name):
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

# Check all modules and collect the ones that are not installed
missing_modules = [pkg_name for import_name, pkg_name in modules_to_check if not check_module_installed(import_name)]

# If there are missing modules, print instructions and exit
if missing_modules:
    print("The following modules are not installed:")
    for module in missing_modules:
        print(f"- {module}") 
    print("\nTo install the missing modules, run the following command(s):")
    for module in missing_modules:
        print(f"pip install {module}")
    # Exit the script immediately
    sys.exit("Script has been terminated due to missing modules.")
# If all modules are installed, continue with the rest of the script
if mode == "DEBUG":
    print("All required modules are installed.\n")

#
### Check if API KEY is existing, if not create file and put default Key in - inform user where to get key and how to add it here.
#   If all is good load the API Key
# Get the directory where the script is located
env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

# Check if the environment variable 'OPENAI_API_KEY' exists and is not empty
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key or api_key == "Put_your_API_key_here":
    print(f"Cannot find the OPENAI_API_KEY in your environmentvariables.")
    # If the environment variable does not exist or is empty, check for '.env' file
    if not os.path.exists(env_file_path):
        # If '.env' file does not exist, create it with the specified line
        with open(env_file_path, 'w') as env_file:
            env_file.write('OPENAI_API_KEY="Put_your_API_key_here"\n')
        # Inform the user that the file has been created and exit the script
        print(f"The '.env' file has been created at {env_file_path}. Please add your OpenAI API key to the '.env' file.")
        exit()
    else:
        print(f"The '.env' file exists at {env_file_path}.")
        print(f"Please ensure your OpenAI API key is set in the '.env' file correctly like: OPENAI_API_KEY=\"Put_your_API_key_here\"")
        exit()
else:
    if mode == "DEBUG":
        print("The 'OPENAI_API_KEY' environment variable is set.\n")

# Continue Load the API Key with the rest of your script if the API key exists and is not empty
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"),)

#
### Check if the inputfile is there
#   
# Check if the file exists
if not os.path.exists(inputfilename):
    print(f"Sorry, the file '{inputfilename}' is missing and is required for text processing and translation. Please check the file name and try again.")
    sys.exit()  # Exit the script with a non-zero exit code to indicate an error


#################################################################
#                                                               #
#                                                               #
#   Load File for processing prepare blocks to sent to api      #
#                                                               #
#                                                               #
#################################################################
#
### Read the file and create list of blocks, faster processing, don't know if less tokens gettings used, at least these are less request and context of textblock can be used.
# 

def is_unwanted_line(line):
    # Check if a line is of the unwanted transcript format with timestamps (like webex), e.g., 1 "Name" (931653120), 00:00:04.435 --> 00:00:16.229
    # Check for the pattern: digit, "Name", (number)
    if re.match(r'^\d+ ".+" \(\d+\)$', line):
        return True
    # Check for the time range pattern
    if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$', line):
        return True
    return False

def read_sentences_from_file(inputfilename):
    with open(inputfilename, 'r', encoding='utf-8') as file:
        sentences = []
        for line in file:
            line = line.strip()
            if line and not is_unwanted_line(line):
                sentences.append(line)
    return sentences

def create_bigblocks(sentences):
    bigblocks = []
    current_block = ''
    for sentence in sentences:
        if len(current_block) + len(sentence) <= blocksize:
            current_block += sentence + ' '
        else:
            bigblocks.append(current_block.strip())
            current_block = sentence + ' '
    # Add the last block if it's not empty
    if current_block:
        bigblocks.append(current_block.strip())
    return bigblocks

# Call sentences to generate list of sentences
sentences = read_sentences_from_file(inputfilename)
if mode == "DEBUG": [print(sentence + '\n') for sentence in sentences]

# Create bigblocks
bigblocks = create_bigblocks(sentences)

if mode == "DEBUG":
    for bigblock in bigblocks:
        print(bigblock+'\n')

#################################################################
#                                                               #
#                                                               #
#   Send to API and create / append to files on the fly         #
#                                                               #
#                                                               #
#################################################################
#
### Run the bigblocks witch each prompt against via OPENAI API 
#
def process_bigblocks(bigblocks, systemprompts, client, aimodel, destinationlanguage, mode):
    loop_counter = 0
    for bigblock in bigblocks:
        current_content = bigblock  # Start with the original bigblock content
        if loop_counter >= maxloops:
                break
        for j, systemprompt in enumerate(systemprompts):
            try:
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": systemprompt},
                        {"role": "user", "content": current_content}
                    ],
                    model=aimodel,  # Replace 'aimodel' with the actual model you want to use
                )

                # Extract the translated content of the response
                current_content = response.choices[0].message.content

                # Create the output filename based on the prompt index
                prompt_index = j + 1  # Prompt indices start from 1
                outputfilename = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{timestamp}_{mode}_{aimodel}_{destinationlanguage}_prompt{prompt_index}.txt")

                # Write the results to the corresponding file
                with open(outputfilename, 'a', encoding='utf-8') as file:
                    file.write(f"{current_content}\n\n")

                # Optionally print the original and translated content
                print(f"Systemprompt used: {systemprompt}\n")
                print(f"{current_content}\n")

            except Exception as e:
                # Handle exceptions properly
                print("Unfortunately, there was an error. Are you sure you provided the right API Key?")
                print("Might it be that you have a free account without $ credit on it? Don't forget API requests cost a very little money.\n")
                print(f"This error message was sent from the API for further analysis:\n{e}\n")
                return  # Exit the function on error
        loop_counter += 1
    return

process_bigblocks(bigblocks, systemprompts, client, aimodel, destinationlanguage, mode)
