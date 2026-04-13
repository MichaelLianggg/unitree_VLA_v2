# Deploy & train

## 1. Run the deploy script

From the **repository root** (parent of `unitree_lerobot/`; the deploy script sits next to `README.md`):

```bash
chmod +x deploy_unitree_lerobot_env.sh
./deploy_unitree_lerobot_env.sh
conda activate unitree_lerobot
```

If your shell is already under `unitree_lerobot/scripts/`, run:

```bash
chmod +x ../../deploy_unitree_lerobot_env.sh
../../deploy_unitree_lerobot_env.sh
```


## 2. Train (single GPU)

```bash
cd unitree_lerobot/lerobot/src/lerobot/scripts
python lerobot_train.py \
  --dataset.repo_id=<your_dataset> \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --output_dir=./outputs/run1
```

## 3. Train on multi-GPU

LeRobot uses **Hugging Face Accelerate**. Effective batch size = **`batch_size` × number of processes** (one process per GPU).

**Launch:**

```bash
cd unitree_lerobot/lerobot/src/lerobot/scripts

accelerate launch \
  --multi_gpu \
  --num_processes=8 \
  --mixed_precision=bf16 \
  lerobot_train.py \
  --dataset.repo_id=unitreerobotics/G1_Dex1_PickPlaceRedBlock_Dataset_Sim \
  --policy.type=pi05 \
  --policy.pretrained_path=lerobot/pi05_base \
  --policy.dtype=bfloat16 \
  --policy.device=cuda \
  --policy.use_amp=false \
  --output_dir=./outputs/pi05_test1 \
  --batch_size=64 \
  --num_workers=8 \
  --steps=100000
```


