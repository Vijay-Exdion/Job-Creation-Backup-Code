import asyncio
from Thomson_Epic import run_epic
from Thomson_iStudio import run_istudio


async def Job_Creation():

    print("========== PHASE 1 : EPIC ==========")
    await run_epic()

    print("========== PHASE 2 : ISTUDIO ==========")
    await run_istudio()

    print("========== JOB CREATION COMPLETED ==========")


if __name__ == "__main__":
    asyncio.run(Job_Creation())




# import logging
# from logging.handlers import RotatingFileHandler
# import os
# import asyncio
# from datetime import datetime

# # ================= LOGGING CONFIGURATION =================

# BASE_FOLDER = r"C:\Users\vijay_m\OneDrive - Exdion Solutions Pvt. Ltd.-70692290\Documents\Project_Job_Creation\Thomson"
# LOG_FOLDER = os.path.join(BASE_FOLDER, "Logs")
# os.makedirs(LOG_FOLDER, exist_ok=True)

# log_file = os.path.join(
#     LOG_FOLDER,
#     f"Job_Creation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
# )

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",   # removes milliseconds
#     handlers=[
#         RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5),
#         logging.StreamHandler()
#     ]
# )

# logger = logging.getLogger(__name__)


# from Thomson_Epic import run_epic
# from Thomson_iStudio import run_istudio

# # ================= MAIN JOB =================

# async def Job_Creation():

#     logger.info("========== JOB CREATION STARTED ==========")



#     try:
#         logger.info("========== PHASE 1 : EPIC ==========")
#         await run_epic()
#         logger.info("EPIC Phase Completed Successfully")




#         logger.info("========== PHASE 2 : ISTUDIO ==========")
#         await run_istudio()
#         logger.info("ISTUDIO Phase Completed Successfully")

#         logger.info("========== JOB CREATION COMPLETED ==========")



#     except Exception as e:
#         logger.critical("FATAL ERROR IN JOB CREATION", exc_info=True)

#     finally:
#         logger.info("========== PROGRAM ENDED ==========")



# if __name__ == "__main__":
#     asyncio.run(Job_Creation())