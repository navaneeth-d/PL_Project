class PluginProxy:
    def __init__(self, runtime, ctx):
        self._runtime = runtime
        self._ctx = ctx

    def __getattr__(self, func_name):
        def wrapper(*args):
            return self._runtime.call(self._ctx, func_name, *args)
        return wrapper
