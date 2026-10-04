FROM python:3.12-slim-trixie@sha256:02108f5d322dd89f1c9e552442c25acb0543dfdbc455693a5599624f20d9155d
RUN python -m pip install --no-cache-dir --only-binary=:all: pillow==11.3.0 numpy==1.26.4
ENTRYPOINT ["python", "/codec/compact_evidence.py"]
