# import asyncio
# from Carroll_Epic import run_epic
# from Carroll_iStudio import run_istudio


# async def Job_Creation():

#     print("========== PHASE 1 : EPIC ==========")
#     await run_epic()

#     print("========== PHASE 2 : ISTUDIO ==========")
#     await run_istudio()

#     print("========== JOB CREATION COMPLETED ==========")


# if __name__ == "__main__":
#     asyncio.run(Job_Creation())

# ################################################################################################################

# import asyncio
# from Carroll_Epic import run_epic
# from Carroll_iStudio import run_istudio
# from Email_Alert import send_email
# import traceback
# import time

# async def Job_Creation():

#     start = time.time()

#     try:
#         print("========== PHASE 1 : EPIC ==========")
#         await run_epic()

#     except Exception as e:
#         error = traceback.format_exc()
#         send_email("EPIC FAILED", error)
#         return

#     try:
#         print("========== PHASE 2 : ISTUDIO ==========")
#         await run_istudio()

#     except Exception as e:
#         error = traceback.format_exc()
#         send_email("ISTUDIO FAILED", error)
#         return

#     #send_email("JOB SUCCESS", "Epic + iStudio completed successfully")
#     end = time.time()
#     duration = round(end - start, 2)

#     send_email("JOB SUCCESS", f"Epic + iStudio completed successfully\nTime Taken: {duration} seconds")

###########################3#-------------------------------------- PRODUCTION LEVEL ----------------------------------------###########################################

# import asyncio
# from Carroll_Epic import run_epic
# from Carroll_iStudio import run_istudio
# from Email_Alert import send_email
# import traceback
# import time

# PHASES = [
#     ("EPIC", run_epic),
#     ("ISTUDIO", run_istudio)
# ]


# async def Job_Creation():

#     for name, func in PHASES:

#         start = time.time()

#         try:
#             print(f"========== RUNNING {name} ==========")

#             await func()

#             print(f" {name} COMPLETED")

#         except Exception as e:

#             error = traceback.format_exc()

#             print(f" {name} FAILED")

#             send_email(f"{name} FAILED", error)

#             return   # stop pipeline

#     send_email("JOB SUCCESS", "Epic + iStudio completed successfully")
#     end = time.time()
#     duration = round(end - start, 2)

#     send_email("JOB SUCCESS", f"Epic + iStudio completed successfully\nTime Taken: {duration} seconds") 

# if __name__ == "__main__":
#     asyncio.run(Job_Creation())



#-------------------------------------------------------########################    PRODUCTION LEVEL WITH ATTACHMENT     ########################-------------------------------------------------------


# import asyncio
# from Carroll_Epic import run_epic
# from Carroll_iStudio import run_istudio, generate_daily_report
# from Email_Alert import send_email
# import traceback
# import time

# PHASES = [
#     ("EPIC", run_epic),
#     ("ISTUDIO", run_istudio)
# ]


# async def Job_Creation():

#     start = time.time()

#     for name, func in PHASES:

#         try:
#             print(f"========== RUNNING {name} ==========")

#             await func()

#             print(f" {name} COMPLETED")

#         except Exception as e:

#             error = traceback.format_exc()

#             print(f" {name} FAILED")

#             send_email(f"{name} FAILED", error)

#             return   # stop pipeline


#     end = time.time()
#     duration = round(end - start, 2)
#     print(f"Total Time: {duration} seconds")

#     try:
#         summary, report_path = generate_daily_report()

#         # Add timing info into report
#         summary += f"\n\n⏱ Total Execution Time: {duration} seconds"

#         send_email(
#             "JOB SUMMARY REPORT",
#             summary,
#             report_path
#         )

#     except Exception as e:
#         send_email("REPORT FAILED", str(e))
        
# if __name__ == "__main__":
#     asyncio.run(Job_Creation())




import asyncio
from Carroll_Epic import run_epic
from Carroll_iStudio import run_istudio, generate_daily_report
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