"""Intel/OpenMP optimisation bootstrap.

MUST be imported before any other package (torch, faiss, onnxruntime)
so that all env-vars are set before OpenMP runtimes initialise.
"""

import os

# ── OpenMP conflict suppression ───────────────────────────────────────────────
# faiss-cpu links LLVM OpenMP (libomp140); PyTorch links Intel OpenMP (libiomp5).
# On Windows both end up in the same process — this suppresses the fatal crash.
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ── Thread / parallelism tuning ───────────────────────────────────────────────
os.environ["OMP_NUM_THREADS"] = "12"
os.environ["MKL_NUM_THREADS"] = "12"
os.environ["KMP_BLOCKTIME"] = "1"
os.environ["KMP_AFFINITY"] = "granularity=fine,compact,1,0"
os.environ["MALLOC_TRIM_THRESHOLD_"] = "100000"
os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# ── Torch tuning (import AFTER env-vars) ──────────────────────────────────────
import torch  # noqa: E402

torch.set_num_threads(12)
torch.set_num_interop_threads(4)
torch.set_grad_enabled(False)

try:
    torch.backends.mkl.enabled = True
except Exception:
    pass
try:
    torch.backends.mkldnn.enabled = True
except Exception:
    pass


