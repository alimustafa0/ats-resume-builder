"""Shared processing lifecycle.

A context manager wrapping any "processable" document -- one with a `status`
field, a matching `Status` choices enum, and an `error_message` field -- in the
standard PENDING -> PROCESSING -> COMPLETED / FAILED transitions. The body of
the `with` block does the real work and sets the result fields; this manager
owns only the status bookkeeping, so every document type behaves identically
and none is ever left stuck mid-process.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def processing_lifecycle(instance) -> Iterator[None]:
    """Run the wrapped body within the standard status lifecycle.

    Sets PROCESSING on entry, COMPLETED on clean exit, or FAILED with the error
    message saved on any exception -- which is then re-raised so the worker logs
    the traceback. `instance` must expose `status`, `error_message`, a `Status`
    enum, and `save()`.
    """
    instance.status = instance.Status.PROCESSING
    instance.error_message = ""
    instance.save(update_fields=["status", "error_message", "updated_at"])
    try:
        yield
        instance.status = instance.Status.COMPLETED
        instance.save()
    except Exception as exc:
        instance.status = instance.Status.FAILED
        instance.error_message = str(exc)
        instance.save(update_fields=["status", "error_message", "updated_at"])
        raise