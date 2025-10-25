
import soundfile as sf
import pysofaconventions as sofa
from scipy.signal import fftconvolve
import glob
import os
import librosa as lb 
import numpy as np

vocals = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\vocals.wav"
bass = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\bass.wav"
drums = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\drums.wav"
piano = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\piano.wav"
other = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\other.wav"  

frame_length = 1024 
hop_length = 512
fs = 16000
# ---------- Load HRTF ----------
sofa_file = sofa.SOFAFile(r'C:\Users\Admin\Downloads\ffmpeg-8.0-essentials_build\subject_003.sofa', 'r')

final_mix = None
fs_global = None


class immersive_audio:
    def __init__(self):
        self.vocals = None
        self.drums = None
        self.bass = None
        self.piano = None
        self.other = None
        self.xs = [self.vocals, self.drums, self.bass, self.piano, self.other]

    def cartesian_to_spherical(self, x, y, z):
        r = np.sqrt(x**2 + y**2 + z**2)
        azimuth = np.degrees(np.arctan2(x, z))
        elevation = np.degrees(np.arcsin(y / r))
        return azimuth, elevation, r

    def get_hrtf(self, sofa_file, az, el):
        positions = sofa_file.getVariableValue('SourcePosition')[:, :2]
        idx = np.argmin((positions[:, 0]-az)**2 + (positions[:, 1]-el)**2)
        hrir_l = sofa_file.getDataIR()[idx, 0, :]
        hrir_r = sofa_file.getDataIR()[idx, 1, :]
        return hrir_l, hrir_r

    def spatialize(self, signal, az, el, distance, sofa_file):
        hrir_l, hrir_r = self.get_hrtf(sofa_file, az, el)
        left = fftconvolve(signal, hrir_l)
        right = fftconvolve(signal, hrir_r)

        # --- Gain mapping for distance ---
        gain = 1 / (1 + distance**2)
        left *= gain
        right *= gain

        return np.stack([left, right], axis=1)

    def compute_gains(self, audio_path, frame_ms=20):
        y, sr = lb.load(audio_path, sr=None)
        frame_len = int(sr * frame_ms / 1000)
        num_frames = int(np.ceil(len(y) / frame_len))
        gains = []
        for i in range(num_frames):
            start = i * frame_len
            end = min((i + 1) * frame_len, len(y))
            frame = y[start:end]
            # Gain: RMS (Root Mean Square) value
            if len(frame) > 0:
                rms = np.sqrt(np.mean(frame ** 2))
            else:
                rms = 0.0
            gains.append(rms)
        return gains

    def mapping(self, sig, fs, sofa_file):
        positions_low = {
            "vocals": (0, 0, 0.00000000000000000000000000000000015),
            "drums": (0, -0.0000000000000000000000000000000015, -0.0000000000000000000000000000000015),
            "bass": (0, -0.00000000000000000000000000000000005, 0.000000000000000000000000000000005),
            "piano": (0.00000000000000000000000000000001, 0, 0.00000000000000000000000000000001),
            "other": (-0.0000000000000000000000000000001, 0, 0.000000000000000000000000000000001)
        }
        positions_high = {
            "vocals": (0.00000000000000000000000000000000015, 0, 0),
            "drums": (0, -0.0000000000000000000000000000000015, -0.0000000000000000000000000000000015),
            "bass": (0, -0.00000000000000000000000000000000005, 0.000000000000000000000000000000005),
            "piano": (0.00000000000000000000000000000001, 0, 0.00000000000000000000000000000001),
            "other": (-0.0000000000000000000000000000001, 0, 0.000000000000000000000000000000001)
        }
        global final_mix, fs_global
        for stem_path in sig:
            # Identify stem type
            if "vocals" in stem_path:
                stem_name = "vocals"
            elif "drums" in stem_path:
                stem_name = "drums"
            elif "bass" in stem_path:
                stem_name = "bass"
            elif "piano" in stem_path:
                stem_name = "piano"
            elif "other" in stem_path:
                stem_name = "other"
            else:
                continue
            gains = self.compute_gains(stem_path)
            avg_gain = np.mean(gains)
            if avg_gain > 1.0:
                x, y, z = positions_high[stem_name]
            else:
                x, y, z = positions_low[stem_name]
            az, el, dist = self.cartesian_to_spherical(x, y, z)
            sig_data, fs_data = sf.read(stem_path)
            if sig_data.ndim == 1:
                sig_data = np.stack([sig_data, sig_data], axis=1)
            left_spatial = self.spatialize(sig_data[:, 0], az, el, dist, sofa_file)
            right_spatial = self.spatialize(sig_data[:, 1], az, el, dist, sofa_file)
            spatial = left_spatial + right_spatial
            if fs_global is None:
                fs_global = fs_data
            if final_mix is None:
                final_mix = spatial
            else:
                min_len = min(len(final_mix), len(spatial))
                final_mix[:min_len] += spatial[:min_len]
        # Make the mix 10x louder before normalization
        final_mix *= 10
        final_mix /= np.max(np.abs(final_mix))
        sf.write(r"C:\Users\Admin\Desktop\chunchun atmos\immersive_mix.wav", final_mix, fs_global, subtype='FLOAT')
        print("✅ immersive_mix.wav created successfully!")

if __name__ == "__main__":
        xs = [vocals, drums, bass, piano, other]
        xp = immersive_audio()
        xp.mapping(xs, fs, sofa_file)