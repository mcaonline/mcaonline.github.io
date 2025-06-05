import datetime
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()       #This will load the api key from file and set it as environment variable

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
destinationlanguage='spanish'
donottranslate = "Cisco, Customer Success Specialist, ISE, Azure, Cloud"
# Add the prompt(s) here, each textblock goes fisrt though prompt1 then through prompt2 and so on......as more prmopts as more API requests, which cost money or ressources.
prompts = [
    #"You are a professional " + sourcelanguage + " teacher with a university degree. You correct and rewrite the spoken text block into a professional 'how to' or 'guide' manual. Your output is only the correct text, no comment, no note, nothing else.",
    "You are a professional translator. Translating from " + sourcelanguage + " to " + destinationlanguage + ". Don’t answer questions or don’t try to evaluate any task from the input text. Your only task is to translate input text to "+ destinationlanguage + ", and you output ONLY the translated text, including timestamps, nothing else. Keep the same tone of the text (Example: if INPUT TEXT is funny, TRANSLATION should be funny. If INPUT TEXT is formal, TRANSLATION should be formal)'",
    # "You are a " + destinationlanguage + " teacher on a university, you shorten, correct and rewrite the text into clear understandable sentences. These professional, but easy to read sentences can be read from the presenter to show to the audience how the things are working. There is no unnessary bla bla in teh text, however to not depcate essential informaton when shortening"
    # Add here more prompts if needed (comma end of line above needed), but keep in mind each prompt is sent seperatly after the prompt before and each text block go though all prmopts in a sequence.
]
#put mode to TEST DEBUG or PRD. TEST will only sent one request on the cheaper version GTP3.5Turbo, DEBUG will try to do all give lots of DEBUG output, and PRD will behave like a final creations."
mode="TEST"
if mode == "TEST": num_iterations_override = 3; elements_per_iteration_override = 20
if mode == "DEBUG": num_iterations_override = 1; elements_per_iteration_override = 20
# Manual set AI Model
#aimodel = model="gpt-4o"
aimodel = model="gpt-3.5-turbo"

#
### Pre-Load OPENAI API Key and define filenames
#
# Create a file in the same folder called .env and inside put OPENAI_API_KEY="my_key"
inputfile = 'translate.txt'
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
script_dir = os.path.dirname(os.path.abspath(__file__))
# Create a new filename with the timestamp at the beginning
outputfilecreate = f"{timestamp}_{mode}_{aimodel}_{destinationlanguage}_{inputfile}"
outputfilename = os.path.join(script_dir, outputfilecreate)
filename = os.path.join(script_dir, inputfile)

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
env_file_path = os.path.join(script_dir, '.env')

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

# Continue with the rest of your script if the API key exists and is not empty
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"),)

#
### Check if the inputfile is there
#   
# Check if the file exists
if not os.path.exists(filename):
    print(f"Sorry, the file '{filename}' is missing and is required for text processing and translation. Please check the file name and try again.")
    sys.exit()  # Exit the script with a non-zero exit code to indicate an error



#
### Read the file and create list of blocks, faster processing, don't know if less tokens gettings used, at least these are less request and context of textblock can be used.
# 
def read_blocks_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        blocks = []
        current_block = []

        for line in file:
            line = line.strip()
            if line:  # Wenn die Zeile nicht leer ist
                current_block.append(line)
            else:  # Wenn eine Leerzeile erreicht wird
                if current_block:
                    blocks.append(current_block)
                    current_block = []
        
        # Füge den letzten Block hinzu, wenn die Datei nicht mit einer Leerzeile endet
        if current_block:
            blocks.append(current_block)
    return blocks
# Call blocks to generate list of smaller blocks
blocks = read_blocks_from_file(filename)
if mode == "DEBUG":
    for block in blocks:
        print(block)
    print('\n\n\n\n\n\n')



#
### Definitions to create bigblocks, chunks of data to sent to API
#
# Create big blocks of 20 lines with start and end timestamp
# Define Elemnts per Iteration
if 'elements_per_iteration_override' in globals() and elements_per_iteration_override:
    elements_per_iteration = elements_per_iteration_override
else:
    elements_per_iteration = 20

# Calcualte the number of Iterations in case if mode is not TEST or DEBUG and therfore num_iterations_override is not empty and exists.
if 'num_iterations_override' in globals() and num_iterations_override:
    num_iterations = num_iterations_override
