import os
from pathlib import Path

import nox


@nox.session(python="3.9", reuse_venv=True)
def run_min_version_test(session):
    # explicit venv to avoid overwriting local venv if exists
    py_str = "test-venv"
    session.run(
        "uv",
        "sync",
        env={"UV_PROJECT_ENVIRONMENT": py_str, "VIRTUAL_ENV": py_str},
    )
    session.run(
        "uv",
        "run",
        "pytest",
        "tests_basic/core",
        env={"UV_PROJECT_ENVIRONMENT": py_str, "VIRTUAL_ENV": py_str},
    )


@nox.session(python="3.11", reuse_venv=True, venv_backend="uv|virtualenv")
def run_tests(session):
    """Run the tests. Doing it via nox will create an isolated venv."""
    session.install(".[developer]")
    session.run("pytest")


@nox.session(reuse_venv=True, venv_backend="uv|virtualenv")
def serve_docs(session):
    session.install(".[docs]")
    session.run(
        "sphinx-autobuild",
        "docs/source",
        "docs/build",
        "--port",
        "8777",
        "--open-browser",
    )


@nox.session(reuse_venv=True, venv_backend="uv|virtualenv")
def build_docs(session):
    """Build the docs; used in CI pipelines to test the build. Will always rebuild and will always fail if there are any warnings"""
    session.install(".[docs]")
    session.run(
        "sphinx-build",
        "docs/source",
        "docs/build",
        "-W",
        "--keep-going",
        "-a",
        "-E",
        "-b",
        "html",
        "-q",
    )


@nox.session(reuse_venv=True, venv_backend="uv")
def build_wheel(session):
    """Build the wheel and sdist"""
    session.install(".[developer]")
    session.run("uv", "build")


@nox.session(python=False)
def update_dev_kraken(session):
    """Run the Kraken build to update it with new pylinac changes"""
    if Path("GCP_creds.json").exists():
        os.environ["GCP_BUILD_CREDS"] = Path("gcp_build_creds.json").open().read()
    key_info = os.environ["GCP_BUILD_CREDS"]
    with open("service_key.json", "w") as key_file:
        key_file.write(key_info)
    session.run(
        "gcloud", "auth", "activate-service-account", "--key-file", "service_key.json"
    )
    session.run("gcloud", "config", "set", "project", "radmachine")
    session.run("gcloud", "builds", "triggers", "run", "Kraken", "--branch=master")
