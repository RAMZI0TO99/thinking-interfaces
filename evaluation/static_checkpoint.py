"""Inert inspection of a restricted protocol-2 torch checkpoint vocabulary.

This is NOT an unpickler. GLOBAL, REDUCE, NEWOBJ and BUILD are recorded as
descriptors; no referenced class/function is imported, instantiated or called.
It cannot load a model. Unknown opcodes and malformed structures fail closed.
"""

from __future__ import annotations

import math
import pickletools
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GlobalName:
    name: str


@dataclass(eq=False)
class Descriptor:
    kind: str
    target: Any
    arguments: Any
    items: dict[Any, Any] = field(default_factory=dict)
    state: Any = None


def inspect_metadata(payload: bytes) -> Any:
    """Return inert builtins/descriptors, without executing pickle operations."""
    if len(payload) > 8 * 1024 * 1024:
        raise ValueError("metadata exceeds inspection limit")
    stack: list[Any] = []
    memo: dict[int, Any] = {}
    mark = object()

    def pop() -> Any:
        if not stack or stack[-1] is mark:
            raise ValueError("metadata stack underflow")
        return stack.pop()

    def marked() -> list[Any]:
        values = []
        while stack and stack[-1] is not mark:
            values.append(stack.pop())
        if not stack:
            raise ValueError("missing metadata mark")
        stack.pop()
        return values[::-1]

    def set_items(target: Any, values: list[Any]) -> None:
        if len(values) % 2:
            raise ValueError("unpaired metadata dictionary item")
        if isinstance(target, Descriptor):
            if target.target != GlobalName("collections OrderedDict") or target.arguments != ():
                raise ValueError("unsupported dictionary descriptor")
            target = target.items
        if not isinstance(target, dict):
            raise ValueError("dictionary operation on non-dictionary")
        for key, value in zip(values[::2], values[1::2], strict=True):
            if type(key) not in (int, str) or key in target:
                raise ValueError("unsupported or duplicate metadata key")
            target[key] = value

    try:
        for count, (opcode, argument, position) in enumerate(pickletools.genops(payload)):
            if count > 200_000 or len(stack) > 20_000 or len(memo) > 30_000:
                raise ValueError("metadata complexity limit exceeded")
            name = opcode.name
            if count == 0 and (name != "PROTO" or argument != 2):
                raise ValueError("only explicit protocol 2 is inspected")
            if name == "PROTO":
                if count != 0:
                    raise ValueError("repeated protocol declaration")
            elif name == "MARK":
                stack.append(mark)
            elif name in {"BININT", "BININT1", "BININT2", "BINUNICODE", "BINFLOAT"}:
                stack.append(argument)
            elif name == "NONE":
                stack.append(None)
            elif name in {"NEWTRUE", "NEWFALSE"}:
                stack.append(name == "NEWTRUE")
            elif name == "EMPTY_DICT":
                stack.append({})
            elif name == "EMPTY_LIST":
                stack.append([])
            elif name == "EMPTY_TUPLE":
                stack.append(())
            elif name == "GLOBAL":
                if not isinstance(argument, str):
                    raise ValueError("invalid global name")
                stack.append(GlobalName(argument))
            elif name in {"BINPUT", "LONG_BINPUT"}:
                if not isinstance(argument, int) or argument < 0:
                    raise ValueError("invalid memo index")
                if not stack or stack[-1] is mark or argument in memo:
                    raise ValueError("invalid or repeated memo assignment")
                memo[argument] = stack[-1]
            elif name in {"BINGET", "LONG_BINGET"}:
                if not isinstance(argument, int) or argument < 0:
                    raise ValueError("invalid memo index")
                stack.append(memo[argument])
            elif name == "TUPLE":
                stack.append(tuple(marked()))
            elif name in {"TUPLE1", "TUPLE2", "TUPLE3"}:
                values = [pop() for _ in range(int(name[-1]))]
                stack.append(tuple(values[::-1]))
            elif name in {"REDUCE", "NEWOBJ"}:
                arguments, target = pop(), pop()
                if not isinstance(target, GlobalName) or not isinstance(arguments, tuple):
                    raise ValueError("unsupported call descriptor")
                stack.append(Descriptor(name, target, arguments))
            elif name == "BINPERSID":
                stack.append(Descriptor(name, None, pop()))
            elif name == "BUILD":
                state = pop()
                if not stack or not isinstance(stack[-1], Descriptor):
                    raise ValueError("state operation on non-descriptor")
                if stack[-1].state is not None:
                    raise ValueError("repeated state operation")
                stack[-1].state = state
            elif name == "SETITEM":
                value, key = pop(), pop()
                if not stack:
                    raise ValueError("missing dictionary")
                set_items(stack[-1], [key, value])
            elif name == "SETITEMS":
                values = marked()
                if not stack:
                    raise ValueError("missing dictionary")
                set_items(stack[-1], values)
            elif name == "APPENDS":
                values = marked()
                if not stack or not isinstance(stack[-1], list):
                    raise ValueError("list operation on non-list")
                stack[-1].extend(values)
            elif name == "STOP":
                if len(stack) != 1 or stack[0] is mark or position != len(payload) - 1:
                    raise ValueError("invalid stop or trailing metadata")
                return stack[0]
            else:
                raise ValueError(f"unsupported metadata opcode: {name}")
    except (IndexError, KeyError, TypeError, OverflowError) as error:
        raise ValueError("malformed static metadata") from error
    raise ValueError("missing metadata stop")


