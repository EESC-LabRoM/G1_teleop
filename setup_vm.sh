#!/usr/bin/env bash
# Setup para G1 subir escada (Safe100Humanoid + stair_RL, ambos mjlab). Rodar na VM com GPU NVIDIA.
# Uso: bash setup_vm.sh [smoke|eval|train]
set -euo pipefail

WORK="${WORK:-$HOME/g1_stairs}"
mkdir -p "$WORK" && cd "$WORK"

nvidia-smi || { echo "Sem GPU NVIDIA/driver (precisa CUDA 12.8)"; exit 1; }

# ---- ambiente conda (Python 3.11) ----
if ! command -v conda >/dev/null; then
  curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o mc.sh
  bash mc.sh -b -p "$HOME/miniconda3" && rm mc.sh
  export PATH="$HOME/miniconda3/bin:$PATH"
fi
eval "$(conda shell.bash hook)"
conda env list | grep -q g1stairs || conda create -y -n g1stairs python=3.11
conda activate g1stairs

# ---- repos ----
[ -d Safe100Humanoid ] || git clone https://github.com/lzqw/Safe100Humanoid
[ -d stair_RL ]        || git clone https://github.com/Kepitition/stair_RL
[ -d unitree_mujoco ]  || git clone https://github.com/unitreerobotics/unitree_mujoco

# ---- deps (versoes do README do Safe100Humanoid) ----
cd Safe100Humanoid
python -m pip install -r requirements-lock.txt || {
  python -m pip install "torch==2.7.0" --index-url https://download.pytorch.org/whl/cu128
  python -m pip install "rsl-rl-lib==5.0.1"
}
python -m pip install -e .

case "${1:-smoke}" in
  smoke)  # 4 envs, so para ver se roda
    python scripts/train.py Unitree-G1-Stairs-CBF --env.scene.num-envs 4 --agent.max-iterations 2 ;;
  eval)   # checkpoint pre-treinado, escada 13 cm
    python experiments/scripts/evaluate_stairs.py \
      --checkpoint results/models/cbf/model_1500.pt \
      --fixed-step-height 0.13 --num-episodes 128 --seed 42 ;;
  train)
    python scripts/train.py Unitree-G1-Stairs-CBF \
      --env.scene.num-envs 1024 --agent.max-iterations 1500 \
      --agent.seed 42 --agent.logger tensorboard ;;
esac
