## Installation

To run this project, you need to set up the required Python environment. An `visual_novel_env.yml` file is provided to recreate the Conda environment used for development.

### Steps to set up the environment

1. **Install Conda** (if you don’t have it yet)  
   - Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/).

2. **Open a terminal** and navigate to the project directory where `visual_novel_env.yml` is located (INSTALL/ folder).

3. **Create the Conda environment** from the `.yml` file:

conda env create -f visual_novel_env.yml

This will create a new environment with all the required dependencies.  
By default, the environment name is taken from the `name` field in `visual_novel_env.yml`.

4. **Activate the environment**:

conda activate visual_novel_env

> Replace `visual_novel_env` with the name defined in your `visual_novel_env.yml` if it’s different.

5. **Run the project**  
After activating the environment, you can execute your scripts as usual (in src/ folder):

python Tests.py
