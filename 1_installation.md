---
title: "WSL 2 + VS Code + Miniforge (conda-forge) Setup"

---



# Overview
This is a concise, general guide to install pylidar either on your windows or linux machine. Steps 1-3 are only required for the windows setup and show how to setup a Python development environment on Windows using **WSL 2**, **VS Code**, and **Miniforge**. Steps 4-10 cover cloning the repository, creating a conda environment from `environment.yml`, and (optionally) installing **RIEGL** libraries for projects that need them. 

> **Works best with:** Windows 10/11 (with WSL 2), Ubuntu on WSL, VS Code, and the official Microsoft **WSL**, **Python**, and **Jupyter** extensions.

# Step 1: Install WSL 2 (Ubuntu)

Open **PowerShell** as Administrator and run:

```powershell
wsl --install -d Ubuntu
```

Restart if prompted. Launch **Ubuntu** from the Start menu to create your Linux user.

> **Tip:** Check versions anytime: `wsl --status`

# Step 2: Install VS Code + extensions (Windows)

1. Install **Visual Studio Code** on Windows.  
2. In VS Code (Windows), install these extensions:
   - **WSL** (`ms-vscode-remote.remote-wsl`)
   - **Python** (`ms-python.python`)
   - **Jupyter** (`ms-toolsai.jupyter`)

When you later open a project inside WSL (using `code .`), VS Code will connect to your Linux environment and prompt to install these extensions there as well—accept that.

# Step 3: Install Miniforge (you can use conda if you prefer)


In your **linux (WSL or linux machine)** terminal:

```bash
# Update and basic tools
sudo apt-get update
sudo apt-get install -y wget git ca-certificates

# Download Miniforge (adjust architecture if needed)
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O /tmp/miniforge.sh

# Install Miniforge
bash /tmp/miniforge.sh -b -p "$HOME/miniforge3"

# Initialise shell
"$HOME/miniforge3/bin/conda" init bash

# Reload shell to pick up conda
exec bash
```

Verify:

```bash
conda --version
```

# Step 4: Create a workspace

**Recommended:** keep code under your Linux home (fast I/O), not under `/mnt/c`.

```bash
mkdir -p "$HOME/projects"
cd "$HOME/projects"
```

# Step 5: Install Git (if not already) and clone your repo

```bash
sudo apt-get install -y git

# Example: clone a repository
cd "$HOME/projects"
git clone https://github.com/armstonj/pylidar-tls-canopy.git
cd pylidar-tls-canopy
```

If your project includes an `environment.yml` you wish to edit on Windows, you may copy it out and back later via `/mnt/c/...` paths. However, editing directly in **VS Code connected to WSL** is usually simpler.

# Step 6: Organise RIEGL libraries (RDBLIB / RIVLIB)

