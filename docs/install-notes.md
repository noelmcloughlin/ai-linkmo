# Install notes: compilers, CUDA, corporate indexes

The README's [Install](../README.md#install) step (`uv sync --extra test`) is enough on most machines. These notes cover the cases where it is not.

## Red Hat hosts with an older gcc

Some of the compiled dependencies need gcc 12 or later. On RHEL-family hosts:

```bash
sudo yum install gcc-toolset-12 gcc-toolset-14 ninja-build -y   # once, if gcc < 12
scl enable gcc-toolset-12 bash
```

## Builds behind a corporate package index, or with CUDA

```bash
# export UV_DEFAULT_INDEX=https://proxy.example.com/repository/pypi-all/simple
uv cache clean
MAX_JOBS=4 UV_HTTP_TIMEOUT=60s TORCH_CUDA_ARCH_LIST="8.6" uv sync --extra test   # be patient
```

`MAX_JOBS` bounds parallel compilation; `TORCH_CUDA_ARCH_LIST` should match your GPU. Neither is needed for a CPU-only install from the public index.

## Regenerating the web UI's schema

The web UI ships a JSON Schema derived from the ontology. If the `ai-atlas-nexus` package has been upgraded (or you are unsure), rebuild it. The path below is version-agnostic:

```bash
SCHEMA="$(uv run python -c 'import ai_atlas_nexus, pathlib; print(pathlib.Path(ai_atlas_nexus.__file__).parent / "ai_risk_ontology" / "schema" / "ai-risk-ontology.yaml")')"
uv run gen-json-schema --stacktrace --preserve-names --mergeimports "$SCHEMA" > lib/frontend/static/schema/ai-risk-ontology.json
```

## The two logos

`lib/frontend/static/mylogo.png` is what the web UI serves. `byo/images/mylogo.png` is the example logo for a bring-your-own-data identity. They are separate files on purpose; replace the first to rebrand the UI.
