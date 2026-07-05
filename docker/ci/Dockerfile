# syntax=docker/dockerfile:1
# CI image with leap-c-lab third-party deps pre-installed in 3 venvs.
#
# Does NOT install leap-c, leap-c-lab, or mpc-sac — those are installed
# from exact git refs at runtime so CI tests the right code.
#
# mpc-sac uses this as a warm base and installs its own extra dependencies
# during CI. This avoids maintaining a duplicated dependency union here.
FROM ghcr.io/leap-c/acados-ci:ubuntu24.04

COPY pyproject.toml /tmp/leap-c-lab-pyproject.toml

# Generate requirements from pyproject.toml so dependency versions have a
# single source of truth. Exclude repos-under-test and acados-template, which
# is installed from the acados checkout baked into the base image.
RUN python3 - <<'PY'
import re
import tomllib

with open('/tmp/leap-c-lab-pyproject.toml', 'rb') as f:
    pyproject = tomllib.load(f)

project = pyproject['project']
deps = list(project.get('dependencies', []))
deps.extend(project.get('optional-dependencies', {}).get('dev', []))

excluded = {'leap-c', 'acados-template'}
with open('/tmp/leap-c-lab-requirements.txt', 'w') as f:
    for dep in deps:
        name = re.split(r'\s*(?:\[|==|!=|<=|>=|<|>|~=|;)', dep, maxsplit=1)[0].lower()
        if name not in excluded:
            f.write(dep + '\n')
PY

# Bake all deps into /opt/venvs/{3.11,3.12,3.13}.
RUN for py in 3.11 3.12 3.13; do \
      uv venv --python $py /opt/venvs/$py && \
      VIRTUAL_ENV=/opt/venvs/$py uv pip install \
        /opt/acados/interfaces/acados_template \
        -r /tmp/leap-c-lab-requirements.txt \
      && rm -rf /root/.cache/uv; \
    done

WORKDIR /workspace
CMD ["bash"]
