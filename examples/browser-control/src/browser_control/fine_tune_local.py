"""
本地 GPU 微调脚本（无需 Modal，直接在本地 GPU 运行）
适用于 DGX / 本地 GPU 服务器，通过 Docker 环境运行

用法:
    python -m src.browser_control.fine_tune_local --config-file-name lfm2_350m_local.yaml
"""

import argparse
import os

from datasets import Dataset
from envs.browsergym_env import BrowserGymEnv, BrowserGymAction
from peft import LoraConfig
from transformers import AutoTokenizer
from trl import GRPOTrainer, GRPOConfig

from .config import FineTuningConfig
from .paths import get_path_model_checkpoints


def create_peft_config(config: FineTuningConfig):
    """Create LoRA PEFT config if LoRA is enabled, otherwise return None."""
    if not config.use_peft:
        return None

    return LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        bias=config.lora_bias,
        use_rslora=config.use_rslora,
        target_modules=config.lora_target_modules,
        task_type="CAUSAL_LM",
    )


def reward_completion(completions, **kwargs) -> list[float]:
    """
    Simple reward: reward completions that contain valid BrowserGym actions.
    """
    rewards = []
    valid_actions = ["click(", "fill(", "send_keys(", "scroll(", "noop()"]
    for completion in completions:
        text = completion if isinstance(completion, str) else str(completion)
        if any(action in text for action in valid_actions):
            rewards.append(1.0)
        else:
            rewards.append(0.0)
    return rewards


def rollout_func(
    prompts: list[str],
    trainer: GRPOTrainer,
    client: BrowserGymEnv,
    system_prompt: str,
    max_steps: int,
) -> dict[str, list]:
    """
    Execute rollouts locally (same as Modal version but without Modal overhead).
    """
    episode_prompt_ids: list[list[int]] = []
    episode_completion_ids: list[list[int]] = []
    episode_logprobs: list[list[float]] = []
    completion_rewards: list[float] = []

    for i, prompt_text in enumerate(prompts):
        print(f"[rollout] Processing prompt {i + 1}/{len(prompts)}")

        # Simple single-step rollout for local testing
        full_prompt = f"{system_prompt}\n\nTask: {prompt_text}\n\nAction:"
        tokenizer = trainer.processing_class

        inputs = tokenizer(full_prompt, return_tensors="pt")
        prompt_ids = inputs["input_ids"][0].tolist()

        # Generate one action
        outputs = trainer.model.generate(
            inputs["input_ids"].to(trainer.model.device),
            max_new_tokens=32,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id,
        )
        completion_ids = outputs[0][len(prompt_ids) :].tolist()
        completion_text = tokenizer.decode(completion_ids, skip_special_tokens=True)

        # Simple reward: valid action format
        valid_actions = ["click(", "fill(", "send_keys(", "scroll(", "noop()"]
        reward = 1.0 if any(a in completion_text for a in valid_actions) else 0.0

        episode_prompt_ids.append(prompt_ids)
        episode_completion_ids.append(completion_ids)
        episode_logprobs.append([0.0] * len(completion_ids))
        completion_rewards.append(reward)

    return {
        "prompt_ids": episode_prompt_ids,
        "completion_ids": episode_completion_ids,
        "logprobs": episode_logprobs,
        "rewards": completion_rewards,
    }


def fine_tune_local(config: FineTuningConfig) -> None:
    """
    Fine-tunes a Language Model locally using GRPO (no Modal required).
    """
    # Setup WandB or disable it
    if config.wandb_enabled:
        import wandb

        wandb.init(
            project=config.wandb_project_name,
            name=config.wandb_experiment_name,
            config=config.__dict__,
        )
    else:
        os.environ["WANDB_DISABLED"] = "true"

    print(f"Connecting to BrowserGym at {config.browsergym_url}")
    client = BrowserGymEnv(base_url=config.browsergym_url)

    dataset = Dataset.from_dict({"prompt": [config.default_goal] * config.dataset_size})

    output_dir = get_path_model_checkpoints(config.wandb_experiment_name)
    print(f"Checkpoints will be saved to: {output_dir}")

    grpo_config = GRPOConfig(
        max_steps=config.dataset_size,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        per_device_train_batch_size=config.per_device_train_batch_size,
        num_generations=config.num_generations,
        generation_batch_size=config.generation_batch_size,
        max_completion_length=config.max_completion_length,
        use_vllm=config.use_vllm,
        vllm_mode=config.vllm_mode,
        vllm_gpu_memory_utilization=config.vllm_gpu_memory_utilization,
        output_dir=output_dir,
        logging_steps=config.logging_steps,
        report_to="wandb" if config.wandb_enabled else "none",
        logging_dir="./logs",  # TensorBoard logs
    )

    peft_config = create_peft_config(config)
    if peft_config:
        print(f"LoRA enabled: r={config.lora_r}, alpha={config.lora_alpha}")

    trainer = GRPOTrainer(
        model=config.model_name,
        reward_funcs=[reward_completion],
        train_dataset=dataset,
        args=grpo_config,
        peft_config=peft_config,
        rollout_func=lambda prompts, trainer: rollout_func(
            prompts=prompts,
            trainer=trainer,
            client=client,
            system_prompt=config.system_prompt,
            max_steps=config.max_steps,
        ),
    )

    print("Starting GRPO training...")
    trainer.train()

    print(f"Saving model to {output_dir}")
    trainer.save_model(output_dir)
    print("Training complete!")


def main():
    parser = argparse.ArgumentParser(description="Local GPU fine-tuning with GRPO")
    parser.add_argument(
        "--config-file-name",
        type=str,
        required=True,
        help="Name of the YAML config file in configs/",
    )
    args = parser.parse_args()

    config = FineTuningConfig.from_yaml(file_name=args.config_file_name)
    fine_tune_local(config)


if __name__ == "__main__":
    main()
