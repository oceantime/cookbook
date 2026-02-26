"""
简化版 GGUF 转换脚本（最小依赖，快速使用）

用法:
    python scripts/convert_to_gguf_simple.py <model_path> [quantization]

示例:
    python scripts/convert_to_gguf_simple.py checkpoints/LFM2-350M-browsergym-20260226
    python scripts/convert_to_gguf_simple.py checkpoints/LFM2-350M-browsergym-20260226 Q8_0
"""

import subprocess
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    model_path = Path(sys.argv[1]).resolve()
    quantization = sys.argv[2] if len(sys.argv) > 2 else "Q4_K_M"
    llama_cpp = Path("./llama.cpp").resolve()
    output_dir = Path("gguf_models_local")
    output_dir.mkdir(exist_ok=True)

    if not model_path.exists():
        print(f"Error: {model_path} not found")
        sys.exit(1)

    if not llama_cpp.exists():
        print("Error: ./llama.cpp not found. Run:")
        print(
            "  git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp && make -j4"
        )
        sys.exit(1)

    name = model_path.name
    f16 = output_dir / f"{name}-f16.gguf"
    out = output_dir / f"{name}-{quantization.lower()}.gguf"

    print(f"Converting {model_path.name} → {quantization}...")

    subprocess.run(
        [
            sys.executable,
            str(llama_cpp / "convert_hf_to_gguf.py"),
            str(model_path),
            "--outfile",
            str(f16),
            "--outtype",
            "f16",
        ],
        check=True,
    )

    quantize = llama_cpp / "build" / "bin" / "llama-quantize"
    if not quantize.exists():
        quantize = llama_cpp / "llama-quantize"

    subprocess.run([str(quantize), str(f16), str(out), quantization], check=True)
    f16.unlink()

    size_mb = out.stat().st_size / 1024 / 1024
    print(f"Done: {out} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
