<<<<<<< HEAD
import os

os.environ["PATH"] += os.pathsep + r"C:\Users\Admin\Downloads\ffmpeg-8.0-essentials_build\ffmpeg-8.0-essentials_build\bin"
from spleeter.separator import Separator
import shutil
import pkg_resources
import tensorflow as tf

import logging
logging.basicConfig(level=logging.DEBUG)


class split_components():
    try:
        spleeter_version = pkg_resources.get_distribution("spleeter").version
    except Exception:
        spleeter_version = "unknown"
    print(f"[INFO] Spleeter version: {spleeter_version}")
    print(f"[INFO] TensorFlow version: {tf.__version__}")

    # Remove Spleeter model cache to force re-download
    model_cache = os.path.expanduser(r"~/.cache/spleeter")
    if os.path.exists(model_cache):
        print(f"[INFO] Removing Spleeter model cache at {model_cache}")
        shutil.rmtree(model_cache)
    else:
        print(f"[INFO] No Spleeter model cache found at {model_cache}")

    print("[INFO] Starting Spleeter separation...")
    try:
        separator = Separator('spleeter:5stems')
        print("[INFO] Separator initialized. Beginning separation...")
        separator.separate_to_file(
            r'C:\Users\Admin\Desktop\chunchun atmos\01 Badtameez Dil (Yeh Jawaani Hai Deewani).mp3',
            'output'
        )
        print("[INFO] Separation complete. Check the output folder.")
    except Exception as e:
        print(f"[ERROR] Spleeter failed: {e}")
        
if __name__ == "__main__":
=======
import os

os.environ["PATH"] += os.pathsep + r"C:\Users\Admin\Downloads\ffmpeg-8.0-essentials_build\ffmpeg-8.0-essentials_build\bin"
from spleeter.separator import Separator
import shutil
import pkg_resources
import tensorflow as tf

import logging
logging.basicConfig(level=logging.DEBUG)


class split_components():
    try:
        spleeter_version = pkg_resources.get_distribution("spleeter").version
    except Exception:
        spleeter_version = "unknown"
    print(f"[INFO] Spleeter version: {spleeter_version}")
    print(f"[INFO] TensorFlow version: {tf.__version__}")

    # Remove Spleeter model cache to force re-download
    model_cache = os.path.expanduser(r"~/.cache/spleeter")
    if os.path.exists(model_cache):
        print(f"[INFO] Removing Spleeter model cache at {model_cache}")
        shutil.rmtree(model_cache)
    else:
        print(f"[INFO] No Spleeter model cache found at {model_cache}")

    print("[INFO] Starting Spleeter separation...")
    try:
        separator = Separator('spleeter:5stems')
        print("[INFO] Separator initialized. Beginning separation...")
        separator.separate_to_file(
            r'C:\Users\Admin\Desktop\chunchun atmos\01 Badtameez Dil (Yeh Jawaani Hai Deewani).mp3',
            'output'
        )
        print("[INFO] Separation complete. Check the output folder.")
    except Exception as e:
        print(f"[ERROR] Spleeter failed: {e}")
        
if __name__ == "__main__":
>>>>>>> 98008db (initial commit)
    split_components() 