#!/usr/bin/env python3
""" Text to Audio Generator using ElevenLabs API - Converts text files into audio files using ElevenLabs voice synthesis. - Generates one audio file per sentence for better control and organization. """
import datetime
import shutil
import sys
import ast
import re
import os
import json
import argparse
from pathlib import Path
from typing import List
from elevenlabs import save, Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

class TextToAudioGenerator:
    """Main class for converting text to audio using ElevenLabs API."""
    
    def __init__(self, config=None):
        """Initialize the generator with configuration."""
        load_dotenv()
        
        # Default configuration
        self.config = {
            'input_file': 'input.txt',
            'output_folder': 'output',
            'api_key_name': 'XI_API_KEY',
            'voice': 'oWJ0GSUjVyxG4cvdzY5t',
            'model': 'eleven_multilingual_v2',
            'mode': 'PRODUCTION',
            'max_sentences': 1000  # Maximum sentences to process
        }
        
        # Update with provided config
        if config:
            self.config.update(config)
        
        # Set mode-specific parameters
        if self.config['mode'] in ["TEST", "DEBUG"]:
            self.config['max_sentences'] = 5  # Process only 5 sentences in test mode
        
        # Set paths
        self.base_dir = Path(__file__).parent
        self.input_path = self.base_dir / self.config['input_file']
        self.output_path = self.base_dir / self.config['output_folder']
        
        # Initialize client
        self.client = None
        
    def check_api_key(self):
        """Check if API key is set in environment variables."""
        api_key = os.environ.get(self.config['api_key_name'])
        
        if not api_key or api_key == "Put_your_API_key_here":
            env_file_path = self.base_dir / '.env'
            
            if not env_file_path.exists():
                with open(env_file_path, 'w') as env_file:
                    env_file.write(f'{self.config["api_key_name"]}="Put_your_API_key_here"\n')
                print(f"\nCannot find {self.config['api_key_name']} in environment variables.")
                print(f"Created '.env' file at {env_file_path}")
                print(f"Please add your ElevenLabs API key to the '.env' file.")
                sys.exit()
            else:
                print(f"\nThe '.env' file exists at {env_file_path}")
                print(f"Please ensure your ElevenLabs API key is set correctly.")
                sys.exit()
        
        if self.config['mode'] == "DEBUG":
            print(f"API key {self.config['api_key_name']} is correctly set.\n")
    
    def check_and_create_files(self):
        """Check input file exists and create output folder if needed."""
        if not self.input_path.exists():
            print(f"\nError: Input file '{self.input_path}' not found.")
            print("Please create the file and add your text content.\n")
            sys.exit()
        
        if not self.output_path.exists():
            self.output_path.mkdir(parents=True)
            print(f"Created output folder: {self.output_path}\n")
    
    def backup_existing_files(self):
        """Move existing output files to backup folder."""
        backup_dir = self.output_path / 'backup'
        
        if not backup_dir.exists():
            backup_dir.mkdir()
        
        # Move all files to backup
        for file_path in self.output_path.iterdir():
            if file_path.is_file():
                shutil.move(str(file_path), str(backup_dir / file_path.name))
        
        if any(self.output_path.iterdir()):
            print("Moved existing output files to backup folder.\n")
    
    def is_unwanted_line(self, line):
        """Check if a line should be filtered out (e.g., subtitles)."""
        # Filter subtitle numbers and timestamps
        if re.match(r'^\d+ ".+" \(\d+\)$', line):
            return True
        if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}$', line):
            return True
        return False
    
    def _read_input_text(self) -> str:
        """Read the input text file."""
        with open(self.input_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _clean_text_lines(self, text: str) -> List[str]:
        """Remove subtitle formatting and clean text lines."""
        lines = text.split('\n')
        return [line for line in lines if not self.is_unwanted_line(line)]
    
    def _extract_paragraphs(self, lines: List[str]) -> List[str]:
        """Group lines into paragraphs preserving structure."""
        paragraphs = []
        current_para = []
        
        for line in lines:
            if line.strip():
                current_para.append(line.strip())
            elif current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
        
        if current_para:
            paragraphs.append(' '.join(current_para))
        
        return paragraphs
    
    def _split_into_sentences(self, paragraph: str) -> List[str]:
        """Split a paragraph into sentences with smart handling."""
        # Protect abbreviations
        paragraph = self._protect_abbreviations(paragraph)
        
        # Enhanced sentence splitting regex
        sentence_endings = re.compile(
            r'(?<!\w\.\w.)' +  # Not abbreviations like U.S.A.
            r'(?<![A-Z][a-z]\.)' +  # Not titles like Mr.
            r'(?<![A-Z]\.)' +  # Not initials
            r'(?<=[\.!?।])' +  # After sentence endings
            r'(?:\[[a-zA-Z0-9]+\])?' +  # Optional citation
            r'(?:\s+|"|\')?' +  # Optional whitespace/quotes
            r'(?=[A-Z"\']|$)'  # Before capital/quote/end
        )
        
        sentences = sentence_endings.split(paragraph)
        
        # Restore abbreviations and clean
        return [self._restore_abbreviations(s.strip()) 
                for s in sentences if s.strip()]
    
    def parse_text(self) -> List[str]:
        """Parse input text into clean sentences."""
        # Read and clean text
        text = self._read_input_text()
        cleaned_lines = self._clean_text_lines(text)
        
        # Extract paragraphs
        paragraphs = self._extract_paragraphs(cleaned_lines)
        
        # Split into sentences
        sentences = []
        for paragraph in paragraphs:
            sentences.extend(self._split_into_sentences(paragraph))
        
        # Merge fragments
        sentences = self._merge_fragments(sentences)
        
        # Debug output
        if self.config['mode'] == "DEBUG":
            self._print_debug_sentences(sentences)
        
        return sentences
    
    def _print_debug_sentences(self, sentences: List[str]) -> None:
        """Print debug information about parsed sentences."""
        print(f"Parsed {len(sentences)} sentences:")
        for i, sentence in enumerate(sentences[:10], 1):
            truncated = sentence[:80] + "..." if len(sentence) > 80 else sentence
            print(f"  {i}. {truncated}")
        if len(sentences) > 10:
            print(f"  ... and {len(sentences) - 10} more sentences")
        print()
    
    def _protect_abbreviations(self, text):
        """Temporarily replace periods in common abbreviations."""
        # Common abbreviations
        abbreviations = [
            'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Sr.', 'Jr.',
            'Ph.D.', 'M.D.', 'B.A.', 'M.A.', 'B.S.', 'M.S.',
            'i.e.', 'e.g.', 'etc.', 'vs.', 'Inc.', 'Ltd.', 'Co.',
            'Jan.', 'Feb.', 'Mar.', 'Apr.', 'Jun.', 'Jul.', 'Aug.',
            'Sep.', 'Sept.', 'Oct.', 'Nov.', 'Dec.',
            'Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.', 'Sun.',
            'U.S.', 'U.K.', 'U.N.', 'E.U.', 'U.S.A.'
        ]
        
        protected_text = text
        for abbr in abbreviations:
            protected_text = protected_text.replace(abbr, abbr.replace('.', '☐'))
        
        return protected_text
    
    def _restore_abbreviations(self, text):
        """Restore periods in abbreviations."""
        return text.replace('☐', '.')
    
    def _merge_fragments(self, sentences):
        """Merge very short fragments with previous sentences."""
        if not sentences:
            return sentences
        
        merged = []
        buffer = sentences[0]
        
        for sentence in sentences[1:]:
            # Check if sentence is just a citation or very short fragment
            is_citation_only = re.match(r'^\[[a-zA-Z0-9]+\]$', sentence.strip())
            
            # If current sentence is very short or starts with lowercase, merge it
            # But don't merge if it's a proper sentence that just happens to be short
            if (is_citation_only or 
                (len(sentence) < 20 and not sentence[0].isupper() and not sentence[0] in ['"', "'"])):
                buffer += ' ' + sentence
            else:
                merged.append(buffer)
                buffer = sentence
        
        merged.append(buffer)
        return merged
    
    def save_sentences_reference(self, sentences, voice_name_id):
        """Save all sentences to a reference file."""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        reference_file = self.output_path / f"{timestamp}_000_{voice_name_id}_sentences_reference.txt"
        
        with open(reference_file, 'w', encoding='utf-8') as f:
            f.write(f"=== SENTENCES REFERENCE FILE ===\n")
            f.write(f"Total sentences: {len(sentences)}\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Voice: {voice_name_id}\n")
            f.write(f"Model: {self.config['model']}\n\n")
            
            for i, sentence in enumerate(sentences, 1):
                f.write(f"[{i:04d}] {sentence}\n")
        
        return reference_file
    
    
    def generate_audio_for_sentences(self, sentences, voice_name_id):
        """Generate individual audio files for each sentence."""
        # Initialize client
        self.client = ElevenLabs(api_key=os.environ.get(self.config['api_key_name']))
        
        # Prepare output files
        session_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create session folder
        session_folder = self.output_path / f"{session_timestamp}_{voice_name_id}"
        session_folder.mkdir(exist_ok=True)
        
        # Create mapping file
        mapping_file = session_folder / f"000_sentence_mapping.txt"
        
        # Process sentences
        sentences_to_process = min(len(sentences), self.config['max_sentences'])
        print(f"Processing {sentences_to_process} sentences individually...\n")
        
        successful = 0
        failed = 0
        
        with open(mapping_file, 'w', encoding='utf-8') as map_f:
            map_f.write(f"=== SENTENCE TO AUDIO MAPPING ===\n")
            map_f.write(f"Session: {session_timestamp}\n")
            map_f.write(f"Voice: {voice_name_id}\n")
            map_f.write(f"Model: {self.config['model']}\n\n")
            
            for i, sentence in enumerate(sentences[:sentences_to_process]):
                sentence_num = i + 1
                
                try:
                    # Generate audio for single sentence
                    audio = self.client.generate(
                        text=sentence,
                        voice=self.config['voice'],
                        model=self.config['model']
                    )
                    
                    # Save audio file with shortened filename
                    audio_file = session_folder / f"{sentence_num:04d}.mp3"
                    save(audio, str(audio_file))
                    
                    # Save sentence text file with shortened filename
                    text_file = session_folder / f"{sentence_num:04d}.txt"
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(sentence)
                    
                    # Update mapping file
                    map_f.write(f"[{sentence_num:04d}] {audio_file.name} → {sentence}\n")
                    map_f.flush()  # Ensure it's written immediately
                    
                    print(f"✓ [{sentence_num:04d}/{sentences_to_process:04d}] Generated: {audio_file.name}")
                    successful += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"✗ [{sentence_num:04d}/{sentences_to_process:04d}] Error: {error_msg}")
                    map_f.write(f"[{sentence_num:04d}] ERROR → {sentence} (Error: {error_msg})\n")
                    map_f.flush()
                    failed += 1
            
            # Write summary
            map_f.write(f"\n=== SUMMARY ===\n")
            map_f.write(f"Total sentences: {sentences_to_process}\n")
            map_f.write(f"Successful: {successful}\n")
            map_f.write(f"Failed: {failed}\n")
        
        print(f"\n=== GENERATION COMPLETE ===")
        print(f"✓ Successful: {successful}")
        print(f"✗ Failed: {failed}")
        print(f"Files saved to: {session_folder}")
        
        return session_folder
    
    def list_voices(self):
        """List all available voices with comprehensive information."""
        print("=== ElevenLabs Voice List ===\n")
        
        # Initialize client
        self.client = ElevenLabs(api_key=os.environ.get(self.config['api_key_name']))
        
        try:
            # Fetch voices using the client
            voices = self.client.voices.get_all()
            
            if not voices.voices:
                print("No voices found.")
                return
            
            print(f"Total voices available: {len(voices.voices)}\n")
            print(f"{'='*120}")
            print(f"{'Name':<30} {'Voice ID':<25} {'Category':<15} {'Labels':<30}")
            print(f"{'='*120}")
            
            voice_data = []
            
            for voice in voices.voices:
                name = voice.name[:30]
                voice_id = voice.voice_id[:25]
                category = voice.category if hasattr(voice, 'category') else 'N/A'
                
                # Extract labels information
                labels_info = []
                if hasattr(voice, 'labels') and voice.labels:
                    for key, value in voice.labels.items():
                        if value:
                            labels_info.append(f"{key}:{value}")
                
                labels_str = ', '.join(labels_info[:3])[:30] if labels_info else 'N/A'
                
                print(f"{name:<30} {voice_id:<25} {category:<15} {labels_str:<30}")
                
                # Collect full voice data for optional JSON export
                voice_dict = {
                    'name': voice.name,
                    'voice_id': voice.voice_id,
                    'category': category,
                    'labels': voice.labels if hasattr(voice, 'labels') else {},
                    'preview_url': voice.preview_url if hasattr(voice, 'preview_url') else None,
                    'available_for_tiers': voice.available_for_tiers if hasattr(voice, 'available_for_tiers') else [],
                    'settings': voice.settings.__dict__ if hasattr(voice, 'settings') and voice.settings else None
                }
                
                # Add additional attributes if available
                if hasattr(voice, 'description'):
                    voice_dict['description'] = voice.description
                if hasattr(voice, 'samples'):
                    voice_dict['samples'] = voice.samples
                
                voice_data.append(voice_dict)
            
            print(f"{'='*120}")
            
            # Offer to save detailed information
            save_option = input("\nSave detailed voice information to JSON file? (y/n): ").strip().lower()
            if save_option == 'y':
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"voices_list_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(voice_data, f, indent=2, ensure_ascii=False)
                print(f"Voice data saved to: {filename}")
                
                # Also create a detailed text report
                report_filename = f"voices_report_{timestamp}.txt"
                with open(report_filename, 'w', encoding='utf-8') as f:
                    f.write("=== ELEVENLABS VOICE DETAILED REPORT ===\n")
                    f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total voices: {len(voice_data)}\n\n")
                    
                    for i, voice in enumerate(voice_data, 1):
                        f.write(f"[{i}] {voice['name']}\n")
                        f.write(f"    Voice ID: {voice['voice_id']}\n")
                        f.write(f"    Category: {voice['category']}\n")
                        
                        if voice.get('description'):
                            f.write(f"    Description: {voice['description']}\n")
                        
                        if voice.get('labels'):
                            f.write("    Labels:\n")
                            for key, value in voice['labels'].items():
                                if value:
                                    f.write(f"        - {key}: {value}\n")
                        
                        if voice.get('preview_url'):
                            f.write(f"    Preview URL: {voice['preview_url']}\n")
                        
                        if voice.get('available_for_tiers'):
                            f.write(f"    Available for tiers: {', '.join(voice['available_for_tiers'])}\n")
                        
                        f.write("\n")
                
                print(f"Detailed report saved to: {report_filename}")
                
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return
    
    def get_voice_name_id(self):
        """Get voice name_id format by fetching voice details."""
        # Initialize client if not already done
        if not self.client:
            self.client = ElevenLabs(api_key=os.environ.get(self.config['api_key_name']))
        
        try:
            # Fetch all voices to find the matching one
            voices = self.client.voices.get_all()
            
            for voice in voices.voices:
                if voice.voice_id == self.config['voice']:
                    # Create name_id format: sanitize name for filesystem
                    # Remove all non-alphanumeric characters except spaces, then replace spaces with underscores
                    safe_name = re.sub(r'[^a-zA-Z0-9\s]', '', voice.name)
                    safe_name = re.sub(r'\s+', '_', safe_name.strip())
                    
                    # Shorten the name if it's too long (max 50 chars for name part)
                    if len(safe_name) > 50:
                        # Keep first and last parts of the name
                        safe_name = safe_name[:25] + "..." + safe_name[-22:]
                    
                    # Return shortened name with voice ID (last 8 chars of ID for brevity)
                    return f"{safe_name}_{voice.voice_id[-8:]}"
            
            # If voice not found, return just the last 8 chars of ID
            return self.config['voice'][-8:]
            
        except Exception as e:
            print(f"Warning: Could not fetch voice name, using ID only: {e}")
            return self.config['voice'][-8:]
    
    def run(self):
        """Run the complete text-to-audio generation process."""
        print("=== ElevenLabs Text-to-Audio Generator ===\n")
        
        # Validate environment
        self.check_api_key()
        self.check_and_create_files()
        self.backup_existing_files()
        
        # Process text
        print("Reading and processing input text...")
        sentences = self.parse_text()
        
        if not sentences:
            print("No sentences found in input file!")
            return
        
        print(f"Found {len(sentences)} sentences in total.\n")
        
        # Get voice name_id format
        print("Fetching voice information...")
        voice_name_id = self.get_voice_name_id()
        print(f"Using voice: {voice_name_id}\n")
        
        # Save reference file
        reference_file = self.save_sentences_reference(sentences, voice_name_id)
        print(f"Reference file saved: {reference_file.name}\n")
        
        # Generate audio for each sentence
        session_folder = self.generate_audio_for_sentences(sentences, voice_name_id)

