"""Background task definitions for the core app."""

from django.tasks import task


@task()
def ping(message: str) -> str:
    """Trivial task to verify the background worker pipeline end to end."""
    output = f"pong: {message}"
    print(output)
    return output