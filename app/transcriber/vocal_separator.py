import torch
import numpy as np
import io
import soundfile as sf
import tempfile
import os
import logging
import subprocess

class VocalSeparator:
    def __init__(self):
        self.sample_rate = 44100  # works for 44.1kHz
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def separate_vocals(self, audio_data: bytes) -> bytes:
        """
        Separate vocals from the mixed audio using Demucs.
        
        Args:
            audio_data: Raw audio data in bytes
            
        Returns:
            bytes: Isolated vocals audio data in bytes
        """
        try:
            # Create a temporary file to store the input audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_in:
                temp_in.write(audio_data)
                temp_in_path = temp_in.name
            
            # Create a temporary directory for the output
            with tempfile.TemporaryDirectory() as temp_out_dir:
                # Use the command-line interface directly
                cmd = [
                    "demucs",  # Use the installed demucs command
                    "--two-stems=vocals",  # Only separate vocals
                    "-n", "htdemucs",  # Use the latest HT-Demucs model
                    "-d", self.device,  # Device to use
                    "--shifts=1",  # Number of random shifts
                    "-o", temp_out_dir,  # Output directory
                    temp_in_path  # Input file
                ]
                
                # Run the command
                process = subprocess.run(
                    cmd, 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                
                # Log the output for debugging
                logging.debug(f"Demucs stdout: {process.stdout.decode()}")
                logging.debug(f"Demucs stderr: {process.stderr.decode()}")
                
                # The output will be in a subdirectory named after the model
                vocals_path = os.path.join(
                    temp_out_dir, 
                    "htdemucs", 
                    os.path.basename(temp_in_path).replace('.wav', ''), 
                    "vocals.wav"
                )
                
                # Check if the file exists
                if not os.path.exists(vocals_path):
                    logging.error(f"Vocals file not found at {vocals_path}")
                    # List the output directory to help debug
                    logging.error(f"Output directory contents: {os.listdir(temp_out_dir)}")
                    if os.path.exists(os.path.join(temp_out_dir, "htdemucs")):
                        logging.error(f"htdemucs directory contents: {os.listdir(os.path.join(temp_out_dir, 'htdemucs'))}")
                    raise FileNotFoundError(f"Vocals file not found at {vocals_path}")
                
                # Read the separated vocals
                with open(vocals_path, 'rb') as f:
                    vocals_data = f.read()
                
                # Clean up the temporary input file
                os.unlink(temp_in_path)
                
                return vocals_data

        except Exception as e:
            logging.error(f"Vocal separation failed: {str(e)}")
            # Return the original audio if separation fails
            logging.warning("Returning original audio due to separation failure")
            return audio_data
