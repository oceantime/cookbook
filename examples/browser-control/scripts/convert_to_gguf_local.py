"""
本地 GGUF 转换脚本（使用本地安装的 llama.cpp）

前置条件:
    - 已克隆并构建 llama.cpp（默认路径: ./llama.cpp/）
    - 安装了 transformers 和 torch

用法:
    python scripts/convert_to_gguf_local.py \
        --model-path checkpoints/<experiment-name> \
        --output-path gguf_models_local/ \
        --quantization Q4_K_M \
        --llama-cpp-path ./llama.cpp
"""

import argparse
import subprocess
import sys
from pathlib import Path


def convert_to_gguf(
    model_path: str,
    output_path: str,
    quantization: str = "Q4_K_M",
    llama_cpp_path: str = "./llama.cpp",
) -> Path:
    """
    Convert a HuggingFace model checkpoint to GGUF format using local llama.cpp.

    Args:
        model_path: Path to the HuggingFace model checkpoint directory
        output_path: Directory to save the GGUF file
        quantization: Quantization type (Q4_K_M, Q8_0, Q4_0, Q2_K, etc.)
        llama_cpp_path: Path to the llama.cpp installation

    Returns:
        Path to the output GGUF file
    """
    model_path = Path(model_path).resolve()
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    llama_cpp = Path(llama_cpp_path).resolve()

    if not model_path.exists():
        print(f"Error: model path not found: {model_path}")
        sys.exit(1)

    if not llama_cpp.exists():
        print(f"Error: llama.cpp not found at {llama_cpp}")
        print("Clone and build llama.cpp first:")
        print("  git clone https://github.com/ggerganov/llama.cpp")
        print("  cd llama.cpp && make -j4")
        sys.exit(1)

    model_name = model_path.name

    # Step 1: Convert to GGUF f16
    f16_path = output_dir / f"{model_name}-f16.gguf"
    convert_script = llama_cpp / "convert_hf_to_gguf.py"

    print(f"Step 1: Converting {model_path} to GGUF f16...")
    subprocess.run(
        [
            sys.executable,
            str(convert_script),
            str(model_path),
            "--outfile",
            str(f16_path),
            "--outtype",
            "f16",
        ],
        check=True,
    )
    print(f"  → {f16_path}")

    # Step 2: Quantize
    quantize_bin = llama_cpp / "build" / "bin" / "llama-quantize"
    if not quantize_bin.exists():
        # Try alternative path (non-cmake build)
        quantize_bin = llama_cpp / "llama-quantize"

    output_file = output_dir / f"{model_name}-{quantization.lower()}.gguf"

    print(f"Step 2: Quantizing to {quantization}...")
    subprocess.run(
        [str(quantize_bin), str(f16_path), str(output_file), quantization],
        check=True,
    )

    # Clean up intermediate f16 file
    f16_path.unlink()
    print(f"  → {output_file} (intermediate f16 removed)")

    print(f"\nDone! GGUF model saved to: {output_file}")
    print(f"File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Convert HuggingFace model to GGUF format using local llama.cpp"
    )
    parser.add_argument(
        "--model-path",
        required=True,
        help="Path to the HuggingFace model checkpoint directory",
    )
    parser.add_argument(
        "--output-path",
        default="gguf_models_local",
        help="Directory to save the GGUF file (default: gguf_models_local/)",
    )
    parser.add_argument(
        "--quantization",
        default="Q4_K_M",
        choices=["Q2_K", "Q4_0", "Q4_K_M", "Q5_K_M", "Q8_0", "F16"],
        help="Quantization type (default: Q4_K_M)",
    )
    parser.add_argument(
        "--llama-cpp-path",
        default="./llama.cpp",
        help="Path to llama.cpp directory (default: ./llama.cpp)",
    )
    args = parser.parse_args()

    convert_to_gguf(
        model_path=args.model_path,
        output_path=args.output_path,
        quantization=args.quantization,
        llama_cpp_path=args.llama_cpp_path,
    )


if __name__ == "__main__":
    main()
