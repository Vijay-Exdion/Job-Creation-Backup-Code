import asyncio
import re
from playwright.async_api import async_playwright
from configparser import ConfigParser
import pandas as pd
import os
from datetime import datetime

# ================= PATH CONFIG =================

BASE_FOLDER = r"C:\Users\vijay_m\OneDrive - Exdion Solutions Pvt. Ltd.-70692290\Documents\Project_Job_Creation\Thomson"

TRACKER_PATH = os.path.join(BASE_FOLDER, "Thomson_Tracker.xlsx")
LOB_MASTER_PATH = os.path.join(BASE_FOLDER, "Lob_Mapping.xlsx")
PDF_BASE_FOLDER = os.path.join(BASE_FOLDER, "Job_Creation")
CONFIG_PATH = os.path.join(BASE_FOLDER, "Config.ini")


MAX_RETRIES = 3
RETRY_DELAY = 5

#-----------------------------------------------------------------------
################################## Correct One with OCR ##########################################

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\vijay_m\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Users\vijay_m\poppler-25.12.0\Library\bin"

# flexible keywords
TOTAL_KEYWORDS = [
    "grand total",
    "total due",
    "amount due",
    "policy total",
    "total premium",
    "premium total",
    "total",
    "total estimated annual premium",
    "total policy premium",
    "premium shown is payable",
    "annual premium",
    "policy premium"
]

IGNORE_WORDS = [
    "subtotal",
    "subtotals",
    "class premium",
    "coverage premium",
    "estimated annual remuneration",
    "rate per",
    "limit",
    "aggregate",
    "fee",
    "fees",
    "policy fee",
    "tax",
    "taxes",
    "surplus lines tax"
]


AMOUNT_REGEX = r"\$?\s*([\d]{1,3}(?:,[\d]{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)"


def find_premium(text):

    lines = text.split("\n")

    totals = []
    values = []

    for i, line in enumerate(lines):

        line_lower = line.lower()

        if any(word in line_lower for word in IGNORE_WORDS):
            continue

        # detect number on same line
        match = re.search(AMOUNT_REGEX, line)

        if match:
            value = float(match.group(1).replace(",", ""))
            if value < 100:
                continue
            values.append(value)

            if any(k in line_lower for k in TOTAL_KEYWORDS):
                totals.append(value)

        # detect number on next line
        if any(k in line_lower for k in TOTAL_KEYWORDS):

            if i + 1 < len(lines):
                match = re.search(AMOUNT_REGEX, lines[i + 1])

                if match:
                    totals.append(float(match.group(1).replace(",", "")))

    # priority 1 → totals
    if totals:
        return max(totals)

    # priority 2 → largest value
    if values:
        return max(values)

    return None


def extract_premium_from_pdf(pdf_path):

    text = ""

    # ---------- Try normal PDF extraction ----------
    try:
        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages[:10]:

                page_text = page.extract_text()

                if page_text:
                    text += page_text.lower() + "\n"

    except Exception as e:
        print("pdfplumber error:", e)
    
    # print("----- PDF TEXT SAMPLE -----")
    # print(text[:8000])
    # print("---------------------------")

    premium = find_premium(text)

    if premium:
        return premium

    # ---------- OCR fallback ----------
    print("Running OCR...")

    images = convert_from_path(
        pdf_path,
        dpi=300,
        first_page=1,
        last_page=10,
        poppler_path=POPPLER_PATH
    )

    text = ""

    for img in images:
        text += pytesseract.image_to_string(img).lower() + "\n"

    # print("----- PDF TEXT SAMPLE -----")
    # print(text[:8000])
    # print("---------------------------")

    premium = find_premium(text)

    if premium:
        return premium

    return None

#--------------------------------------------------------------------------------

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
    print("Reset any In Progress jobs back to Pending")

# ================= READ PENDING JOBS =================

def get_pending_jobs():
    if not os.path.exists(TRACKER_PATH):
        print("Tracker file not found")
        return pd.DataFrame()

    df = pd.read_excel(TRACKER_PATH)

    if df.empty:
        return pd.DataFrame()

    pending = df[df["Status"] == "Pending"].copy()
    print(f"Total Pending Jobs: {len(pending)}")

    return pending

