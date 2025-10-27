import soundfile as sf
import pysofaconventions as sofa
from scipy.signal import fftconvolve
import librosa as lb
import numpy as np
import os
import math

# --- Configuration ---
TARGET_FS = 48000
# Define sensible gain thresholds for dynamic positioning
VOCALS_GAIN_THRESHOLD = 0.4
BASS_GAIN_THRESHOLD = 0.3
DRUMS_GAIN_THRESHOLD = 0.3
PIANO_GAIN_THRESHOLD = 0.2
OTHER_GAIN_THRESHOLD = 0.2


# --- File Paths (Placeholder: replace with your actual paths) ---
vocals = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\vocals.wav"
bass = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\bass.wav"
drums = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\drums.wav"
piano = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\piano.wav"
other = r"C:\Users\Admin\Desktop\chunchun atmos\output\32 - John Summit - EAT THE BASS (1)\other.wav"
SOFA_FILE_PATH = r'C:\Users\Admin\Downloads\ffmpeg-8.0-essentials_build\subject_003.sofa'
OUTPUT_PATH = r"C:\Users\Admin\Desktop\chunchun atmos\immersive_mix_pro_louder_stems.wav"

# --- Dynamic Stem Positions (Balanced - Louder Instruments) ---
# (x, y, z, base_gain)
positions_low = {
    "vocals": (0.0, 0.0, -1.0, 1.0),     # Base gain remains 1.0
    "drums": (0.8, 0.0, -1.0, 2.0),      # INCREASED gain from 1.5 to 2.0
    "bass": (-0.8, -0.1, -1.0, 2.0),     # INCREASED gain from 1.5 to 2.0
    "piano": (1.0, 0.5, 0.5, 2.0),       # INCREASED gain from 1.5 to 2.0
    "other": (-1.0, 0.5, 0.5, 2.0)       # INCREASED gain from 1.5 to 2.0
}
positions_high = {
    "vocals": (0.0, 0.0, -0.7, 1.0),     # Base gain remains 1.0
    "drums": (1.0, 0.3, -1.2, 2.0),      # INCREASED gain from 1.5 to 2.0
    "bass": (-1.0, -0.2, -1.2, 2.0),     # INCREASED gain from 1.5 to 2.0
    "piano": (0.0, 1.5, -0.7, 2.0),      # INCREASED gain from 1.5 to 2.0
    "other": (0.0, -1.0, -0.7, 2.0)      # INCREASED gain from 1.5 to 2.0
}

# Define which stems should be mirrored for a wider stereo image
STEMS_TO_MIRROR = ["drums", "bass", "piano", "other"]