If your project needs RIEGL libraries (when working with RIEGL data), place the RDBLIB and RIVLIB archives in a subfolder and extract them. They can be downloaded from the [RIEGL member area](http://www.riegl.com/members-area/software-downloads/libraries/). It is advisable to keep a copy within the project folder to ensure version traceability.

```bash
# Inside your project
mkdir -p riegl/libs
cd riegl

# Copy from Windows into WSL (adjust paths, usernames, and versions)
cp /mnt/c/Users/<YOUR_WINDOWS_USER>/Documents/6_software/riegl/linux/rdblib-<VERSION>-x86_64-linux.tar.gz .
cp /mnt/c/Users/<YOUR_WINDOWS_USER>/Documents/6_software/riegl/linux/rivlib-<VERSION>-x86_64-linux-gcc13.zip .

# Note: The trailing "." copies the file into the current directory.

# In case of linux, simply download and copy files to riegl/

# Tools for extraction
sudo apt-get install -y unzip

# Extract into libs/
tar -xf rdblib-<VERSION>-x86_64-linux.tar.gz -C libs/
unzip rivlib-<VERSION>-x86_64-linux-gcc13.zip -d libs/

cd ..   # back to project root

# Remember the paths
```

# Step 7: Setting up environment variables

To persist across shells, append the same lines to `~/.bashrc`:

```bash
cat << 'EOF' >> "$HOME/.bashrc"
export RIVLIB="$HOME/projects/<YOUR_PROJECT>/riegl/libs/rivlib-<VERSION>-x86_64-linux-gcc13"
export RDBLIB="$HOME/projects/<YOUR_PROJECT>/riegl/libs/rdblib-<VERSION>-x86_64-linux"
export PYLIDAR_CXX_FLAGS="-std=c++11"
EOF

# reload shell
source "$HOME/.bashrc"
```

Replace `<YOUR_PROJECT>` and `<VERSION>` accordingly.

## Update the environment.yml file

```
# Copy the absolute paths to the RIVLIB and RDBLIB folders to the environment.yml file. Below is an excerpt from the yml file. 

variables:
  RIVLIB_ROOT: /gpfs/data1/vclgp/software/rivlib-2_6_0-x86_64-linux-gcc9
  RDBLIB_ROOT: /gpfs/data1/vclgp/software/rdblib-2.4.0-x86_64-linux
  PYLIDAR_CXX_FLAGS: -std=c++11 

# Change to the following  

variables:
  RIVLIB_ROOT: $HOME/projects/<YOUR_PROJECT>/riegl/libs/rivlib-<VERSION>-x86_64-linux-gcc13
  RDBLIB_ROOT: $HOME/projects/<YOUR_PROJECT>/riegl/libs/rdblib-<VERSION>-x86_64-linux
  PYLIDAR_CXX_FLAGS: -std=c++11 

# Save the yml file   

```

# Step 8: Create and populate the conda environment

If you removed or edited `environment.yml`, make sure the final version is in the project root with the above changes. Then run:

```bash
# From the project root
conda env create -f environment.yml

# Activate it
conda activate <env-name>   # e.g., conda activate pylidar-tls-canopy
```

```bash
# Classic install
pip install .

# or, editable for development (PEP 660)
pip install -e .
```

> If you see editable-install errors, your project may need a modern `pyproject.toml` (PEP 660). Use `pip install .` as a fallback.

# Step 9: Open the project in VS Code (connected to WSL, if using WSL)

In case of WSL, navigate to the project folder in WSL terminal and launch VS Code. In case of linux, simply navigate to the project folder and launch VS Code

```bash
code .
```

VS Code (Windows) will open, attached to your WSL Ubuntu environment if using WSL. It will open normally in Linux. 

VSCode also has the SSH connection option to work remotely on a linux machine. The setup can be found [here](https://code.visualstudio.com/docs/remote/ssh). The principle is the same as WSL, where you connect to a remote environment installed in linux (dedicated linux machine or WSL partition) but edit and run code as if it were local.



# Step 10: Select the Python interpreter (the conda env inside WSL)

In VS Code (attached to WSL):

1. Press **Ctrl+Shift+P** → **Python: Select Interpreter**.  
2. Choose the interpreter, e.g.:

```
/home/<linux-user>/miniforge3/envs/<env-name>/bin/python
```

This ensures notebooks, terminals, and the debugger use the correct environment.

## Working with Windows files (only for WSL)

The Windows filesystem is available under `/mnt/c`, `/mnt/d`, etc. You can copy files between Windows and WSL, e.g.:

```bash
cp /mnt/c/Users/<YOUR_WINDOWS_USER>/Documents/somefile.txt .
```

> **Performance note:** Keep active source code, virtual environments, and build artefacts in the **Linux home** for best speed. Use `/mnt/c` mainly for sharing/backups.

## Troubleshooting

- **Conda not found after install:** Run `source ~/.bashrc` or restart the WSL shell.  
- **VS Code doesn’t attach to WSL:** Reinstall the **WSL** extension and reopen the folder via WSL terminal using `code .`.  
- **Interpreter mismatch:** Re-select the interpreter and ensure the environment is **activated** in the integrated terminal.  
- **RIEGL libs not found:** Double‑check `RIVLIB`/`RDBLIB` paths in environment.yml and ensure your process inherits the variables (restart VS Code if needed).

## Example: end‑to‑end (quick reference)

```bash
# WSL Ubuntu
sudo apt-get update
sudo apt-get install -y wget git unzip ca-certificates

# Miniforge
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O /tmp/miniforge.sh
bash /tmp/miniforge.sh -b -p "$HOME/miniforge3"
"$HOME/miniforge3/bin/conda" init bash
exec bash

# Workspace + clone
mkdir -p "$HOME/projects"
cd "$HOME/projects"
git clone https://github.com/armstonj/pylidar-tls-canopy.git
cd pylidar-tls-canopy

# (Optional) RIEGL libs as above...

# Environment
conda env create -f environment.yml
conda activate pylidar-tls-canopy
pip install -e .

# VS Code
code .
```
