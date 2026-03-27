import asyncio
from Carroll_Epic import run_epic
from Carroll_iStudio import run_istudio


async def Job_Creation():

    print("========== PHASE 1 : EPIC ==========")
    await run_epic()

    print("========== PHASE 2 : ISTUDIO ==========")
    await run_istudio()

    print("========== JOB CREATION COMPLETED ==========")


if __name__ == "__main__":
    asyncio.run(Job_Creation())



