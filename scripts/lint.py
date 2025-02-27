import subprocess


def run_linters():
    """Run all linters"""
    exclude_patterns = [
        r"/?venv/",
        r"/?\.venv/",
        r"/?migrations/",
        r"/?build/",
        r"/?dist/",
        r"/?tests/",
        r".*\.pyc$",
        r"/?tools/",
        r"__pycache__",
    ]

    print("Running Black...")
    exclude_regex = "|".join(exclude_patterns)
    subprocess.run(["black", ".", f"--extend-exclude={exclude_regex}"], check=True)

    print("\nRunning mypy...")
    subprocess.run(["mypy", "."], check=True)


if __name__ == "__main__":
    run_linters()
