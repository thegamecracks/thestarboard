FROM python:3.11-alpine AS apt-deps

# Required for direct references to git repositories in requirements.txt
RUN apk add --no-cache git

FROM apt-deps AS project-download-deps

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache \
    pip download --dest pip-deps -r requirements.txt

FROM python:3.11-alpine AS project-install-deps

COPY --from=project-download-deps pip-deps/ pip-deps/
# --no-index to avoid network resolution; missing wheels should be errors
RUN pip install --no-index pip-deps/*

FROM project-install-deps AS project

WORKDIR /thestarboard

COPY --link MANIFEST.in pyproject.toml setup.py ./
COPY --link src/ src/
# --no-build-isolation to avoid re-installing setuptools in pyproject.toml
RUN pip install --no-build-isolation --no-index .

FROM project AS prod

ENTRYPOINT ["python", "-m", "thestarboard"]