# ================= UPDATE TRACKER =================

def update_tracker(reference_id, job_id=None, status=None, error=None, premium=None, csr_type=None):

    df = pd.read_excel(TRACKER_PATH)

    for col in ["Job ID", "Status", "Error"]:
        if col in df.columns:
            df[col] = df[col].astype("string")

    idx = df.index[df["Reference ID"] == reference_id]

    if idx.empty:
        print(f"Reference ID not found → {reference_id}")
        return

    row_index = idx[0]

    if job_id is not None:
        df.at[row_index, "Job ID"] = str(job_id)

    if status is not None:
        df.at[row_index, "Status"] = str(status)

    if error is not None:
        df.at[row_index, "Error"] = str(error)

    # if premium is not None and "Premium" in df.columns:
    #     df.at[row_index, "Premium"] = round(premium, 2)

    # if csr_type is not None and "CSR Type" in df.columns:
    #     df.at[row_index, "CSR Type"] = csr_type

    # Create columns if missing
    if "Premium" not in df.columns:
        df["Premium"] = ""

    if "CSR Type" not in df.columns:
        df["CSR Type"] = ""

    # Update values
    if premium is not None:
        df.at[row_index, "Premium"] = round(premium, 2)

    if csr_type is not None:
        df.at[row_index, "CSR Type"] = csr_type

    df.at[row_index, "Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df.to_excel(TRACKER_PATH, index=False)

    updates = []

    if premium is not None:
        updates.append(f"Premium={premium}")

    if csr_type is not None:
        updates.append(f"CSR={csr_type}")

    if status is not None:
        updates.append(f"Status={status}")

    if error is not None:
        updates.append(f"Error={error}")

    print(f"Tracker Updated → {reference_id} | " + " | ".join(updates))

# ================= LOGIN FUNCTION =================

async def login(page, url, username, password):

    await page.goto(url, timeout=60000)

    await page.locator("input[name='username']").fill(username)
    await page.locator("input[name='password']").fill(password)
    await page.locator("input[name='termsAccepted']").check()

    await page.get_by_role("button", name="Submit").click()

    print("Login Successful")

    await page.get_by_role("button", name="Take me there").first.click()


# ================= CREATE JOB FUNCTION =================

async def create_job(page, record, lob_mapping):

    ref_id = record["Reference ID"]
    print(f"Creating Job -> {ref_id}")

    # ================= Select Broker =================

    await page.wait_for_timeout(5000)

    broker_name = "Thomson Smith and Leach Insurance"

    await page.locator('div[role="combobox"]').first.click()
    await page.wait_for_selector('ul[role="listbox"]', timeout=60000)
    await page.locator(f'li[data-value="{broker_name}"]').click()
    print(f"Broker Selected → {broker_name}")


    # ================= ACCOUNT MANAGER ---> Primary CSR =================

    # account_manager = str(record["Account Manager"]).strip()
    # parts = account_manager.split()
    # username = (parts[0][0] + parts[-1]).lower()
    # email = f"{username}@tslins.com"
    # print(f"Account_manager → {account_manager}")
    # print(f"Selecting Primary CSR → {email}")

    manager_email_map = {
        "faith dirk": "stat093@tslins.com",
        "amy v. nunez, mba, cic, cisr": "stat088@tslins.com",
        "shelby lavergne": "stat052@tslins.com",
        "angela viator": "stat086@tslins.com"
    }

    account_manager = str(record["Account Manager"]).strip().lower()

    if account_manager in manager_email_map:
        email = manager_email_map[account_manager]
    else:
        parts = account_manager.split()
        username = (parts[0][0] + parts[-1]).lower()
        email = f"{username}@tslins.com"

    print(f"Account Manager → {account_manager}")
    print(f"Selecting Primary CSR → {email}")


    await page.locator('div[role="combobox"]').nth(1).click()
    await page.wait_for_selector('ul[role="listbox"]')
    #await page.get_by_role("option", name=email, exact=True).click()
    option = page.get_by_role("option", name=email, exact=True)

    if await option.count() > 0:
        await option.click()
        print(f"CSR Selected → {email}")

    else:
        print(f"CSR NOT FOUND → {email}")

        update_tracker(
            reference_id=record["Reference ID"],
            status="Error",
            error="New CSR Mail ID not selected"
        )

        await page.keyboard.press("Escape")
        return None
    
    await page.get_by_role("button", name="Save").click()


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

        for file in files:
            file_lower = file.lower()

            is_current_term = False
            is_prior_term = False

            is_non_policy = any(word in file_lower for word in NON_POLICY_KEYWORDS)

            # ---- Detect CT ----
            if re.search(r"\b26[-_/]27\b", file_lower) and not is_non_policy:
                is_current_term = True

            # ---- Detect PT ----
            elif re.search(r"\b25[-_/]26\b", file_lower) and not is_non_policy:
                is_prior_term = True

            # ---- Date Range Format ----
            else:
                match = re.search(
                    r"\d{1,2}-\d{1,2}-(\d{2})\s*to\s*\d{1,2}-\d{1,2}-(\d{2})",
                    file_lower
                )

                if match and not is_non_policy:
                    start_year = match.group(1)
                    end_year = match.group(2)

                    if start_year == "26" and end_year == "27":
                        is_current_term = True
                    elif start_year == "25" and end_year == "26":
                        is_prior_term = True

            if is_current_term:
                current_term_files.append(file)
            elif is_prior_term:
                prior_term_files.append(file)
            else:
                other_files.append(file)
    
    # ================= TAB SELECTION =================

    if len(other_files) == 0:

        print("Only CT & PT found -> Automatic Renewal")

        tab = page.get_by_role("tab", name="Automatic Renewal")
        await tab.wait_for(timeout=20000)
        await tab.click()

    else:

        print("Other documents found -> Marketed Renewal")

        tab = page.get_by_role("tab", name="Marketed Renewal")
        await tab.wait_for(timeout=20000)
        await tab.click()

    await page.wait_for_timeout(2000)

    # ================= LOB SELECTION =================

    lob_code = str(record["LOB"]).strip()

    if lob_code not in lob_mapping:
        raise Exception(f"LOB Code not found in LOB Master: {lob_code}")

    possible_lob_names = lob_mapping[lob_code]

    print(f"Trying LOB names → {possible_lob_names}")

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
                print(f"LOB Selected → {option_text}")
                selected = True
                break

        if selected:
            break

    if not selected:
        raise Exception(f"No matching LOB found in dropdown for code: {lob_code}")
    
    # ================= FILE UPLOAD =================


    # Force correct order
    ordered_files = current_term_files + prior_term_files + other_files

    #-----------------------------------------------------------------------------------------

    if not current_term_files:
        error_msg = "Current Term Policy not found"

        update_tracker(
            reference_id=record["Reference ID"],
            status="Error",
            error=error_msg
        )

        return None
    
    premium_value = None

    ct_file_path = os.path.join(folder_path, current_term_files[0])
    try:
        premium_value = extract_premium_from_pdf(ct_file_path)
    except Exception as e:
        print("Premium extraction failed:", e)
        premium_value = None

    print(f"Premium Extracted → {premium_value}")

    update_tracker(
        reference_id=record["Reference ID"],
        premium=premium_value
    )
    
    # ===== ERROR IF PREMIUM NOT FOUND =====

    if premium_value is None:

        error_msg = "Premium not found in Current Term Policy PDF"

        print(error_msg)

        update_tracker(
            reference_id=record["Reference ID"],
            status="Error",
            error=error_msg
        )

        return None
    
    await page.locator("#checklist").click()
    await page.get_by_role("listbox").wait_for()

    csr_type = "CSR Plus"

    if premium_value > 5000:
        csr_type = "CSR Pro"

    #await page.locator("li[role='option']", has_text=csr_type).click()
    await page.get_by_role("option", name=csr_type, exact=True).click()

    print(f"Checklist Type Selected → {csr_type}")

    update_tracker(
        reference_id=record["Reference ID"],
        csr_type=csr_type
    )
#------------------------------------------------------------------------------------------

    # ================= UPLOAD LOOP =================
    for file in ordered_files:

        file_lower = file.lower()
        file_path = os.path.join(folder_path, file)

        # ===== CURRENT TERM =====
        if file in current_term_files:
            print(f"Uploading to Current Term → {file}")
            label = page.locator("p:has-text('Current Term Policy')")
            section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
            await section.locator("input[type='file']").set_input_files(file_path)

            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1500)

        # ===== PRIOR TERM =====
        elif file in prior_term_files:
            print(f"Uploading to Prior Term → {file}")
            label = page.locator("p:has-text('Prior Term Policy')")
            section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
            await section.locator("input[type='file']").set_input_files(file_path)

        # ===== OTHER DOCUMENTS =====
        else:

            if "endorsement" in file_lower:
                label_text = "Endorsement"

            elif "quote" in file_lower or "qte" in file_lower:
                label_text = "Carrier Quote"

            elif "proposal" in file_lower:
                label_text = "Proposal"

            elif "accord" in file_lower or "application" in file_lower or "app" in file_lower:
                label_text = "Acord Application"

            elif "schedule" in file_lower:
                label_text = "Schedule"

            elif "binder" in file_lower:
                label_text = "Binder"

            else:
                print(f"Not matched → {file}")
                continue

            print(f"Uploading to {label_text} → {file}")

            label = page.locator(f"p:has-text('{label_text}')")
            await label.scroll_into_view_if_needed()

            section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")

            await section.locator("input[type='file']").set_input_files(file_path)


    # Wait for dialog while clicking the button
    # async with page.expect_event("dialog", timeout=40000) as dialog_info:
    #     await page.get_by_role("button", name="Generate Checklist").click()
    #     #await page.locator("button:has-text('Generate Checklist')").click()

    # dialog = await dialog_info.value

    # message = dialog.message
    # print("Popup message:", message)

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

    # # Extract Job ID
    # match = re.search(r"Job ID:\s*(\S+)", message)
    # job_id = match.group(1) if match else None

    # if not job_id:
    #     error_msg = "Job ID not generated"

    #     update_tracker(
    #         reference_id=record["Reference ID"],
    #         status="Error",
    #         error=error_msg
    #     )

    #     return None

    # print("Job ID:", job_id)

    # await page.wait_for_timeout(3000)

    # await dialog.accept()

    # print(f"Job Created Successfully → {job_id}")

    # ================= CSR UPLOAD =================

    await page.wait_for_timeout(5000)


    csr_btn = page.get_by_role("button", name="CSR Upload")

    await csr_btn.wait_for(state="visible", timeout=20000)
    await csr_btn.click()

    # await page.get_by_role("button", name="CSR Upload").click()
    await page.wait_for_timeout(10000)

    # return job_id

