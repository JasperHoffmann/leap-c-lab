# syntax=docker/dockerfile:1
# CI image with leap-c-lab third-party deps pre-installed in 3 venvs.
#
# Does NOT install leap-c, leap-c-lab, or mpc-sac — those are installed
# from exact git refs at runtime so CI tests the right code.
#
# mpc-sac uses this as a warm base and installs its own extra dependencies
# during CI. This avoids maintaining a duplicated dependency union here.
FROM ghcr.io/leap-c/acados-ci:ubuntu24.04

COPY pyproject.toml README.md /tmp/leap-c-lab/
COPY leapc_lab /tmp/leap-c-lab/leapc_lab

# Bake all deps into /opt/venvs/{3.11,3.12,3.13}.
RUN for py in 3.11 3.12 3.13; do \
      uv venv --python $py /opt/venvs/$py && \
      VIRTUAL_ENV=/opt/venvs/$py uv pip install /opt/acados/interfaces/acados_template && \
      VIRTUAL_ENV=/opt/venvs/$py uv pip install \
        "git+https://github.com/leap-c/leap-c.git@main" && \
      VIRTUAL_ENV=/opt/venvs/$py uv pip install -e "/tmp/leap-c-lab[dev]" && \
      VIRTUAL_ENV=/opt/venvs/$py uv pip uninstall -y leap-c leap-c-lab \
      && rm -rf /root/.cache/uv; \
    done

WORKDIR /workspace
CMD ["bash"]
