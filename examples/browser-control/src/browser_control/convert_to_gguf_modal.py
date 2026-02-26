"""
Modal 云端 GGUF 转换脚本
将微调后的模型从 HuggingFace Safetensors 格式转换为 GGUF 格式

用法:
    uv run modal run -m src.browser_control.convert_to_gguf_modal
"""

import modal
from pathlib import Path

from .modal_infra import get_modal_app, get_volume

app = get_modal_app("browser-control-gguf-convert")

# Volume where checkpoints are stored
checkpoints_volume = get_volume("browser-control-fine-tune-with-grpo")
gguf_output_volume = get_volume("browser-control-gguf-models")

convert_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "build-essential", "cmake")
    .run_commands(
        "git clone https://github.com/ggerganov/llama.cpp /llama.cpp",
        "cd /llama.cpp && cmake -B build && cmake --build build --config Release -j4",
    )
    .pip_install("transformers", "torch", "huggingface_hub")
)


@app.function(
    image=convert_image,
    gpu="A10G",
    timeout=1800,
    volumes={
        "/checkpoints": checkpoints_volume,
        "/gguf_output": gguf_output_volume,
    },
)
def convert_to_gguf(checkpoint_name: str, quantization: str = "Q4_K_M") -> str:
    """
    Convert a HuggingFace checkpoint to GGUF format.

    Args:
        checkpoint_name: Name of the checkpoint directory in /checkpoints/
        quantization: GGUF quantization type (Q4_K_M, Q8_0, Q4_0, etc.)

    Returns:
        Path to the output GGUF file
    """
    import subprocess

    checkpoint_path = Path("/checkpoints") / checkpoint_name
    output_dir = Path("/gguf_output")
    output_dir.mkdir(exist_ok=True)

    # Step 1: Convert to GGUF (f16 first)
    f16_path = output_dir / f"{checkpoint_name}-f16.gguf"
    print(f"Converting {checkpoint_path} to GGUF f16...")
    subprocess.run(
        [
            "python3",
            "/llama.cpp/convert_hf_to_gguf.py",
            str(checkpoint_path),
            "--outfile",
            str(f16_path),
            "--outtype",
            "f16",
        ],
        check=True,
    )

    # Step 2: Quantize
    output_path = output_dir / f"{checkpoint_name}-{quantization.lower()}.gguf"
    print(f"Quantizing to {quantization}...")
    subprocess.run(
        [
            "/llama.cpp/build/bin/llama-quantize",
            str(f16_path),
            str(output_path),
            quantization,
        ],
        check=True,
    )

    # Clean up f16 intermediate file
    f16_path.unlink()

    print(f"GGUF model saved to: {output_path}")
    gguf_output_volume.commit()
    return str(output_path)


@app.local_entrypoint()
def main(
    checkpoint_name: str = "LFM2-350M-browsergym-latest",
    quantization: str = "Q4_K_M",
):
    result = convert_to_gguf.remote(
        checkpoint_name=checkpoint_name,
        quantization=quantization,
    )
    print(f"Conversion complete: {result}")
