"""Device detection utility for PyTorch-based models."""

import torch


def get_device() -> str:
    """
    Detect and return the appropriate device for PyTorch models.

    Returns:
        str: "cuda" if GPU is available, "cpu" otherwise
    """
    if torch.cuda.is_available():
        device = "cuda"
        gpu_name = torch.cuda.get_device_name(0)
        print(f"GPU detected: {gpu_name} - using CUDA")
    else:
        device = "cpu"
        print("No GPU detected - using CPU")
    return device
