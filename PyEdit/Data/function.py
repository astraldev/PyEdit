from ._functions import *
import asyncio

async def load_(textbuff):
  await syntax_error(textbuff)

def load(tb):
  #load_(tb)
  loop = asyncio.get_event_loop()
  loop.run_until_complete(load_(tb))


