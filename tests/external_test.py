from typing import TypeVar

import pytest

from slipcover import slipcover as sc

F = TypeVar("F")

@pytest.mark.xfail(reason="https://github.com/plasma-umass/slipcover/issues/3", raises=TypeError, strict=True)
def test_cloudpickle_function():
    # cloudpickle is a pseudo-standard library used in distributed applications, like dask
    # it extends pickle with support for pickling local functions and code objects
    cloudpickle = pytest.importorskip("cloudpickle")

    sci = sc.Slipcover()

    def cycle(f: F) -> F:
        return cloudpickle.loads(cloudpickle.dumps(f))

    # local functions are pickled "by value" by cloudpickle
    # this breaks under slipcover, because the function's code object is
    # instrumented with process-local tracing capsules
    #
    # i.e. TypeError: cannot pickle 'PyCapsule' object
    # https://github.com/plasma-umass/slipcover/issues/3
    #
    # deinstrumentation does't remove the capsules, is just disables them
    # so we still have pickle problems
    def local_func():
        return "local"

    # non-instrumented function is passes
    assert cycle(local_func)() == "local"

    instrumented_local = sci.instrument(local_func)

    # cloudpickle cycle here raises
    try:
        assert cycle(instrumented_local)() == "local"
    except TypeError as ex:
        assert "cannot pickle 'PyCapsule' object" in str(ex)
        raise