# ================= MAIN FUNCTION =================


async def run_istudio():

    config = ConfigParser()
    config.read(CONFIG_PATH)

    browser_name = config.get("ThomsoniStudio", "browser")
    url = config.get("ThomsoniStudio", "Link")
    username = config.get("ThomsoniStudio", "User_ID")
    password = config.get("ThomsoniStudio", "Password")

    # Crash recovery
    reset_in_progress()

    lob_mapping = load_lob_mapping()
    pending_df = get_pending_jobs()

    if pending_df.empty:
        print("No Pending Jobs Found")
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

                    print(f"\nProcessing {ref_id} | Attempt {attempt}")

                    job_id = await create_job(page, row, lob_mapping)

                    if job_id is None:
                        print(f"Skipping {ref_id} due to validation error")
                        update_tracker(
                            reference_id=ref_id,
                            status="Error",
                            error="Job ID not generated"
                        )
                        break

                    update_tracker(ref_id, job_id=job_id, status="Completed")

                    break   # Success → Exit retry loop

                except Exception as e:

                    print(f"Attempt {attempt} Failed → {ref_id}")
                    print(str(e))

                    if attempt == MAX_RETRIES:
                        print(f"Max retries reached → {ref_id}")
                        update_tracker(ref_id, status="Error")
                        break

                    attempt += 1

                    await page.wait_for_timeout(10000)
                    await page.get_by_role("button", name="CSR Upload").click()
                    await page.wait_for_timeout(10000)

                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)

                    # Optional: reload page before retry
                    await page.reload()

        print("\nAll Jobs Processed")

        try:
            print("Logging out...")

            profile_btn = page.locator("svg[data-testid='KeyboardArrowDownIcon']").first
            await profile_btn.click()

            logout_btn = page.get_by_role("menuitem", name="Sign Out")
            await logout_btn.click()

            print("Logout Successful")

        except Exception as e:
            print("Logout failed:", str(e))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_istudio())





