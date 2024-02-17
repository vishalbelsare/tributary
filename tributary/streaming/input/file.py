import aiofiles
import json as JSON
from .input import Func


class File(Func):
    """Open up a file and yield back lines in the file

    Args:
        filename (str): filename to read
        json (bool): load file line as json
    """

    def __init__(self, filename, json=False, csv=False):
        assert not (json and csv)

        async def _file(filename=filename, json=json, csv=csv):
            if csv:
                async with aiofiles.open(filename) as f:
                    async for line in f:
                        yield line.strip().split(",")
            else:
                async with aiofiles.open(filename) as f:
                    async for line in f:
                        if json:
                            yield JSON.loads(line)
                        else:
                            yield line

        super().__init__(func=_file)
        self._name = "File"
