# 🎧 Music Immersion — HRTF-Based Spatial Audio

## 🪶 Overview
**Music Immersion** is a research-driven audio project that converts any stereo or multitrack song into an **immersive 3D listening experience** using **Head-Related Transfer Functions (HRTF)**.  
It simulates how humans perceive spatial sound through headphones — placing vocals, drums, and instruments around the listener’s head for a lifelike, concert-like experience.

---

## ✨ Features
- 🎚️ **Dynamic Spatialization** — 3D positioning of individual stems using HRTF convolution.  
- 🧠 **SOFA Support** — Load standardized or personalized HRTF datasets (`.sofa` format).  
- 🎵 **Multi-Stem Compatibility** — Works seamlessly with source-separated stems (e.g., Spleeter).  

- 🌀 **Gain-Adaptive Mapping** — Adjusts spatial intensity dynamically based on loudness or energy.  
- ⚙️ **Fully Software-Based** — No specialized DSP hardware required.  
- 🎧 **Binaural Output** — Produces immersive stereo `.wav` files playable on any headphones.  

---

## 🧩 System Architecture
        +------------------------+
        |   Input Audio (.wav)   |
        +-----------+------------+[immersive_mix_cropped.wav](https://github.com/user-attachments/files/23170486/immersive_mix_cropped.wav)

                    |
                    v
          +------------------+
          | Source Separation|
          |  (e.g., Spleeter)|
          +------------------+
                    |
                    v
          +------------------+
          |  Spatial Mapper  |
          | (Gain + Position)|
          +------------------+
                    |
                    v
          +------------------+
          |  HRTF Processor  |
          | (SOFA Convolver) |
          +------------------+
                    |
                    v
          +------------------+
          | Immersive Output |
          |  (.wav binaural) |
          +------------------+

---

## 🧠 How It Works
1. **Source Separation:**  
   Splits input audio into individual stems (vocals, drums, bass, etc.) using [Spleeter](https://github.com/deezer/spleeter).  
2. **Gain Mapping:**  
   Computes gain coefficients from RMS or spectral energy to control depth perception.  
3. **HRTF Convolution:**  
   Applies left/right HRTF impulse responses to each stem based on its 3D position.  
4. **Mixdown:**  
   Combines all spatialized stems into a final **binaural stereo** output file.

---

## ⚙️ Requirements
- Python **3.9+**
- Libraries:
  ```bash
  pip install numpy scipy soundfile librosa matplotlib pysofaconventions spleeter
## ╰(*°▽°*)╯  OUTPUT 

[immersive_mix_cropped.wav](https://github.com/user-attachments/files/23170513/immersive_mix_cropped.wav)
