# Bumping Dependencies

Python dependencies are specified in [pyproject.toml] following the
[PyPA standard](https://packaging.python.org/en/latest/specifications/declaring-project-metadata/)
and [setuptools](https://setuptools.pypa.io/en/latest/userguide/index.html)
build system. Use `pip install .` to install the project and its dependencies.
[PEP 440] should be followed when changing the dependency versions.

[pyproject.toml]: /pyproject.toml
[PEP 440]: https://peps.python.org/pep-0440/

The [Dockerfile] for this project uses [requirements.txt] to lock dependencies,
rather than installing the latest version of each requirement.
The requirements.txt file can be generated with the following steps:

1. `pip install pip-tools` into your project environment
2. Run `pip-compile --upgrade --generate-hashes --extra jishaku pyproject.toml`

A simpler requirements.txt file can also be created with
`pip install .[jishaku] && pip uninstall thestarboard && pip freeze > requirements.txt`.

[Dockerfile]: /Dockerfile
[requirements.txt]: /requirements.txt
