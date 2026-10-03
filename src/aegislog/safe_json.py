"""Reject excessive structural nesting before recursive JSON decoding."""
import json


def loads(text, max_depth=64):
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > max_depth:
                raise ValueError('JSON nesting exceeds the supported depth of 64')
        elif char in ']}':
            depth -= 1
    return json.loads(text)
