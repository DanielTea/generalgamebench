FROM python:3.12-slim
WORKDIR /agent
COPY examples/agent.py /agent/agent.py
USER 65534:65534
ENTRYPOINT ["python", "-u", "/agent/agent.py"]
