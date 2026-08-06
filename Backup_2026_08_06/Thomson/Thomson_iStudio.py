import asyncio
import re
from playwright.async_api import async_playwright
from configparser import ConfigParser
import pandas as pd
import os
from datetime import datetime

# ================= PATH CONFIG =================

config = ConfigParser()
config.read("c:/Users/vijay_m/OneDrive - Exdion Solutions Pvt. Ltd.-70692290/Documents/Project_Job_Creation/Thomson/config.ini")
BASE_FOLDER = config.get("PATHS", "BASE_FOLDER")
TRACKER_PATH = os.path.join(BASE_FOLDER, "Thomson_Tracker.xlsx")
LOB_MASTER_PATH = os.path.join(BASE_FOLDER, "Lob_Mapping.xlsx")
PDF_BASE_FOLDER = os.path.join(BASE_FOLDER, "Job_Creation")
CONFIG_PATH = os.path.join(BASE_FOLDER, "Config.ini")

os.makedirs(BASE_FOLDER, exist_ok=True)
os.makedirs(PDF_BASE_FOLDER, exist_ok=True)

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

def update_tracker(reference_id, job_id=None, status=None, error=None, csr_type=None):

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

    if "CSR Type" not in df.columns:
        df["CSR Type"] = ""

    if csr_type is not None:
        df.at[row_index, "CSR Type"] = csr_type

    df.at[row_index, "Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df.to_excel(TRACKER_PATH, index=False)

    updates = []

    if csr_type is not None:
        updates.append(f"CSR={csr_type}")

    if status is not None:
        updates.append(f"Status={status}")

    if error is not None:
        updates.append(f"Error={error}")

    print(f"Tracker Updated → {reference_id} | " + " | ".join(updates))


#======================= EMAIL ATTACHMENT ========================#

from datetime import datetime
import os
import pandas as pd

def generate_daily_report():

    if not os.path.exists(TRACKER_PATH):
        raise Exception("Tracker file not found")

    df = pd.read_excel(TRACKER_PATH)

    df["Last Updated"] = pd.to_datetime(df["Last Updated"], errors="coerce")

    df["Status"] = df["Status"].astype(str).str.strip().str.capitalize()

    today_date = datetime.now().date()
    today_str = datetime.now().strftime("%Y-%m-%d")

    today = pd.Timestamp.today().normalize()
    tomorrow = today + pd.Timedelta(days=1)

    filtered = df[
        (df["Last Updated"] >= today) &
        (df["Last Updated"] < tomorrow)
    ].copy()

    # if filtered.empty:
    #     raise Exception(f"No jobs found for today: {today_date}")
    
    
    if filtered.empty:
        df_valid_dates = df["Last Updated"].dropna()

        if df_valid_dates.empty:
            date_str = "No Data"
        else:
            date_str = df_valid_dates.max().strftime("%Y-%m-%d")

        report_summary = f"""\
    Today Job Report Status

    Date: {date_str}

    No jobs found.
    """
        print(report_summary)

        return report_summary, None

    filtered = filtered.sort_values(by="Reference ID")

    filtered["Date"] = pd.to_datetime(filtered["Date"], errors="coerce")

    run_dates = (
        filtered["Date"]
        .dropna()
        .dt.strftime("%Y-%m-%d")
        .unique()
    )

    run_dates = sorted(run_dates)

    if len(run_dates) == 1:
        date_label = "Date"
        date_str = run_dates[0]
    else:
        date_label = "Date(s)"
        date_str = ", ".join(run_dates) if len(run_dates) else "No Data"


    total = len(filtered)
    completed = len(filtered[filtered["Status"] == "Completed"])
    failed = len(filtered[filtered["Status"] == "Error"])
    pending = len(filtered[filtered["Status"] == "Pending"])

    success_rate = round((completed / total) * 100, 2) if total else 0

    daily_folder = os.path.join(BASE_FOLDER, "Daily_Report")
    os.makedirs(daily_folder, exist_ok=True)

    report_path = os.path.join(
        daily_folder,
        f"Carroll_Report_{today_str}.xlsx"
    )

    filtered.to_excel(report_path, index=False)

    print(f"Report saved: {report_path}")

    report_summary = f"""\
    Today Job Report Status

    {date_label}: {date_str}

    Total Jobs   : {total}
    Completed    : {completed}
    Failed       : {failed}
    Pending      : {pending}
    Success Rate : {success_rate:.2f}%
    """

    return report_summary, report_path


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

    valid_doc_uploaded = False

    # ================= DETECT FILE TYPES =================

    if os.path.exists(folder_path):

        files = [f for f in os.listdir(folder_path) if f.lower().endswith((".pdf", ".docx", ".xlsx"))]

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

            # Check NON-POLICY keywords (these should block CT/PT)
            is_non_policy = any(word in file_lower for word in NON_POLICY_KEYWORDS)

            #  Step 1: If NON-POLICY → directly classify as OTHER
            if is_non_policy:
                other_files.append(file)
                continue

            # # ---- Detect CT ----
            # if re.search(r"\b26[-_/]27\b", file_lower):
            #     is_current_term = True

            # # ---- Detect PT ----
            # elif re.search(r"\b25[-_/]26\b", file_lower):
            #     is_prior_term = True

            # ---- Detect CT ----
            if (
                re.search(r"\b26[-_/]27\b", file_lower)
                or re.search(r"20?26.*20?27", file_lower)
            ):
                is_current_term = True

            # ---- Detect PT ----
            elif (
                re.search(r"\b25[-_/]26\b", file_lower)
                or re.search(r"20?25.*20?26", file_lower)
            ):
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
    
        # ================= VALIDATION =================

    has_ct = len(current_term_files) > 0
    has_pt = len(prior_term_files) > 0

    if len(other_files) == 0:
        renewal_type = "Automatic"
    else:
        renewal_type = "Marketed"

    print(f"Renewal Type: {renewal_type}")
    print(f"CT: {has_ct}, PT: {has_pt}, Other: {len(other_files)}")

    if renewal_type == "Automatic":
        if not (has_ct and has_pt):
            raise Exception("Automatic Renewal requires BOTH CT and PT")

    # ================= TAB =================

    tab = page.get_by_role("tab", name=f"{renewal_type} Renewal")
    await tab.wait_for()
    await tab.click()

    await page.wait_for_load_state("networkidle")

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
    
    premium_value = record.get("Premium")

    # Clean Excel currency values
    if premium_value is not None:
        premium_value = str(premium_value)\
            .replace("$", "")\
            .replace(",", "")\
            .strip()

    try:
        premium_value = float(premium_value)
    except ValueError:
        premium_value = None

    print(f"Premium Read From Excel → {premium_value}")

    # ===== ERROR IF PREMIUM NOT FOUND =====

    if premium_value is None:

        error_msg = "Premium value missing/invalid in Excel"

        print(error_msg)

        update_tracker(
            reference_id=record["Reference ID"],
            status="Error",
            error=error_msg
        )

        return None

    await page.locator("#checklist").click()
    await page.get_by_role("listbox").wait_for()

    # CSR Logic
    if premium_value < 5000:
        csr_type = "CSR Pro"
    else:
        csr_type = "CSR Plus"

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

            if "endorsement" in file_lower or "endt" in file_lower:
                label_text = "Endorsement"

            elif "quote" in file_lower or "qte" in file_lower or "quotation" in file_lower:
                label_text = "Carrier Quote"
                valid_doc_uploaded = True

            elif "proposal" in file_lower:
                label_text = "Proposal"
                valid_doc_uploaded = True

            elif "accord" in file_lower or "application" in file_lower or "app" in file_lower:
                label_text = "Acord Application"
                valid_doc_uploaded = True

            elif "schedule" in file_lower:
                label_text = "Schedule"
                valid_doc_uploaded = True

            elif "binder" in file_lower or "bind" in file_lower:
                label_text = "Binder"
                valid_doc_uploaded = True

            else:
                print(f"Not matched -> {file}")
                continue

            print(f"Uploading to {label_text} → {file}")

            label = page.locator(f"p:has-text('{label_text}')")
            await label.scroll_into_view_if_needed()

            section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")

            await section.locator("input[type='file']").set_input_files(file_path)

    if renewal_type == "Marketed":
        if not has_ct:
            raise Exception("Marketed requires Current Term document")

        if not valid_doc_uploaded:
            raise Exception("Marketed requires at least one valid doc (Proposal/Quote/Application/Binder)")



    try:

        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)

        async with page.expect_event("dialog", timeout=120000) as dialog_info:
            await page.get_by_role("button", name="Generate Checklist").click()

        dialog = await dialog_info.value

        message = dialog.message
        print("Popup message: ", message)

    except Exception as e:
        raise Exception(f"No popup received after Generate Checklist: {str(e)}")

    #error_msg = "Please choose Proposal or ACORD Application or Carrier Quote or Binder"
    msg_lower = message.lower()
    if "please choose" in msg_lower:
        await dialog.accept()
        raise Exception("Validation Error: Required documents missing")

    # Extract Job ID
    match = re.search(r"Job ID:\s*(\S+)", message)
    #match = re.search(r"Job ID:\s*([a-zA-Z0-9]+)", message)

    job_id = match.group(1) if match else None

    print("Job ID: ", job_id)

    if not job_id:
        await dialog.accept()
        raise Exception("Job ID not found in popup")

    update_tracker(ref_id, job_id=job_id, status="Completed")

    await page.wait_for_timeout(3000)

    await dialog.accept()

    print(f"Job Created Successfully -> {job_id}")

    await page.wait_for_url("**jobcsrlisting**", timeout=30000)
    await page.get_by_placeholder("Search by Job ID").wait_for(timeout=20000)

    try:
        jobs = page.get_by_text("Jobs", exact=True)
        await jobs.wait_for(state="visible", timeout=5000)
        await jobs.click()

        upload_docs = page.get_by_text("Upload Documents", exact=True)
        await upload_docs.wait_for(state="visible", timeout=5000)
        await upload_docs.click()

    except Exception as nav_err:
        print("Navigation warning:", str(nav_err))

    return job_id


