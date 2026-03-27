
##############################------------------WITH LOGGER---------------------############################### 

import asyncio
import re
from playwright.async_api import async_playwright
from configparser import ConfigParser
import pandas as pd
import os
from datetime import datetime
import logging

# ================= PATH CONFIG =================

BASE_FOLDER = r"C:\Users\vijay_m\OneDrive - Exdion Solutions Pvt. Ltd.-70692290\Documents\Project_Job_Creation\carroll"

TRACKER_PATH = os.path.join(BASE_FOLDER, "Carroll_Tracker.xlsx")
LOB_MASTER_PATH = os.path.join(BASE_FOLDER, "Lob_Mapping.xlsx")
PDF_BASE_FOLDER = os.path.join(BASE_FOLDER, "Job_Creation")
CONFIG_PATH = os.path.join(BASE_FOLDER, "Config.ini")


# ================= LOGGING SETUP =================
from logging.handlers import RotatingFileHandler

LOG_FOLDER = os.path.join(BASE_FOLDER, "Logs")
os.makedirs(LOG_FOLDER, exist_ok=True)

log_file = os.path.join(
    LOG_FOLDER,
    f"Job_Creation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",   # removes milliseconds
    handlers=[
        RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
#---------------------------------------------------
logger = logging.getLogger(__name__)

#-------------------------------------------------------

MAX_RETRIES = 3
RETRY_DELAY = 5

# ================= LOAD LOB MAPPING =================


def load_lob_mapping():
    df_lob = pd.read_excel(LOB_MASTER_PATH)

    df_lob["LOB_CODE"] = df_lob["LOB_CODE"].astype(str).str.strip()
    df_lob["LOB_NAME"] = df_lob["LOB_NAME"].astype(str).str.strip()

    mapping = {}

    for _, row in df_lob.iterrows():
        code = row["LOB_CODE"]
        name = row["LOB_NAME"]

        if code not in mapping:
            mapping[code] = []

        mapping[code].append(name)

    return mapping

# ================= CRASH RECOVERY =================

def reset_in_progress():
    df = pd.read_excel(TRACKER_PATH)

    if "Status" in df.columns:
        df.loc[df["Status"] == "In Progress", "Status"] = "Pending"

    df.to_excel(TRACKER_PATH, index=False)
    logger.info("Reset any In Progress jobs back to Pending")

# ================= READ PENDING JOBS =================

def get_pending_jobs():
    if not os.path.exists(TRACKER_PATH):
        logger.warning("Tracker file not found")
        return pd.DataFrame()

    df = pd.read_excel(TRACKER_PATH)

    if df.empty:
        return pd.DataFrame()

    pending = df[df["Status"] == "Pending"].copy()
    logger.info(f"Total Pending Jobs: {len(pending)}")

    return pending

# ================= UPDATE TRACKER =================

def update_tracker(reference_id, job_id=None, status=None, error=None):

    df = pd.read_excel(TRACKER_PATH)

    for col in ["Job ID", "Status", "Error"]:
        if col in df.columns:
            df[col] = df[col].astype("string")

    idx = df.index[df["Reference ID"] == reference_id]

    if idx.empty:
        logger.info(f"Reference ID not found -> {reference_id}")
        return

    row_index = idx[0]

    if job_id is not None:
        df.at[row_index, "Job ID"] = str(job_id)

    if status is not None:
        df.at[row_index, "Status"] = str(status)

    if error is not None:
        df.at[row_index, "Error"] = str(error)

    df.at[row_index, "Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df.to_excel(TRACKER_PATH, index=False)

    logger.info(f"Tracker Updated -> {reference_id} | {status} | {error}")

# ================= LOGIN FUNCTION =================

async def login(page, url, username, password):

    await page.goto(url, timeout=60000)

    await page.locator("input[name='username']").fill(username)
    await page.locator("input[name='password']").fill(password)
    await page.locator("input[name='termsAccepted']").check()

    await page.get_by_role("button", name="Submit").click()

    logger.info("Login Successful")

    await page.get_by_role("button", name="Take me there").first.click()
    await page.get_by_role("button", name="Jobs").click()
    await page.get_by_role("button", name="Upload Documents").click()

    logger.info("Navigated to Upload Documents")


# ================= CREATE JOB FUNCTION =================

async def create_job(page, record, lob_mapping):

    ref_id = record["Reference ID"]
    logger.info(f"Creating Job -> {ref_id}")

    folder_path = os.path.join(PDF_BASE_FOLDER, ref_id)

    current_term_files = []
    prior_term_files = []
    other_files = []

    # ================= DETECT FILE TYPES =================

    if os.path.exists(folder_path):

        files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

        NON_POLICY_KEYWORDS = [
            "binder",
            "quote",
            "proposal",
            "schedule",
            "endorsement",
            "accord",
            "application",
            "app",
            "endt",
            "accord"
        ]
    
    # ================= CLASSIFY FILES =================

        # for file in files:
        #     file_lower = file.lower()

        #     is_current_term = False
        #     is_prior_term = False

        #     is_non_policy = any(word in file_lower for word in NON_POLICY_KEYWORDS)

        #     # ---- Detect CT ----
        #     if re.search(r"\b26[-_/]27\b", file_lower) and not is_non_policy:
        #         is_current_term = True

        #     # ---- Detect PT ----
        #     elif re.search(r"\b25[-_/]26\b", file_lower) and not is_non_policy:
        #         is_prior_term = True

        #     # ---- Date Range Format ----
        #     else:
        #         match = re.search(
        #             r"\d{1,2}-\d{1,2}-(\d{2})\s*to\s*\d{1,2}-\d{1,2}-(\d{2})",
        #             file_lower
        #         )

        #         if match and not is_non_policy:
        #             start_year = match.group(1)
        #             end_year = match.group(2)

        #             if start_year == "26" and end_year == "27":
        #                 is_current_term = True
        #             elif start_year == "25" and end_year == "26":
        #                 is_prior_term = True

        #     if is_current_term:
        #         current_term_files.append(file)
        #     elif is_prior_term:
        #         prior_term_files.append(file)
        #     else:
        #         other_files.append(file)


        for file in files:
            file_lower = file.lower()

            is_current_term = False
            is_prior_term = False

            # Check NON-POLICY keywords (these should block CT/PT)
            is_non_policy = any(word in file_lower for word in NON_POLICY_KEYWORDS)

            #  Step 1: If NON-POLICY → directly classify as OTHER
            if is_non_policy:
                other_files.append(file)
                continue

            # ---- Detect CT ----
            if re.search(r"\b26[-_/]27\b", file_lower):
                is_current_term = True

            # ---- Detect PT ----
            elif re.search(r"\b25[-_/]26\b", file_lower):
                is_prior_term = True

            # ---- Date Range Format ----
            else:
                match = re.search(
                    r"\d{1,2}-\d{1,2}-(\d{2})\s*to\s*\d{1,2}-\d{1,2}-(\d{2})",
                    file_lower
                )

                if match:
                    start_year = match.group(1)
                    end_year = match.group(2)

                    if start_year == "26" and end_year == "27":
                        is_current_term = True
                    elif start_year == "25" and end_year == "26":
                        is_prior_term = True

            # ---- Classification ----
            if is_current_term:
                current_term_files.append(file)

            elif is_prior_term:
                prior_term_files.append(file)

            else:
                other_files.append(file)



    
    # ================= TAB SELECTION =================

    if len(other_files) == 0:

        logger.info("Only CT & PT found -> Automatic Renewal")

        tab = page.get_by_role("tab", name="Automatic Renewal")
        await tab.wait_for(timeout=20000)
        await tab.click()

    else:

        logger.info("Other documents found -> Marketed Renewal")

        tab = page.get_by_role("tab", name="Marketed Renewal")
        await tab.wait_for(timeout=20000)
        await tab.click()

    await page.wait_for_timeout(2000)

    # ================= SELECT LOB =================

    lob_code = str(record["LOB"]).strip()

    if lob_code not in lob_mapping:
        raise Exception(f"LOB Code not found in LOB Master: {lob_code}")

    possible_lob_names = lob_mapping[lob_code]

    logger.info(f"Trying LOB names -> {possible_lob_names}")

    # Open dropdown
    await page.locator("#coverage").click()
    await page.get_by_role("listbox").wait_for()

    options = page.get_by_role("option")
    count = await options.count()

    selected = False

    for i in range(count):
        option_text = (await options.nth(i).inner_text()).strip()

        for lob_name in possible_lob_names:
            if option_text.lower() == lob_name.strip().lower():
                await options.nth(i).click()
                logger.info(f"LOB Selected -> {option_text}")
                selected = True
                break

        if selected:
            break

    if not selected:
        raise Exception(f"No matching LOB found in dropdown for code: {lob_code}")
    

    # ================= CHECKLIST =================

    await page.locator("#checklist").click()
    await page.get_by_role("listbox").wait_for()

    await page.locator("li[role='option']", has_text="Lite_ExdionPOD").click()

    logger.info("Checklist Selected -> Lite_ExdionPOD")

    # ================= FILE UPLOAD =================

    ordered_files = current_term_files + prior_term_files + other_files

    for file in ordered_files:

        file_lower = file.lower()
        file_path = os.path.join(folder_path, file)

        # ===== CURRENT TERM =====
        if file in current_term_files:
            logger.info(f"Uploading to Current Term -> {file}")
            label = page.locator("p:has-text('Current Term Policy')")
            section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
            await section.locator("input[type='file']").set_input_files(file_path)

            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1500)

        # ===== PRIOR TERM =====
        elif file in prior_term_files:
            logger.info(f"Uploading to Prior Term -> {file}")
            label = page.locator("p:has-text('Prior Term Policy')")
            section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
            await section.locator("input[type='file']").set_input_files(file_path)

        # ===== OTHER DOCUMENTS =====
        else:

            if "endorsement" in file_lower or "endt" in file_lower:
                label_text = "Endorsement"

            elif "quote" in file_lower or "qte" in file_lower or "quotation" in file_lower:
                label_text = "Carrier Quote"

            elif "proposal" in file_lower:
                label_text = "Proposal"

            elif "accord" in file_lower or "application" in file_lower or "app" in file_lower:
                label_text = "Acord Application"

            elif "schedule" in file_lower:
                label_text = "Schedule"

            elif "binder" in file_lower or "bind" in file_lower:
                label_text = "Binder"

            else:
                logger.warning(f"Not matched -> {file}")
                continue

            logger.info(f"Uploading to {label_text} -> {file}")

            label = page.locator(f"p:has-text('{label_text}')")
            await label.scroll_into_view_if_needed()

            section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")

            await section.locator("input[type='file']").set_input_files(file_path)


    # async with page.expect_event("dialog", timeout=40000) as dialog_info:
    #     await page.get_by_role("button", name="Generate Checklist").click()

    # dialog = await dialog_info.value

    # message = dialog.message
    # logger.info("Popup message: %s", message)

    # # ===== HANDLE ERROR POPUP =====
    # if any(text in message.lower() for text in [
    #     "Please choose", "Proposal", "ACORD Application", "Carrier Quote", "Binder"
    # ]):

    #     error_msg = "Please choose Proposal or ACORD Application or Carrier Quote or Binder"

    #     await dialog.accept()

    #     update_tracker(
    #         reference_id=record["Reference ID"],
    #         status="Error",
    #         error=error_msg
    #     )

    #     return None


    # try:
    #     dialog = await dialog_info.value
    #     message = dialog.message.lower()

    #     logger.info(f"Popup message -> {message}")

    #     if "please choose" in message:
    #         await dialog.accept()
    #         return None

    # except:
    #     # fallback if modal popup
    #     if await page.locator("text=Please choose").is_visible():
    #         logger.info("Validation modal detected")

    #         await page.get_by_role("button", name="OK").click()

    #         return None

    # # Extract Job ID
    # match = re.search(r"Job ID:\s*(\S+)", message)
    # job_id = match.group(1) if match else None

    # logger.info("Job ID: %s", job_id)

    # await page.wait_for_timeout(3000)

    # await dialog.accept()

    # logger.info(f"Job Created Successfully -> {job_id}")


    await page.wait_for_timeout(10000)

    await page.get_by_role("button", name="Jobs").click()
    await page.get_by_role("button", name="Upload Documents").click()
    await page.wait_for_timeout(5000)

    await page.get_by_role("tab", name="Marketed Renewal").wait_for()

    # return job_id

# ================= MAIN FUNCTION =================

async def run_istudio():

    logger.info("ISTUDIO started")

    config = ConfigParser()
    config.read(CONFIG_PATH)

    browser_name = config.get("CarrolliStudio", "browser")
    url = config.get("CarrolliStudio", "Link")
    username = config.get("CarrolliStudio", "User_ID")
    password = config.get("CarrolliStudio", "Password")

    # Crash recovery
    reset_in_progress()

    lob_mapping = load_lob_mapping()
    pending_df = get_pending_jobs()

    if pending_df.empty:
        logger.info("No Pending Jobs Found")
        return

    async with async_playwright() as p:

        if browser_name.lower() == "chrome":
            browser = await p.chromium.launch(channel="chrome", headless=False)
        elif browser_name.lower() == "edge":
            browser = await p.chromium.launch(channel="msedge", headless=False)
        else:
            raise Exception("Unsupported browser")

        context = await browser.new_context()
        page = await context.new_page()

        await login(page, url, username, password)


        for _, row in pending_df.iterrows():

            ref_id = row["Reference ID"]
            attempt = 1

            while attempt <= MAX_RETRIES:

                try:
                    if attempt == 1:
                        update_tracker(ref_id, status="In Progress")

                    logger.info(f"\nProcessing {ref_id} | Attempt {attempt}")

                    job_id = await create_job(page, row, lob_mapping)

                    if job_id is None:
                        logger.info(f"Skipping {ref_id} due to validation error")
                        break

                    update_tracker(ref_id, job_id=job_id, status="Completed")

                    break   # Success -> Exit retry loop

                except Exception as e:

                    logger.info(f"Attempt {attempt} Failed -> {ref_id}")
                    logger.info(str(e))

                    if attempt == MAX_RETRIES:
                        logger.info(f"Max retries reached -> {ref_id}")
                        update_tracker(ref_id, status="Error")
                        break

                    attempt += 1

                    await page.wait_for_timeout(20000)
                    await page.get_by_role("button", name="Jobs").click()
                    await page.get_by_role("button", name="Upload Documents").click()
                    await page.wait_for_timeout(5000)

                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)

                    # Optional: reload page before retry
                    if not page.is_closed():
                        await page.reload()

        logger.info("\nAll Jobs Processed")

        try:
            logger.info("Logging out...")

            profile_btn = page.locator("svg[data-testid='KeyboardArrowDownIcon']").first
            await profile_btn.click()

            logout_btn = page.get_by_role("menuitem", name="Sign Out")
            await logout_btn.click()

            logger.info("Logout Successful")

        except Exception as e:
            logger.info("Logout failed:", str(e))

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_istudio())







