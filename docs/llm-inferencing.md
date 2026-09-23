# LLM inferencing and ARES evaluation

Both of these need infrastructure you run yourself. Neither is required for the CLI, the API, the web UI, or the graph export.

## LLM inferencing

AI-LinkMO can use a large language model to infer risk dimensions. You need access to a model (for example `ibm-granite/granite-3.1-8b-instruct`) served by an inference engine such as [vLLM](https://docs.vllm.ai/). On a host with the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#with-dnf-rhel-centos-fedora-amazon-linux), the official [vLLM container](https://docs.vllm.ai/en/stable/deployment/docker/) is the simplest route:

```bash
# example only - adjust the model, the GPU flags, and the mounts to your host
podman pull docker.io/vllm/vllm-openai

VLLM_API_KEY="${VLLM_API_KEY:-replace-with-your-key}"
VLLM_HOST_IP="${VLLM_HOST_IP:-127.0.0.1}"
VLLM_API_URL="${VLLM_HOST_IP}/v1"
UV_TORCH_BACKEND=auto

podman run --device nvidia.com/gpu=all \
  -v ~/.cache/modelscope/hub/models:/root/.cache/modelscope/hub/models \
  -e REQUESTS_CA_BUNDLE=/cert.pem --mount type=bind,source=/etc/pki/tls/cert.pem,target=/cert.pem \
  --env "VLLM_USE_MODELSCOPE=True" --env "TRANSFORMERS_OFFLINE=1" --env "TORCH_CUDA_ARCH_LIST=8.6" \
  --env "PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.6,max_split_size_mb:64,expandable_segments:True" \
  -p 8000:8000 --ipc=host \
  docker.io/vllm/vllm-openai --model facebook/opt-125m --gpu_memory_utilization="0.8"
```

The container above also listens on port 8000, which is the FastAPI backend's port; run one of them elsewhere.

## ARES evaluation

ARES is an evaluation framework for Retrieval-Augmented Generation (RAG) systems. An [extension for ai-atlas-nexus](https://github.com/ibm/ai-atlas-nexus-extensions/tree/main/ran-ares-integration) exists, but it cannot be installed here until an upstream pull request merges.