#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




#####################################################################################################################################################################################

# #------------------WITH LOGGER---------------------# 

# import asyncio
# import re
# from playwright.async_api import async_playwright
# from configparser import ConfigParser
# import pandas as pd
# import os
# from datetime import datetime

# # ================= PATH CONFIG =================

# BASE_FOLDER = r"C:\Users\vijay_m\OneDrive - Exdion Solutions Pvt. Ltd.-70692290\Documents\Project_Job_Creation\Thomson"

# TRACKER_PATH = os.path.join(BASE_FOLDER, "Thomson_Tracker.xlsx")
# LOB_MASTER_PATH = os.path.join(BASE_FOLDER, "Lob_Mapping.xlsx")
# PDF_BASE_FOLDER = os.path.join(BASE_FOLDER, "Job_Creation")
# CONFIG_PATH = os.path.join(BASE_FOLDER, "Config.ini")

# # ================= LOGGING SETUP =================
# # from logging.handlers import RotatingFileHandler

# # LOG_FOLDER = os.path.join(BASE_FOLDER, "Logs")
# # os.makedirs(LOG_FOLDER, exist_ok=True)

# # log_file = os.path.join(
# #     LOG_FOLDER,
# #     f"Job_Creation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
# # )

# # logging.basicConfig(
# #     level=logging.INFO,
# #     format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
# #     datefmt="%Y-%m-%d %H:%M:%S",   # removes milliseconds
# #     handlers=[
# #         RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5),
# #         logging.StreamHandler()
# #     ]
# # )
# #---------------------------------------------------
# logger = logging.getLogger(__name__)
# #-------------------------------------------------------

