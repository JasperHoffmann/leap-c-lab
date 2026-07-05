# syntax=docker/dockerfile:1
# CI image with all third-party deps pre-installed in 3 venvs.
#
# Does NOT install leap-c, leap-c-lab, or mpc-sac — those are installed
# from exact git refs at runtime so CI tests the right code.
#
# Used by both leap-c-lab and mpc-sac CI workflows.
FROM ghcr.io/leap-c/acados-ci:ubuntu24.04

# Bake all deps into /opt/venvs/{3.11,3.12,3.13}.
# Union of leap-c-lab + mpc-sac deps so both repos can use this image.
# acados_template is installed from the local /opt/acados checkout.
RUN for py in 3.11 3.12 3.13; do \
      uv venv --python $py /opt/venvs/$py && \
      VIRTUAL_ENV=/opt/venvs/$py uv pip install \
        /opt/acados/interfaces/acados_template \
        "torch>=2.0.0" \
        "numpy>=1.26.0" \
        "scipy==1.15.2" \
        casadi \
        "gymnasium==1.1.1" \
        matplotlib \
        moviepy \
        pygame \
        tensordict \
        "tensorboard==2.19.0" \
        "PyYAML==6.0.2" \
        "pytest==8.4.0" \
        "ruff==0.12.12" \
      && rm -rf /root/.cache/uv; \
    done

WORKDIR /workspace
CMD ["bash"]