def check_module_installed(module_name):
    """Check if a module is installed."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def get_imported_modules(script_path):
    """Extract imported modules from a Python script."""
    with open(script_path, "r") as file:
        tree = ast.parse(file.read(), filename=script_path)
    
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.append(node.module)
    return imported_modules

def check_required_modules():
    """Check if all required modules are installed."""
    required_modules = ['elevenlabs', 'dotenv']
    missing_modules = [module for module in required_modules if not check_module_installed(module)]
    
    if missing_modules:
        print("The following modules are not installed:")
        for module in missing_modules:
            print(f"- {module}")
        print("\nTo install the missing modules, run:")
        for module in missing_modules:
            print(f"pip install {module}")
        sys.exit("Script terminated due to missing modules.")

# Check modules before importing them
check_required_modules()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='ElevenLabs Text-to-Audio Generator')
    parser.add_argument('action', nargs='?', default='generate', help='Action to perform: generate (default) or listvoices')
    parser.add_argument('--mode', choices=['TEST', 'DEBUG', 'PRODUCTION'], default='TEST', help='Operating mode')
    parser.add_argument('--voice', help='Voice ID or name to use')
    parser.add_argument('--model', help='Model to use for generation')
    parser.add_argument('--max-sentences', type=int, help='Maximum number of sentences to process')
    
    args = parser.parse_args()
    
    # Build configuration from arguments
    config = {'mode': args.mode}
    if args.voice:
        config['voice'] = args.voice
    if args.model:
        config['model'] = args.model
    if args.max_sentences:
        config['max_sentences'] = args.max_sentences
    
    generator = TextToAudioGenerator(config)
    
    if args.action.lower() == 'listvoices':
        # Check API key before listing voices
        generator.check_api_key()
        generator.list_voices()
    else:
        generator.run()


if __name__ == "__main__":
    main()