@dataclass(frozen=True)
class TensorSlice:
    storage_key: str
    storage_elements: int
    offset: int
    shape: tuple[int, ...]
    stride: tuple[int, ...]

    @property
    def elements(self) -> int:
        return math.prod(self.shape)


def float_tensor_slice(value: Any) -> TensorSlice:
    """Accept only dense contiguous FloatStorage tensor metadata (no decoding)."""
    if (
        not isinstance(value, Descriptor)
        or value.kind != "REDUCE"
        or value.target != GlobalName("torch._utils _rebuild_tensor_v2")
        or len(value.arguments) != 6
        or value.state is not None
        or value.items
    ):
        raise ValueError("unsupported tensor descriptor")
    storage, offset, shape, stride, requires_grad, hooks = value.arguments
    if not isinstance(storage, Descriptor) or storage.kind != "BINPERSID":
        raise ValueError("missing static storage descriptor")
    if not isinstance(storage.arguments, tuple) or len(storage.arguments) != 5:
        raise ValueError("unsupported storage descriptor")
    tag, dtype, key, location, size = storage.arguments
    if (
        tag != "storage"
        or dtype != GlobalName("torch FloatStorage")
        or not isinstance(key, str)
        or not key.isascii()
        or not key.isdecimal()
        or not isinstance(location, str)
        or type(size) is not int
        or size < 1
        or type(offset) is not int
        or offset < 0
        or type(shape) is not tuple
        or type(stride) is not tuple
        or len(shape) != len(stride)
        or any(type(number) is not int or number < 1 for number in shape)
        or any(type(number) is not int for number in stride)
        or requires_grad is not False
        or not isinstance(hooks, Descriptor)
        or hooks.target != GlobalName("collections OrderedDict")
        or hooks.arguments != ()
        or hooks.items
        or hooks.state is not None
    ):
        raise ValueError("unsupported tensor/storage metadata")
    expected_stride = 1
    for dimension, step in zip(reversed(shape), reversed(stride), strict=True):
        if step != expected_stride:
            raise ValueError("noncontiguous tensor is not supported")
        expected_stride *= dimension
    if offset + expected_stride > size:
        raise ValueError("tensor exceeds its storage")
    return TensorSlice(key, size, offset, shape, stride)