# MAX_RETRIES = 3
# RETRY_DELAY = 5

# # ================= LOAD LOB MAPPING =================


# def load_lob_mapping():
#     df_lob = pd.read_excel(LOB_MASTER_PATH)

#     df_lob["LOB_CODE"] = df_lob["LOB_CODE"].astype(str).str.strip()
#     df_lob["LOB_NAME"] = df_lob["LOB_NAME"].astype(str).str.strip()

#     mapping = {}

#     for _, row in df_lob.iterrows():
#         code = row["LOB_CODE"]
#         name = row["LOB_NAME"]

#         if code not in mapping:
#             mapping[code] = []

#         mapping[code].append(name)

#     return mapping

# # ================= CRASH RECOVERY =================

# def reset_in_progress():
#     df = pd.read_excel(TRACKER_PATH)

#     if "Status" in df.columns:
#         df.loc[df["Status"] == "In Progress", "Status"] = "Pending"

#     df.to_excel(TRACKER_PATH, index=False)
#     logger.info("Reset any In Progress jobs back to Pending")

# # ================= READ PENDING JOBS =================

# def get_pending_jobs():
#     if not os.path.exists(TRACKER_PATH):
#         print("Tracker file not found")
#         return pd.DataFrame()

#     df = pd.read_excel(TRACKER_PATH)

#     if df.empty:
#         return pd.DataFrame()

#     pending = df[df["Status"] == "Pending"].copy()
#     logger.info(f"Total Pending Jobs: {len(pending)}")

