# import asyncio
# from Thomson_Epic import run_epic
# from Thomson_iStudio import run_istudio


# async def Job_Creation():

#     print("========== PHASE 1 : EPIC ==========")
#     await run_epic()

#     print("========== PHASE 2 : ISTUDIO ==========")
#     await run_istudio()

#     print("========== JOB CREATION COMPLETED ==========")


# if __name__ == "__main__":
#     asyncio.run(Job_Creation())


import asyncio
from Thomson_Epic import run_epic
from Thomson_iStudio import run_istudio, generate_daily_report
from Email_Alert import send_email
import traceback
import time

PHASES = [
    ("EPIC", run_epic, 3600),      # 1 hour
    ("ISTUDIO", run_istudio, 7200) # 2 hours
]

async def Job_Creation():

    start = time.time()

    for name, func, timeout in PHASES:

        try:
            print(f"========== RUNNING {name} ==========")

            await asyncio.wait_for(func(), timeout=timeout)

            print(f"{name} COMPLETED")

        except asyncio.TimeoutError:
            print(f"{name} TIMEOUT")

            send_email(f"{name} TIMEOUT", f"{name} exceeded {timeout} seconds")
            return
            #continue

        except Exception:
            error = traceback.format_exc()

            print(f"{name} FAILED")

            send_email(f"{name} FAILED", error)
            return


    end = time.time()
    duration = round(end - start, 2)
    print(f"Total Time: {duration} seconds")

    try:
        summary, report_path = generate_daily_report()

        summary += f"\n\n⏱ Total Execution Time: {duration} seconds"

        send_email(
            "JOB SUMMARY REPORT",
            summary,
            report_path
        )

    except Exception as e:
        send_email("REPORT FAILED", str(e))
        
if __name__ == "__main__":
    asyncio.run(Job_Creation())