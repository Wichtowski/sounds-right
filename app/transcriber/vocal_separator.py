import torch
import numpy as np  
from demucs.pretrained import get_model
import io
import soundfile as sf

class VocalSeparator:
    def __init__(self):
        # Load the Demucs v4 model (latest version)
        self.model = get_model('htdemucs')
        self.model.eval()
        if torch.cuda.is_available():
            self.model.cuda()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sample_rate = 44100  # Demucs works with 44.1kHz

    def separate_vocals(self, audio_data: bytes) -> bytes:
        """
        Separate vocals from the mixed audio using Demucs.
        
        Args:
            audio_data: Raw audio data in bytes
            
        Returns:
            bytes: Isolated vocals audio data in bytes
        """
        try:
            # Convert bytes to numpy array
            audio_np, sr = sf.read(io.BytesIO(audio_data))
            
            # Convert to mono if stereo
            if len(audio_np.shape) > 1:
                audio_np = audio_np.mean(axis=1)
            
            audio_torch = torch.tensor(audio_np)[None, None, :]
            
            with torch.no_grad():
                audio_torch = audio_torch.to(self.device)
                sources = self.model.separate(audio_torch)
                sources = sources.cpu().numpy()
            
            # Extract vocals (Demucs order is drums, bass, other, vocals)
            vocals = sources[0, 3]  # Get vocals track
            
            # Convert back to bytes
            output_buffer = io.BytesIO()
            sf.write(output_buffer, vocals.T, self.sample_rate, format='WAV')
            return output_buffer.getvalue()

        except Exception as e:
            raise Exception(f"Vocal separation failed: {str(e)}") 