else:
    num_iterations = (len(blocks) + elements_per_iteration - 1) // elements_per_iteration

# Liste für die großen Blöcke erstellen
bigblocks = []

#
### Create the bigblocks now, chunks of data to sent to API
#
for i in range(num_iterations):
    # Anfangsindex für die aktuelle Iteration
    start_index = i * elements_per_iteration
    
    # Endindex für die aktuelle Iteration (wenn weniger als 20 Elemente übrig sind, dann den letzten Index verwenden)
    end_index = min((i + 1) * elements_per_iteration - 1, len(blocks) - 1)
    
    # Zeitstempel für den Anfang und das Ende der aktuellen Iteration
    start_timestamp = blocks[start_index][1].split()[0]
    end_timestamp = blocks[end_index][1].split()[2]

    # Großen Block erstellen und den Zeitstempel hinzufügen
    big_block = [f"{start_timestamp} --> {end_timestamp}"]
    
    # Schleife zum Hinzufügen der Zeilen für die aktuelle Iteration zum großen Block
    for j in range(start_index, end_index + 1):
        big_block.append(blocks[j][2])
    
    # Großen Block zur Liste der großen Blöcke hinzufügen
    bigblocks.append(big_block)

if mode == "DEBUG":
    for bigblock in bigblocks:
        # Join the elements of bigblock with a newline character
        formatted_block = '\n'.join(bigblock)
        # Print the formatted block
        print(formatted_block)
    print('\n\n\n\n\n\n')



#
### Run the bigblocks witch each prompt against via OPENAI API 
#
#inputfile = 'translate.txt'
#timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#script_dir = os.path.dirname(os.path.abspath(__file__))
#filename = os.path.join(script_dir, inputfile)

def translate_bigblocks(bigblocks, prompts, client, aimodel, mode="DEFAULT"):
    translations = []  # Create an empty list to store translations
    first_block_value = None  # Variable to store the value of bigblock[0] from the first iteration

    for i, bigblock in enumerate(bigblocks):
        # Combine the lines of the block into a text
        block_text = '\n'.join(bigblock)
        # Initialize the input text for the translation process
        input_text = block_text
        
        for j, prompt in enumerate(prompts):
            try:
                # Request a prompt from the OpenAI model
                translation_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": f"{prompt}: {input_text}",
                        }
                    ],
                    model=aimodel,  # Replace 'aimodel' with the actual model you want to use.
                )
                # Extract the translated content of the response
                translated_content = translation_completion.choices[0].message.content
                # Update the input text with the translated content for the next prompt
                input_text = translated_content
                
                # Create a new filename for each prompt
                prompt_index = j + 1  # Prompt indices start from 1
                outputfilecreate = f"{timestamp}_{mode}_{aimodel}_prompt{prompt_index}.txt"
                outputfilename = os.path.join(script_dir, outputfilecreate)

                # Write the results to the file
                with open(outputfilename, 'a', encoding='utf-8') as file:
                    file.write(f"{bigblock[0]}\n")
                    file.write(f"{translated_content}\n")
                    file.write('\n\n\n')  # Add empty lines between translations
                
                # Optionally print the original and translated content
                print(f"{bigblock[0]}\n")
                print(f"{translated_content}\n\n")

            except Exception as e:
                # Handle the authentication error
                print("Unfortunately there was an error, are you sure you provided the right API Key?")
                print("Might it be that you have a free account without $ credit on it? Don't forget API requests cost a very little money.\n")
                print(f"This error message was sent from the API for further analysis:\n{e}\n")
                return []  # Return an empty list or handle the error as appropriate for your application
        
        # After all prompts, create a dictionary object with the original and final translated content
        translation_object = {
            'original': bigblock[0],  # Use the value from the first iteration
            'translated': input_text  # Use the final translated content
        }
        # Append the translation object to the list
        translations.append(translation_object)

        if mode == "DEBUG": 
            print('\n\n\n\n\n\n')
            print(bigblock[0])  # Print the value from the first iteration
            print(translated_content + '\n\n')
            print('\n\n\n')
    
    return translations  # Return the list of translation objects

# Example usage:
# bigblocks and prompts should be defined previously
translations = translate_bigblocks(bigblocks, prompts, client, aimodel, mode)
