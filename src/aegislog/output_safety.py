"""Prevent derived output from replacing its input, including filesystem aliases."""
from pathlib import Path


def ensure_distinct_output(source, *outputs):
    original = Path(source)
    for output in map(Path, outputs):
        if original.resolve() == output.resolve() or (original.exists() and output.exists() and original.samefile(output)):
            raise ValueError('Output cannot overwrite source')
