# syntax=docker/dockerfile:1
# ==============================================================
# leap-c-lab notebook Dockerfile
#
# Thin layer on top of the leap-c notebook image.
# Adds leap-c-lab (example environments and planners) and
# example notebooks (cartpole demo, etc.).
#
# Build:
#   docker build -t leap-c-lab:notebook .
#   docker run -it --rm -p 7860:7860 leap-c-lab:notebook
#
# Multi-arch: linux/amd64 + linux/arm64 (inherited from base).
# ==============================================================

FROM ghcr.io/leap-c/leap-c:notebook

# leap-c + torch + marimo + acados already installed.
# Add leap-c-lab on top, keeping the venv owned by the non-root user.
COPY --chown=leap:leap pyproject.toml /home/leap/leap-c-lab/pyproject.toml
COPY --chown=leap:leap README.md /home/leap/leap-c-lab/README.md
COPY --chown=leap:leap leapc_lab /home/leap/leap-c-lab/leapc_lab
WORKDIR /home/leap/leap-c-lab

RUN uv pip install -e ".[dev]"

# Copy example notebooks
COPY --chown=leap:leap notebooks /home/leap/leap-c-lab/notebooks

WORKDIR /home/leap/leap-c-lab/notebooks

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["marimo", "edit", "--host", "0.0.0.0", "-p", "7860", "--no-token"]