# ================= MAIN FUNCTION =================


async def run_istudio():

    print("ISTUDIO started")

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

                    if job_id:
                        print(f"Completed -> {ref_id}")
                        break
                    else:
                        raise Exception("Job ID not Generated")

                except Exception as e:

                    print(f"Attempt {attempt} Failed → {ref_id}")
                    print(str(e))

                    #----------------------------------------------------------
                    # ===== CLOSE POPUP IF EXISTS =====
                    try:
                        await page.keyboard.press("Escape")
                    except:
                        pass

                    # ===== RELOAD PAGE TO CLEAR OLD UPLOADS =====
                    try:
                        print("Reloading page to clear uploads...")
                        await page.reload(wait_until="networkidle")
                    except Exception as reload_err:
                        print("Reload failed:", str(reload_err))
                    #----------------------------------------------------------

                    df = pd.read_excel(TRACKER_PATH)
                    existing_job = df.loc[df["Reference ID"] == ref_id, "Job ID"].values

                    if len(existing_job) > 0 and pd.notna(existing_job[0]):
                        print("Job ID already exists → marking Completed")
                        update_tracker(ref_id, status="Completed")
                        break

                    if attempt == MAX_RETRIES:
                        print(f"Max retries reached -> {ref_id}")
                        update_tracker(ref_id, status="Error", error=str(e))
                        break

                    attempt += 1

                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)

                    if page.is_closed():
                        print("Page closed → reopening browser page")
                        page = await context.new_page()
                        await login(page, url, username, password)
                    # else:
                    #     print("Reloading page")
                    #     await page.reload()
                    #     await page.wait_for_load_state("networkidle")

                    print("Navigating to Jobs → Upload Documents")

                    await page.wait_for_timeout(5000)

                    jobs = page.get_by_text("Jobs", exact=True)
                    await jobs.wait_for(state="visible", timeout=15000)
                    await jobs.click()

                    upload_docs = page.get_by_text("Upload Documents", exact=True)
                    await upload_docs.wait_for(state="visible")
                    await upload_docs.click()

        print("\nAll Jobs Processed")

        try:
            print("Logging out...")

            profile_btn = page.get_by_text("Divya", exact=True)
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