#     return pending

# # ================= UPDATE TRACKER =================

# def update_tracker(reference_id, job_id=None, status=None, error=None):

#     df = pd.read_excel(TRACKER_PATH)

#     # if "Job ID" in df.columns:
#     #     df["Job ID"] = df["Job ID"].astype("string")

#     # if "Status" in df.columns:
#     #     df["Status"] = df["Status"].astype("string")

#     # Ensure correct column types
#     for col in ["Job ID", "Status", "Error"]:
#         if col in df.columns:
#             df[col] = df[col].astype("string")

#     idx = df.index[df["Reference ID"] == reference_id]

#     if idx.empty:
#         print(f"Reference ID not found -> {reference_id}")
#         return

#     row_index = idx[0]

#     if job_id is not None:
#         df.at[row_index, "Job ID"] = str(job_id)

#     if status is not None:
#         df.at[row_index, "Status"] = str(status)

#     if error is not None:
#         df.at[row_index, "Error"] = str(error)

#     df.at[row_index, "Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     df.to_excel(TRACKER_PATH, index=False)

#     print(f"Tracker Updated -> {reference_id} | {status} | {error}")

# # ================= LOGIN FUNCTION =================

# async def login(page, url, username, password):

#     await page.goto(url, timeout=60000)

#     await page.locator("input[name='username']").fill(username)
#     await page.locator("input[name='password']").fill(password)
#     await page.locator("input[name='termsAccepted']").check()

#     await page.get_by_role("button", name="Submit").click()

#     print("Login Successful")

#     await page.get_by_role("button", name="Take me there").first.click()


# # ================= CREATE JOB FUNCTION =================

# async def create_job(page, record, lob_mapping):

#     print(f"\nCreating Job -> {record['Reference ID']}")

#     # ================= Select Broker =================

#     broker_name = "Thomson Smith and Leach Insurance"

#     await page.locator('div[role="combobox"]').first.click()
#     await page.wait_for_selector('ul[role="listbox"]', timeout=60000)
#     await page.locator(f'li[data-value="{broker_name}"]').click()
#     print(f"Broker Selected -> {broker_name}")


#     # ================= ACCOUNT MANAGER ---> Primary CSR =================

#     account_manager = str(record["Account Manager"]).strip()
#     parts = account_manager.split()
#     username = (parts[0][0] + parts[-1]).lower()
#     email = f"{username}@tslins.com"
#     print(f"Account_manager -> {account_manager}")
#     print(f"Selecting Primary CSR -> {email}")

#     await page.locator('div[role="combobox"]').nth(1).click()
#     await page.wait_for_selector('ul[role="listbox"]')
#     await page.get_by_role("option", name=email, exact=True).click()

#     await page.get_by_role("button", name="Save").click()

#     await page.get_by_role("tab", name="Marketed Renewal").click()


#     # ================= LOB SELECTION =================

#     lob_code = str(record["LOB"]).strip()

#     if lob_code not in lob_mapping:
#         raise Exception(f"LOB Code not found in LOB Master: {lob_code}")

#     possible_lob_names = lob_mapping[lob_code]

#     print(f"Trying LOB names -> {possible_lob_names}")

#     # Open dropdown
#     await page.locator("#coverage").click()
#     await page.get_by_role("listbox").wait_for()

#     options = page.get_by_role("option")
#     count = await options.count()

#     selected = False

#     for i in range(count):
#         option_text = (await options.nth(i).inner_text()).strip()

#         for lob_name in possible_lob_names:
#             if option_text.lower() == lob_name.strip().lower():
#                 await options.nth(i).click()
#                 print(f"LOB Selected -> {option_text}")
#                 selected = True
#                 break

#         if selected:
#             break

#     if not selected:
#         raise Exception(f"No matching LOB found in dropdown for code: {lob_code}")
    
#     await page.locator("#checklist").click()
#     await page.get_by_role("listbox").wait_for()
    
#     await page.locator("li[role='option']", has_text="CSR Plus").click()
#     print("Checklist Type Selected -> Lite_ExdionPOD")

