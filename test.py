import asyncio
import random
import sys

from tqdm import tqdm


async def task_func():
    total = random.randint(1, 30)
    with tqdm(total=total, dynamic_ncols=True, leave=False) as pbar:
        for _ in range(total):
            pbar.update()
            await asyncio.sleep(random.uniform(0.5, 1))
        pbar.set_description("Task completed")


async def logger_func():
    while True:
        tqdm.write("logging...", file=sys.stdout)
        tqdm.write(f"instances: {len(getattr(tqdm, '_instances'))}", file=sys.stderr)
        await asyncio.sleep(random.uniform(1, 3))


async def main():
    tasks = []
    tasks.append(asyncio.create_task(logger_func()))
    while True:
        task = asyncio.create_task(task_func())
        tasks.append(task)
        await asyncio.sleep(random.uniform(1, 3))


asyncio.run(main())