class ImmersiveAudio:
    def __init__(self, sofa_file_path):
        self.sofa_file = sofa.SOFAFile(sofa_file_path, 'r')
        self.positions = self.sofa_file.getVariableValue('SourcePosition')[:, :2]
        
        # Robustly retrieve and store the HRTF Sample Rate
        try:
            self.hrtf_fs = int(self.sofa_file.getSamplingRate())
        except Exception:
            self.hrtf_fs = TARGET_FS 
        print(f"HRTF Sample Rate Detected/Assumed: {self.hrtf_fs} Hz")

    def __del__(self):
        if hasattr(self, 'sofa_file') and self.sofa_file:
            self.sofa_file.close()

    def cartesian_to_spherical(self, x, y, z):
        """Converts Cartesian coordinates (x,y,z) to spherical (Azimuth, Elevation, Distance)."""
        r = np.sqrt(x**2 + y**2 + z**2)
        azimuth = np.degrees(np.arctan2(x, -z))
        elevation = np.degrees(np.arcsin(y / r)) if r != 0 else 0.0
        return azimuth, elevation, r

    def get_hrtf(self, az, el):
        """Finds the closest HRIR pair (L/R) for a given Azimuth and Elevation."""
        idx = np.argmin((self.positions[:, 0] - az)**2 + (self.positions[:, 1] - el)**2)
        hrir_l = self.sofa_file.getDataIR()[idx, 0, :]
        hrir_r = self.sofa_file.getDataIR()[idx, 1, :]
        return hrir_l, hrir_r

    def spatialize(self, signal, az, el, distance):
        """Applies binaural spatialization to a MONO signal."""
        hrir_l, hrir_r = self.get_hrtf(az, el)
        
        distance = max(distance, 0.1)
        gain_db = -20 * math.log10(distance)
        gain_lin = 10**(gain_db / 20)

        left_ear_signal = fftconvolve(signal, hrir_l) * gain_lin
        right_ear_signal = fftconvolve(signal, hrir_r) * gain_lin

        return np.stack([left_ear_signal, right_ear_signal], axis=1)

    def compute_rms(self, audio_data):
        """Computes the RMS gain of the audio data."""
        rms = np.sqrt(np.mean(audio_data ** 2)) if len(audio_data) > 0 else 0.0
        return rms

    def process_stem(self, stem_name, mono_signal, avg_rms, positions_set, final_mix, fs_global):
        """Helper function to spatialize a single position/gain configuration and its mirror."""

        current_threshold = {
            "vocals": VOCALS_GAIN_THRESHOLD,
            "drums": DRUMS_GAIN_THRESHOLD,
            "bass": BASS_GAIN_THRESHOLD,
            "piano": PIANO_GAIN_THRESHOLD,
            "other": OTHER_GAIN_THRESHOLD
        }.get(stem_name, 0.1)

        pos_data = positions_set[stem_name] if avg_rms > current_threshold else positions_low[stem_name]
        
        x, y, z, base_gain = pos_data

        # --- Sub-Function to Handle Accumulation ---
        def accumulate_mix(current_mix, spatial_output):
            if current_mix is None:
                return spatial_output
            else:
                len_mix = len(current_mix)
                len_spatial = len(spatial_output)

                if len_spatial > len_mix:
                    padding = np.zeros((len_spatial - len_mix, 2))
                    current_mix = np.vstack([current_mix, padding])
                elif len_mix > len_spatial:
                    padding = np.zeros((len_mix - len_spatial, 2))
                    spatial_output = np.vstack([spatial_output, padding])

                return current_mix + spatial_output
        # -------------------------------------------

        # --- 1. Process Original Position ---
        az, el, dist = self.cartesian_to_spherical(x, y, z)
        
        spatial_output = self.spatialize(mono_signal, az, el, dist)
        spatial_output *= base_gain
        final_mix = accumulate_mix(final_mix, spatial_output)

        print(f"  > Original {stem_name}: Az={az:.1f}°, El={el:.1f}°, Dist={dist:.2f}m, BaseGain={base_gain}")

        # --- 2. Process Mirrored Position (if applicable) ---
        if stem_name in STEMS_TO_MIRROR:
            # Mirroring: Invert the x-coordinate
            mirrored_x = -x 
            
            az_mirror, el_mirror, dist_mirror = self.cartesian_to_spherical(mirrored_x, y, z)

            spatial_output_mirror = self.spatialize(mono_signal, az_mirror, el_mirror, dist_mirror)
            # Apply slight gain reduction for mirroring to maintain headroom
            spatial_output_mirror *= base_gain * 0.9 
            final_mix = accumulate_mix(final_mix, spatial_output_mirror)
            
            print(f"  > Mirrored {stem_name}: Az={az_mirror:.1f}°, El={el_mirror:.1f}°, Dist={dist_mirror:.2f}m, BaseGain={base_gain * 0.9:.2f}")

        return final_mix, fs_global


    def mapping(self, stem_paths):
        """Loads, positions, spatializes, and mixes the audio stems, including mirroring."""

        final_mix = None
        fs_global = self.hrtf_fs 

        print(f"Final output sample rate set to: {fs_global} Hz")

        for stem_path in stem_paths:
            stem_name = os.path.basename(stem_path).split('.')[0]
            if stem_name not in positions_low:
                continue

            try:
                sig_data, fs_data = lb.load(stem_path, sr=TARGET_FS, mono=False)
            except Exception as e:
                print(f"Could not load {stem_path}. Skipping. Error: {e}")
                continue

            mono_signal = np.mean(sig_data, axis=0) if sig_data.ndim > 1 else sig_data
            
            # **Resample to Match HRTF Sample Rate**
            if TARGET_FS != self.hrtf_fs:
                mono_signal = lb.resample(mono_signal, orig_sr=TARGET_FS, target_sr=self.hrtf_fs)

            avg_rms = self.compute_rms(mono_signal)
            
            # --- Call the process_stem function ---
            final_mix, fs_global = self.process_stem(stem_name, mono_signal, avg_rms, positions_high, final_mix, fs_global)

        # 6. Final Normalization and Output
        if final_mix is not None:
            peak = np.max(np.abs(final_mix))
            if peak > 0:
                final_mix = final_mix / peak * 0.95
            
            sf.write(OUTPUT_PATH, final_mix, fs_global, subtype='PCM_16')
            print(f"✅ immersive_mix_pro_louder_stems.wav created successfully at {OUTPUT_PATH}! (Wider Binaural Stereo)")
        else:
            print("❌ Error: No audio stems were processed.")

if __name__ == "__main__":
    try:
        stem_files = [vocals, drums, bass, piano, other]

        xp = ImmersiveAudio(SOFA_FILE_PATH)

        xp.mapping(stem_files)

    except FileNotFoundError as e:
        print(f"File Not Found Error: Please check your audio and SOFA file paths. {e}")
    except Exception as e:
        print(f"An error occurred: {e}")