#     folder_path = os.path.join(PDF_BASE_FOLDER, record["Reference ID"])

#     if os.path.exists(folder_path):

#         files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

#         NON_POLICY_KEYWORDS = [
#             "binder",
#             "quote",
#             "proposal",
#             "schedule",
#             "endorsement",
#             "accord",
#             "application"
#         ]

#         current_term_files = []
#         prior_term_files = []
#         other_files = []

#         # ================= CLASSIFY FILES =================
#         for file in files:
#             file_lower = file.lower()

#             is_current_term = False
#             is_prior_term = False

#             is_non_policy = any(word in file_lower for word in NON_POLICY_KEYWORDS)

#             # ---- Detect CT ----
#             if re.search(r"\b26[-_/]27\b", file_lower) and not is_non_policy:
#                 is_current_term = True

#             # ---- Detect PT ----
#             elif re.search(r"\b25[-_/]26\b", file_lower) and not is_non_policy:
#                 is_prior_term = True

#             # ---- Date Range Format ----
#             else:
#                 match = re.search(
#                     r"\d{1,2}-\d{1,2}-(\d{2})\s*to\s*\d{1,2}-\d{1,2}-(\d{2})",
#                     file_lower
#                 )

#                 if match and not is_non_policy:
#                     start_year = match.group(1)
#                     end_year = match.group(2)

#                     if start_year == "26" and end_year == "27":
#                         is_current_term = True
#                     elif start_year == "25" and end_year == "26":
#                         is_prior_term = True

#             if is_current_term:
#                 current_term_files.append(file)
#             elif is_prior_term:
#                 prior_term_files.append(file)
#             else:
#                 other_files.append(file)

#         # Force correct order
#         ordered_files = current_term_files + prior_term_files + other_files

#         # ================= UPLOAD LOOP =================
#         for file in ordered_files:

#             file_lower = file.lower()
#             file_path = os.path.join(folder_path, file)

#             # ===== CURRENT TERM =====
#             if file in current_term_files:
#                 print(f"Uploading to Current Term -> {file}")
#                 label = page.locator("p:has-text('Current Term Policy')")
#                 section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
#                 await section.locator("input[type='file']").set_input_files(file_path)

#                 await page.wait_for_load_state("networkidle")
#                 await page.wait_for_timeout(1500)

#             # ===== PRIOR TERM =====
#             elif file in prior_term_files:
#                 print(f"Uploading to Prior Term -> {file}")
#                 label = page.locator("p:has-text('Prior Term Policy')")
#                 section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
#                 await section.locator("input[type='file']").set_input_files(file_path)

#             # ===== OTHER DOCUMENTS =====
#             else:

#                 if "endorsement" in file_lower:
#                     label_text = "Endorsement"

#                 elif "quote" in file_lower:
#                     label_text = "Carrier Quote"

#                 elif "proposal" in file_lower:
#                     label_text = "Proposal"

#                 elif "accord" in file_lower or "application" in file_lower:
#                     label_text = "Acord Application"

#                 elif "schedule" in file_lower:
#                     label_text = "Schedule"

#                 elif "binder" in file_lower:
#                     label_text = "Binder"

#                 else:
#                     print(f"Not matched -> {file}")
#                     continue

#                 print(f"Uploading to {label_text} -> {file}")

#                 label = page.locator(f"p:has-text('{label_text}')")
#                 await label.scroll_into_view_if_needed()

#                 section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")

#                 await section.locator("input[type='file']").set_input_files(file_path)


#     # Wait for dialog while clicking the button
#     async with page.expect_event("dialog", timeout=40000) as dialog_info:
#         await page.get_by_role("button", name="Generate Checklist").click()
#         #await page.locator("button:has-text('Generate Checklist')").click()

#     dialog = await dialog_info.value

#     message = dialog.message
#     print("Popup message:", message)

#     # ===== HANDLE ERROR POPUP =====
#     if any(text in message.lower() for text in [
#         "Please choose", "Proposal", "ACORD Application", "Carrier Quote", "Binder"
#     ]):

