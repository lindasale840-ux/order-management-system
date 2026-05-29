import subprocess
import os


# =========================
# CURRENT PROJECT DIRECTORY
# =========================

base_dir = os.getcwd()

# =========================
# MAIN FILE
# =========================

main_file = os.path.join(
    base_dir,
    "main.py"
)

# =========================
# RUN STREAMLIT
# =========================

subprocess.Popen(

    [
        "python",
        "-m",
        "streamlit",
        "run",
        main_file
    ],

    cwd=base_dir
)