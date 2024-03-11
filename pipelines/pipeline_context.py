import asyncio

class PipelineContext:
    def __init__(self):
        self.outputs = {}
        self.events = {}

    async def set_output(self, name, value):
        """Set the output value and notify any waiters."""
        self.outputs[name] = value
        event = self.events.get(name)
        if event and event.is_set() == False:
            event.set()

    async def get_output(self, name):
        """Get the output value if available, or wait for it to be set."""
        if name in self.outputs:
            return self.outputs[name]

        if name not in self.events:
            self.events[name] = asyncio.Event()

        await self.events[name].wait()
        return self.outputs[name]
