import subprocess
from typing import Optional
from PIL import Image
from loguru import logger
import os

class TesseractOCR:
    """Wrapper for Tesseract OCR execution."""
    
    def __init__(self, tesseract_cmd: str = "tesseract"):
        self.tesseract_cmd = tesseract_cmd

    def image_to_string(self, image: Image.Image, lang: str = "eng") -> str:
        """Runs Tesseract on a PIL Image and returns the text."""
        temp_img = "temp_ocr_input.png"
        temp_out = "temp_ocr_output" 
        
        try:
            image.save(temp_img)
            # Correcting keyword from capture_with_output to capture_output
            cmd = [self.tesseract_cmd, temp_img, temp_out, "-l", lang]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            output_file = temp_out + ".txt"
            if os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8") as f:
                    text = f.read()
                os.remove(output_file)
                return text.strip()
            return ""
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Tesseract failed: {e.stderr}")
            return f"Error: Tesseract OCR failed ({e.returncode})"
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            return f"Error: {str(e)}"
        finally:
            if os.path.exists(temp_img):
                try:
                    os.remove(temp_img)
                except:
                    pass

class TesseractProvider:
    """Adapter for Tesseract OCR."""
    
    def __init__(self):
        self.ocr = TesseractOCR()

    def process_image(self, image: Image.Image) -> str:
        return self.ocr.image_to_string(image)
