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
RUN pip install --no-index pip-deps/* \
    && rm -r pip-deps

FROM project-install-deps AS project

WORKDIR /thestarboard

RUN apk add --no-cache gettext

COPY --link MANIFEST.in pyproject.toml setup.py ./
COPY --link src/ src/
# --no-build-isolation to avoid re-installing setuptools in pyproject.toml
RUN pip install --no-build-isolation --no-index .

RUN apk del gettext

FROM project AS prod

# -u for PYTHONUNBUFFERED; prints won't be shown otherwise
ENTRYPOINT ["python", "-u", "-m", "thestarboard"]
