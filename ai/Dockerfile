FROM python:3.13-slim
WORKDIR /workspace
COPY ai/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend/app/services/prompt_builder.py backend/app/services/prompt_builder.py
COPY db/benchmark_pack.json db/benchmark_pack.json
COPY ai ai
ENV PYTHONPATH=/workspace/backend HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false
ENTRYPOINT ["python", "ai/pipeline.py"]