#         error_msg = "Please choose Proposal or ACORD Application or Carrier Quote or Binder"

#         await dialog.accept()

#         update_tracker(
#             reference_id=record["Reference ID"],
#             status="Error",
#             error=error_msg
#         )

#         return None

#     # Extract Job ID
#     match = re.search(r"Job ID:\s*(\S+)", message)
#     job_id = match.group(1) if match else None

#     print("Job ID:", job_id)

#     await page.wait_for_timeout(3000)

#     await dialog.accept()

#     print(f"Job Created Successfully -> {job_id}")

#     await page.get_by_role("button", name="CSR Upload").click()
#     await page.wait_for_timeout(5000)

#     return job_id

# # ================= MAIN FUNCTION =================


# async def run_istudio():

#     config = ConfigParser()
#     config.read(CONFIG_PATH)

#     browser_name = config.get("ThomsoniStudio", "browser")
#     url = config.get("ThomsoniStudio", "Link")
#     username = config.get("ThomsoniStudio", "User_ID")
#     password = config.get("ThomsoniStudio", "Password")

#     # Crash recovery
#     reset_in_progress()

#     lob_mapping = load_lob_mapping()
#     pending_df = get_pending_jobs()

#     if pending_df.empty:
#         print("No Pending Jobs Found")
#         return

#     async with async_playwright() as p:

#         if browser_name.lower() == "chrome":
#             browser = await p.chromium.launch(channel="chrome", headless=False)
#         elif browser_name.lower() == "edge":
#             browser = await p.chromium.launch(channel="msedge", headless=False)
#         else:
#             raise Exception("Unsupported browser")

#         context = await browser.new_context()
#         page = await context.new_page()

#         await login(page, url, username, password)

#         # for _, row in pending_df.iterrows():

#         #     ref_id = row["Reference ID"]

#         #     try:
#         #         # Mark In Progress first
#         #         update_tracker(ref_id, status="In Progress")

#         #         # Create job
#         #         job_id = await create_job(page, row, lob_mapping)

#         #         # Mark Created
#         #         update_tracker(ref_id, job_id=job_id, status="Completed")

#         #     except Exception as e:
#         #         print(f"Error -> {ref_id}")
#         #         print(str(e))

#         #         update_tracker(ref_id, status="Error")

#         for _, row in pending_df.iterrows():

#             ref_id = row["Reference ID"]
#             attempt = 1

#             while attempt <= MAX_RETRIES:

#                 try:
#                     if attempt == 1:
#                         update_tracker(ref_id, status="In Progress")

#                     print(f"\nProcessing {ref_id} | Attempt {attempt}")

#                     job_id = await create_job(page, row, lob_mapping)

#                     if job_id is None:
#                         print(f"Skipping {ref_id} due to validation error")
#                         break

#                     update_tracker(ref_id, job_id=job_id, status="Completed")

#                     break   # Success -> Exit retry loop

#                 except Exception as e:

#                     print(f"Attempt {attempt} Failed -> {ref_id}")
#                     print(str(e))

#                     if attempt == MAX_RETRIES:
#                         print(f"Max retries reached -> {ref_id}")
#                         update_tracker(ref_id, status="Error")
#                         break

#                     attempt += 1

#                     await page.get_by_role("button", name="CSR Upload").click()
#                     await page.wait_for_timeout(5000)

#                     print(f"Retrying in {RETRY_DELAY} seconds...")
#                     await asyncio.sleep(RETRY_DELAY)

#                     # Optional: reload page before retry
#                     await page.reload()

#         print("\nAll Jobs Processed")

#         try:
#             print("Logging out...")

#             profile_btn = page.locator("svg[data-testid='KeyboardArrowDownIcon']").first
#             await profile_btn.click()

#             logout_btn = page.get_by_role("menuitem", name="Sign Out")
#             await logout_btn.click()

#             print("Logout Successful")

#         except Exception as e:
#             print("Logout failed:", str(e))

#         await browser.close()

# if __name__ == "__main__":
#     asyncio.run(run_istudio())
