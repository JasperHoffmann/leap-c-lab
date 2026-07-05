# syntax=docker/dockerfile:1
# CI image with leap-c-lab third-party deps pre-installed for one Python version.
#
# Does NOT install leap-c, leap-c-lab, or mpc-sac — those are installed
# from exact git refs at runtime so CI tests the right code.
#
# mpc-sac uses this as a warm base and installs its own extra dependencies
# during CI. This avoids maintaining a duplicated dependency union here.
FROM ghcr.io/leap-c/acados-ci:ubuntu24.04

ARG PYTHON_VERSION=3.12

COPY pyproject.toml README.md /tmp/leap-c-lab/
COPY leapc_lab /tmp/leap-c-lab/leapc_lab

# Bake deps into /opt/venv. The image tag encodes the Python version.
RUN uv venv --python ${PYTHON_VERSION} /opt/venv && \
    VIRTUAL_ENV=/opt/venv uv pip install /opt/acados/interfaces/acados_template && \
    VIRTUAL_ENV=/opt/venv uv pip install \
      "git+https://github.com/leap-c/leap-c.git@main" && \
    VIRTUAL_ENV=/opt/venv uv pip install -e "/tmp/leap-c-lab[dev]" && \
    VIRTUAL_ENV=/opt/venv uv pip uninstall -y leap-c leap-c-lab && \
    rm -rf /root/.cache/uv

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace
CMD ["bash"]
