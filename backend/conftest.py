"""
Root-level pytest conftest.

Applies a compatibility shim for datasets==5.1.0 + pyarrow>=26.
In pyarrow 26, ParquetFragmentScanOptions was removed from pyarrow.dataset,
but datasets 5.1.0's arrow_dataset.py still references it at class-definition
time (not at call time), causing an AttributeError on import.

This shim adds a placeholder attribute before datasets is first imported,
so the class body parses without error. The attribute is used only as a type
annotation default, so the stub value is never called at runtime.
"""
import types
import sys


def _patch_pyarrow_dataset() -> None:
    try:
        import pyarrow.dataset as _pds  # noqa: F401
        if not hasattr(_pds, "ParquetFragmentScanOptions"):
            # Add a stub class so the datasets type annotation doesn't crash.
            _pds.ParquetFragmentScanOptions = type(  # type: ignore[attr-defined]
                "ParquetFragmentScanOptions", (), {}
            )
    except ImportError:
        pass


_patch_pyarrow_dataset()

