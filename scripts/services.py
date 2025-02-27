import subprocess


def start_services():
    """Start Docker services"""
    subprocess.run(["docker-compose", "up", "-d"], check=True)


def stop_services():
    """Stop Docker services"""
    subprocess.run(["docker-compose", "down"], check=True)


if __name__ == "__main__":
    start_services()
