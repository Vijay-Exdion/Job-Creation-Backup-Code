# ##############################------------------ Old Code ---------------------############################### 

# import asyncio
# import re
# from playwright.async_api import async_playwright
# from configparser import ConfigParser
# import pandas as pd
# import os
# from datetime import datetime

# # ================= PATH CONFIG =================

# BASE_FOLDER = r"C:\Users\vijay_m\OneDrive - Exdion Solutions Pvt. Ltd.-70692290\Documents\Project_Job_Creation\carroll"

# TRACKER_PATH = os.path.join(BASE_FOLDER, "Carroll_Tracker.xlsx")
# LOB_MASTER_PATH = os.path.join(BASE_FOLDER, "Lob_Mapping.xlsx")
# PDF_BASE_FOLDER = os.path.join(BASE_FOLDER, "Job_Creation")
# CONFIG_PATH = os.path.join(BASE_FOLDER, "Config.ini")

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
#     print("Reset any In Progress jobs back to Pending")

# # ================= READ PENDING JOBS =================

# def get_pending_jobs():
#     if not os.path.exists(TRACKER_PATH):
#         print("Tracker file not found")
#         return pd.DataFrame()

#     df = pd.read_excel(TRACKER_PATH)

#     if df.empty:
#         return pd.DataFrame()

#     pending = df[df["Status"] == "Pending"].copy()
#     print(f"Total Pending Jobs: {len(pending)}")

#     return pending

# # ================= UPDATE TRACKER =================

# def update_tracker(reference_id, job_id=None, status=None, error=None):

#     df = pd.read_excel(TRACKER_PATH)

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
#     await page.get_by_role("button", name="Jobs").click()
#     await page.get_by_role("button", name="Upload Documents").click()

#     print("Navigated to Upload Documents")


# # ================= CREATE JOB FUNCTION =================

# async def create_job(page, record, lob_mapping):

#     ref_id = record["Reference ID"]
#     print(f"Creating Job -> {ref_id}")

#     folder_path = os.path.join(PDF_BASE_FOLDER, ref_id)

#     current_term_files = []
#     prior_term_files = []
#     other_files = []

#     # ================= DETECT FILE TYPES =================

#     if os.path.exists(folder_path):

#         files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

#         NON_POLICY_KEYWORDS = [
#             "binder",
#             "quote",
#             "proposal",
#             "schedule",
#             "endorsement",
#             "accord",
#             "application",
#             "app",
#             "endt",
#             "accord"
#         ]
    
#     # ================= CLASSIFY FILES =================

#         # for file in files:
#         #     file_lower = file.lower()

#         #     is_current_term = False
#         #     is_prior_term = False

#         #     is_non_policy = any(word in file_lower for word in NON_POLICY_KEYWORDS)

#         #     # ---- Detect CT ----
#         #     if re.search(r"\b26[-_/]27\b", file_lower) and not is_non_policy:
#         #         is_current_term = True

#         #     # ---- Detect PT ----
#         #     elif re.search(r"\b25[-_/]26\b", file_lower) and not is_non_policy:
#         #         is_prior_term = True

#         #     # ---- Date Range Format ----
#         #     else:
#         #         match = re.search(
#         #             r"\d{1,2}-\d{1,2}-(\d{2})\s*to\s*\d{1,2}-\d{1,2}-(\d{2})",
#         #             file_lower
#         #         )

#         #         if match and not is_non_policy:
#         #             start_year = match.group(1)
#         #             end_year = match.group(2)

#         #             if start_year == "26" and end_year == "27":
#         #                 is_current_term = True
#         #             elif start_year == "25" and end_year == "26":
#         #                 is_prior_term = True

#         #     if is_current_term:
#         #         current_term_files.append(file)
#         #     elif is_prior_term:
#         #         prior_term_files.append(file)
#         #     else:
#         #         other_files.append(file)


#         for file in files:
#             file_lower = file.lower()

#             is_current_term = False
#             is_prior_term = False

#             # Check NON-POLICY keywords (these should block CT/PT)
#             is_non_policy = any(word in file_lower for word in NON_POLICY_KEYWORDS)

#             #  Step 1: If NON-POLICY → directly classify as OTHER
#             if is_non_policy:
#                 other_files.append(file)
#                 continue

#             # ---- Detect CT ----
#             if re.search(r"\b26[-_/]27\b", file_lower):
#                 is_current_term = True

#             # ---- Detect PT ----
#             elif re.search(r"\b25[-_/]26\b", file_lower):
#                 is_prior_term = True

#             # ---- Date Range Format ----
#             else:
#                 match = re.search(
#                     r"\d{1,2}-\d{1,2}-(\d{2})\s*to\s*\d{1,2}-\d{1,2}-(\d{2})",
#                     file_lower
#                 )

#                 if match:
#                     start_year = match.group(1)
#                     end_year = match.group(2)

#                     if start_year == "26" and end_year == "27":
#                         is_current_term = True
#                     elif start_year == "25" and end_year == "26":
#                         is_prior_term = True

#             # ---- Classification ----
#             if is_current_term:
#                 current_term_files.append(file)

#             elif is_prior_term:
#                 prior_term_files.append(file)

#             else:
#                 other_files.append(file)



    
#     # ================= TAB SELECTION =================

#     if len(other_files) == 0:

#         print("Only CT & PT found -> Automatic Renewal")

#         tab = page.get_by_role("tab", name="Automatic Renewal")
#         await tab.wait_for(timeout=20000)
#         await tab.click()

#     else:

#         print("Other documents found -> Marketed Renewal")

#         tab = page.get_by_role("tab", name="Marketed Renewal")
#         await tab.wait_for(timeout=20000)
#         await tab.click()

#     await page.wait_for_timeout(2000)

#     # ================= SELECT LOB =================

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
    

#     # ================= CHECKLIST =================

#     await page.locator("#checklist").click()
#     await page.get_by_role("listbox").wait_for()

#     await page.locator("li[role='option']", has_text="Lite_ExdionPOD").click()

#     print("Checklist Selected -> Lite_ExdionPOD")

#     # ================= FILE UPLOAD =================

#     ordered_files = current_term_files + prior_term_files + other_files

#     for file in ordered_files:

#         file_lower = file.lower()
#         file_path = os.path.join(folder_path, file)

#         # ===== CURRENT TERM =====
#         if file in current_term_files:
#             print(f"Uploading to Current Term -> {file}")
#             label = page.locator("p:has-text('Current Term Policy')")
#             section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
#             await section.locator("input[type='file']").set_input_files(file_path)

#             await page.wait_for_load_state("networkidle")
#             await page.wait_for_timeout(1500)

#         # ===== PRIOR TERM =====
#         elif file in prior_term_files:
#             print(f"Uploading to Prior Term -> {file}")
#             label = page.locator("p:has-text('Prior Term Policy')")
#             section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
#             await section.locator("input[type='file']").set_input_files(file_path)

#         # ===== OTHER DOCUMENTS =====
#         else:

#             if "endorsement" in file_lower or "endt" in file_lower:
#                 label_text = "Endorsement"

#             elif "quote" in file_lower or "qte" in file_lower or "quotation" in file_lower:
#                 label_text = "Carrier Quote"

#             elif "proposal" in file_lower:
#                 label_text = "Proposal"

#             elif "accord" in file_lower or "application" in file_lower or "app" in file_lower:
#                 label_text = "Acord Application"

#             elif "schedule" in file_lower:
#                 label_text = "Schedule"

#             elif "binder" in file_lower or "bind" in file_lower:
#                 label_text = "Binder"

#             else:
#                 print(f"Not matched -> {file}")
#                 continue

#             print(f"Uploading to {label_text} -> {file}")

#             label = page.locator(f"p:has-text('{label_text}')")
#             await label.scroll_into_view_if_needed()

#             section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")

#             await section.locator("input[type='file']").set_input_files(file_path)


#     # async with page.expect_event("dialog", timeout=40000) as dialog_info:
#     #     await page.get_by_role("button", name="Generate Checklist").click()

#     # dialog = await dialog_info.value

#     # message = dialog.message
#     # print("Popup message: %s", message)

#     # # ===== HANDLE ERROR POPUP =====
#     # if any(text in message.lower() for text in [
#     #     "Please choose", "Proposal", "ACORD Application", "Carrier Quote", "Binder"
#     # ]):

#     #     error_msg = "Please choose Proposal or ACORD Application or Carrier Quote or Binder"

#     #     await dialog.accept()

#     #     update_tracker(
#     #         reference_id=record["Reference ID"],
#     #         status="Error",
#     #         error=error_msg
#     #     )

#     #     return None


#     # try:
#     #     dialog = await dialog_info.value
#     #     message = dialog.message.lower()

#     #     print(f"Popup message -> {message}")

#     #     if "please choose" in message:
#     #         await dialog.accept()
#     #         return None

#     # except:
#     #     # fallback if modal popup
#     #     if await page.locator("text=Please choose").is_visible():
#     #         print("Validation modal detected")

#     #         await page.get_by_role("button", name="OK").click()

#     #         return None

#     # # Extract Job ID
#     # match = re.search(r"Job ID:\s*(\S+)", message)
#     # job_id = match.group(1) if match else None

#     # print("Job ID: %s", job_id)

#     # await page.wait_for_timeout(3000)

#     # await dialog.accept()

#     # print(f"Job Created Successfully -> {job_id}")


#     await page.wait_for_timeout(10000)

#     await page.get_by_role("button", name="Jobs").click()
#     await page.get_by_role("button", name="Upload Documents").click()
#     await page.wait_for_timeout(5000)

#     await page.get_by_role("tab", name="Marketed Renewal").wait_for()

#     # return job_id

# # ================= MAIN FUNCTION =================

# async def run_istudio():

#     print("ISTUDIO started")

#     config = ConfigParser()
#     config.read(CONFIG_PATH)

#     browser_name = config.get("CarrolliStudio", "browser")
#     url = config.get("CarrolliStudio", "Link")
#     username = config.get("CarrolliStudio", "User_ID")
#     password = config.get("CarrolliStudio", "Password")

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

#                     await page.wait_for_timeout(20000)
#                     await page.get_by_role("button", name="Jobs").click()
#                     await page.get_by_role("button", name="Upload Documents").click()
#                     await page.wait_for_timeout(5000)

#                     print(f"Retrying in {RETRY_DELAY} seconds...")
#                     await asyncio.sleep(RETRY_DELAY)

#                     # Optional: reload page before retry
#                     if not page.is_closed():
#                         await page.reload()

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

# -------------------------------------------------##########################--------------NEW CODE---------------------##################################--------------------------------------------------------

#-----------------------------------------------------------------------------------   Good Working Code  ----------------------------------------------------------------------------------

# import asyncio
# import re
# from playwright.async_api import async_playwright
# from configparser import ConfigParser
# import pandas as pd
# import os
# from datetime import datetime

# # ================= PATH CONFIG =================

# BASE_FOLDER = r"C:\Users\vijay_m\OneDrive - Exdion Solutions Pvt. Ltd.-70692290\Documents\Project_Job_Creation\carroll"

# TRACKER_PATH = os.path.join(BASE_FOLDER, "Carroll_Tracker.xlsx")
# LOB_MASTER_PATH = os.path.join(BASE_FOLDER, "Lob_Mapping.xlsx")
# PDF_BASE_FOLDER = os.path.join(BASE_FOLDER, "Job_Creation")
# CONFIG_PATH = os.path.join(BASE_FOLDER, "Config.ini")


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
#     print("Reset any In Progress jobs back to Pending")

# # ================= READ PENDING JOBS =================

# def get_pending_jobs():
#     if not os.path.exists(TRACKER_PATH):
#         print("Tracker file not found")
#         return pd.DataFrame()

#     df = pd.read_excel(TRACKER_PATH)

#     if df.empty:
#         return pd.DataFrame()

#     pending = df[df["Status"] == "Pending"].copy()
#     print(f"Total Pending Jobs: {len(pending)}")

#     return pending

# # ================= UPDATE TRACKER =================

# def update_tracker(reference_id, job_id=None, status=None, error=None):

#     df = pd.read_excel(TRACKER_PATH)

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
#     await page.get_by_text("Jobs", exact=True).click()

#     upload_docs = page.get_by_text("Upload Documents", exact=True)
#     await upload_docs.wait_for(state="visible")
#     await upload_docs.click()
    
# # ================= CREATE JOB FUNCTION =================

# async def create_job(page, record, lob_mapping):

#     ref_id = record["Reference ID"]
#     print(f"Creating Job -> {ref_id}")

#     folder_path = os.path.join(PDF_BASE_FOLDER, ref_id)

#     current_term_files = []
#     prior_term_files = []
#     other_files = []

#     valid_doc_uploaded = False

#     # ================= DETECT FILE TYPES =================

#     if os.path.exists(folder_path):

#         files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

#         NON_POLICY_KEYWORDS = [
#             "binder",
#             "quote",
#             "proposal",
#             "schedule",
#             "endorsement",
#             "accord",
#             "application",
#             "app",
#             "endt",
#             "accord"
#         ]
    
#     # ================= CLASSIFY FILES =================

#         for file in files:
#             file_lower = file.lower()

#             is_current_term = False
#             is_prior_term = False

#             # Check NON-POLICY keywords (these should block CT/PT)
#             is_non_policy = any(word in file_lower for word in NON_POLICY_KEYWORDS)

#             #  Step 1: If NON-POLICY → directly classify as OTHER
#             if is_non_policy:
#                 other_files.append(file)
#                 continue

#             # ---- Detect CT ----
#             if re.search(r"\b26[-_/]27\b", file_lower):
#                 is_current_term = True

#             # ---- Detect PT ----
#             elif re.search(r"\b25[-_/]26\b", file_lower):
#                 is_prior_term = True

#             # ---- Date Range Format ----
#             else:
#                 match = re.search(
#                     r"\d{1,2}-\d{1,2}-(\d{2})\s*to\s*\d{1,2}-\d{1,2}-(\d{2})",
#                     file_lower
#                 )

#                 if match:
#                     start_year = match.group(1)
#                     end_year = match.group(2)

#                     if start_year == "26" and end_year == "27":
#                         is_current_term = True
#                     elif start_year == "25" and end_year == "26":
#                         is_prior_term = True

#             # ---- Classification ----
#             if is_current_term:
#                 current_term_files.append(file)

#             elif is_prior_term:
#                 prior_term_files.append(file)

#             else:
#                 other_files.append(file)
    
#     # ================= VALIDATION =================

#     has_ct = len(current_term_files) > 0
#     has_pt = len(prior_term_files) > 0

#     if len(other_files) == 0:
#         renewal_type = "Automatic"
#     else:
#         renewal_type = "Marketed"

#     print(f"Renewal Type: {renewal_type}")
#     print(f"CT: {has_ct}, PT: {has_pt}, Other: {len(other_files)}")

#     if renewal_type == "Automatic":
#         if not (has_ct and has_pt):
#             raise Exception("Automatic Renewal requires BOTH CT and PT")

#     # ================= TAB =================

#     tab = page.get_by_role("tab", name=f"{renewal_type} Renewal")
#     await tab.wait_for()
#     await tab.click()

#     await page.wait_for_load_state("networkidle")

#     # ================= SELECT LOB =================

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
    

#     # ================= CHECKLIST =================

#     await page.locator("#checklist").click()
#     await page.get_by_role("listbox").wait_for()

#     await page.locator("li[role='option']", has_text="Lite_ExdionPOD").click()

#     print("Checklist Selected -> Lite_ExdionPOD")

#     # ================= FILE UPLOAD =================

#     ordered_files = current_term_files + prior_term_files + other_files

#     for file in ordered_files:

#         file_lower = file.lower()
#         file_path = os.path.join(folder_path, file)

#         # ===== CURRENT TERM =====
#         if file in current_term_files:
#             print(f"Uploading to Current Term -> {file}")
#             label = page.locator("p:has-text('Current Term Policy')")
#             section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
#             await section.locator("input[type='file']").set_input_files(file_path)

#             await page.wait_for_load_state("networkidle")
#             await page.wait_for_timeout(1500)

#         # ===== PRIOR TERM =====
#         elif file in prior_term_files:
#             print(f"Uploading to Prior Term -> {file}")
#             label = page.locator("p:has-text('Prior Term Policy')")
#             section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
#             await section.locator("input[type='file']").set_input_files(file_path)

#         # ===== OTHER DOCUMENTS =====
#         else:

#             if "endorsement" in file_lower or "endt" in file_lower:
#                 label_text = "Endorsement"

#             elif "quote" in file_lower or "qte" in file_lower or "quotation" in file_lower:
#                 label_text = "Carrier Quote"
#                 valid_doc_uploaded = True

#             elif "proposal" in file_lower:
#                 label_text = "Proposal"
#                 valid_doc_uploaded = True

#             elif "accord" in file_lower or "application" in file_lower or "app" in file_lower:
#                 label_text = "Acord Application"
#                 valid_doc_uploaded = True

#             elif "schedule" in file_lower:
#                 label_text = "Schedule"
#                 valid_doc_uploaded = True

#             elif "binder" in file_lower or "bind" in file_lower:
#                 label_text = "Binder"
#                 valid_doc_uploaded = True

#             else:
#                 print(f"Not matched -> {file}")
#                 continue

#             print(f"Uploading to {label_text} -> {file}")

#             label = page.locator(f"p:has-text('{label_text}')")
#             await label.scroll_into_view_if_needed()

#             section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")

#             await section.locator("input[type='file']").set_input_files(file_path)
            
#     if renewal_type == "Marketed":
#         if not has_ct:
#             raise Exception("Marketed requires Current Term document")

#         if not valid_doc_uploaded:
#             raise Exception("Marketed requires at least one valid doc (Proposal/Quote/Application/Binder)")



#     # try:

#     #     async with page.expect_event("dialog", timeout=40000) as dialog_info:
#     #         await page.get_by_role("button", name="Generate Checklist").click()

#     #     dialog = await dialog_info.value

#     #     message = dialog.message
#     #     print("Popup message: ", message)

#     # except Exception as e:
#     #     raise Exception(f"No popup received after Generate Checklist: {str(e)}")

#     #error_msg = "Please choose Proposal or ACORD Application or Carrier Quote or Binder"
#     msg_lower = message.lower()
#     if "please choose" in msg_lower:
#         await dialog.accept()
#         raise Exception("Validation Error: Required documents missing")

#     # Extract Job ID
#     match = re.search(r"Job ID:\s*(\S+)", message)
#     #match = re.search(r"Job ID:\s*([a-zA-Z0-9]+)", message)

#     job_id = match.group(1) if match else None

#     print("Job ID: ", job_id)

#     if not job_id:
#         await dialog.accept()
#         raise Exception("Job ID not found in popup")

#     update_tracker(ref_id, job_id=job_id, status="Completed")

#     await page.wait_for_timeout(3000)

#     await dialog.accept()

#     print(f"Job Created Successfully -> {job_id}")

#     await page.wait_for_url("**jobcsrlisting**", timeout=30000)
#     await page.get_by_placeholder("Search by Job ID").wait_for(timeout=20000)

#     try:
#         jobs = page.get_by_text("Jobs", exact=True)
#         await jobs.wait_for(state="visible", timeout=5000)
#         await jobs.click()

#         upload_docs = page.get_by_text("Upload Documents", exact=True)
#         await upload_docs.wait_for(state="visible", timeout=5000)
#         await upload_docs.click()

#     except Exception as nav_err:
#         print("Navigation warning:", str(nav_err))

#     return job_id

# # ================= MAIN FUNCTION =================

# async def run_istudio():

#     print("ISTUDIO started")

#     config = ConfigParser()
#     config.read(CONFIG_PATH)

#     browser_name = config.get("CarrolliStudio", "browser")
#     url = config.get("CarrolliStudio", "Link")
#     username = config.get("CarrolliStudio", "User_ID")
#     password = config.get("CarrolliStudio", "Password")

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


#         for _, row in pending_df.iterrows():

#             ref_id = row["Reference ID"]
#             attempt = 1

#             while attempt <= MAX_RETRIES:

#                 try:
#                     if attempt == 1:
#                         update_tracker(ref_id, status="In Progress")

#                     print(f"\nProcessing {ref_id} | Attempt {attempt}")

#                     job_id = await create_job(page, row, lob_mapping)

#                     if job_id:
#                         print(f"Completed -> {ref_id}")
#                         break
#                     else:
#                         raise Exception("Job ID not Generated")

#                 except Exception as e:

#                     print(f"Attempt {attempt} Failed -> {ref_id}")
#                     print(str(e))

#                     df = pd.read_excel(TRACKER_PATH)
#                     existing_job = df.loc[df["Reference ID"] == ref_id, "Job ID"].values

#                     if len(existing_job) > 0 and pd.notna(existing_job[0]):
#                         print("Job ID already exists → marking Completed")
#                         update_tracker(ref_id, status="Completed")
#                         break

#                     if attempt == MAX_RETRIES:
#                         print(f"Max retries reached -> {ref_id}")
#                         update_tracker(ref_id, status="Error", error=str(e))
#                         break

#                     attempt += 1

#                     print(f"Retrying in {RETRY_DELAY} seconds...")
#                     await asyncio.sleep(RETRY_DELAY)

#                     if page.is_closed():
#                         print("Page closed → reopening browser page")
#                         page = await context.new_page()
#                         await login(page, url, username, password)
#                     else:
#                         print("Reloading page")
#                         await page.reload()
#                         await page.wait_for_load_state("networkidle")

#                     print("Navigating to Jobs → Upload Documents")

#                     jobs = page.get_by_text("Jobs", exact=True)
#                     await jobs.wait_for(state="visible", timeout=15000)
#                     await jobs.click()

#                     upload_docs = page.get_by_text("Upload Documents", exact=True)
#                     await upload_docs.wait_for(state="visible")
#                     await upload_docs.click()

#         print("\nAll Jobs Processed")

#         try:
#             print("Logging out...")

#             profile_btn = page.get_by_text("Carroll", exact=True)
#             await profile_btn.click()

#             logout_btn = page.get_by_role("menuitem", name="Sign Out")
#             await logout_btn.click()

#             print("Logout Successful")

#         except Exception as e:
#             print("Logout failed:", str(e))

#         await browser.close()


# if __name__ == "__main__":
#     asyncio.run(run_istudio())





################################################################################################################################################################################################################################



import asyncio
import re
from playwright.async_api import async_playwright
from configparser import ConfigParser
import pandas as pd
import os
from datetime import datetime

# ================= PATH CONFIG =================

config = ConfigParser()
config.read("c:/Users/vijay_m/OneDrive - Exdion Solutions Pvt. Ltd.-70692290/Documents/Project_Job_Creation/Carroll/config.ini")
BASE_FOLDER = config.get("PATHS", "BASE_FOLDER")
TRACKER_PATH = os.path.join(BASE_FOLDER, "Carroll_Tracker.xlsx")
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

def update_tracker(reference_id, job_id=None, status=None, error=None):

    df = pd.read_excel(TRACKER_PATH)

    for col in ["Job ID", "Status", "Error"]:
        if col in df.columns:
            df[col] = df[col].astype("string")

    idx = df.index[df["Reference ID"] == reference_id]

    if idx.empty:
        print(f"Reference ID not found -> {reference_id}")
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

    print(f"Tracker Updated -> {reference_id} | {status} | {error}")


#======================= EMAIL ATTACHMENT ========================#

from datetime import datetime, timedelta

def generate_daily_report():

    if not os.path.exists(TRACKER_PATH):
        raise Exception("Tracker file not found")

    df = pd.read_excel(TRACKER_PATH)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df["Status"] = df["Status"].astype(str).str.strip().str.capitalize()

    target_date = (datetime.now() - timedelta(days=1)).date()
    today_str = datetime.now().strftime("%Y-%m-%d")

    filtered = df[df["Date"] == target_date].copy()

    if filtered.empty:
        raise Exception(f"No data found for report: {target_date}")

    filtered = filtered.sort_values(by="Reference ID")

    total = len(filtered)
    completed = len(filtered[filtered["Status"] == "Completed"])
    failed = len(filtered[filtered["Status"] == "Error"])
    pending = len(filtered[filtered["Status"] == "Pending"])

    success_rate = round((completed / total) * 100, 2) if total else 0

    report_path = os.path.join(
        BASE_FOLDER,
        f"Daily_Report_{today_str}.xlsx"
    )

    filtered.to_excel(report_path, index=False)

    print(f"Report saved: {report_path}")

    report_summary = f"""
  DAILY JOB REPORT

Run Date: {today_str}
Data Date: {target_date}

Total Jobs   : {total}
Completed    : {completed}
Failed       : {failed}
Pending      : {pending}
Success Rate : {success_rate}%
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
    await page.get_by_text("Jobs", exact=True).click()

    upload_docs = page.get_by_text("Upload Documents", exact=True)
    await upload_docs.wait_for(state="visible")
    await upload_docs.click()
    
# ================= CREATE JOB FUNCTION =================

async def create_job(page, record, lob_mapping):

    ref_id = record["Reference ID"]
    print(f"Creating Job -> {ref_id}")

    folder_path = os.path.join(PDF_BASE_FOLDER, ref_id)

    current_term_files = []
    prior_term_files = []
    other_files = []

    valid_doc_uploaded = False

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

    # ================= SELECT LOB =================

    lob_code = str(record["LOB"]).strip()

    if lob_code not in lob_mapping:
        raise Exception(f"LOB Code not found in LOB Master: {lob_code}")

    possible_lob_names = lob_mapping[lob_code]

    print(f"Trying LOB names -> {possible_lob_names}")

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
                print(f"LOB Selected -> {option_text}")
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

    print("Checklist Selected -> Lite_ExdionPOD")

    # ================= FILE UPLOAD =================

    ordered_files = current_term_files + prior_term_files + other_files

    for file in ordered_files:

        file_lower = file.lower()
        file_path = os.path.join(folder_path, file)

        # ===== CURRENT TERM =====
        if file in current_term_files:
            print(f"Uploading to Current Term -> {file}")
            label = page.locator("p:has-text('Current Term Policy')")
            section = label.locator("xpath=ancestor::div[.//input[@type='file']][1]")
            await section.locator("input[type='file']").set_input_files(file_path)

            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1500)

        # ===== PRIOR TERM =====
        elif file in prior_term_files:
            print(f"Uploading to Prior Term -> {file}")
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

            print(f"Uploading to {label_text} -> {file}")

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

        async with page.expect_event("dialog", timeout=40000) as dialog_info:
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

    browser_name = config.get("CarrolliStudio", "browser")
    url = config.get("CarrolliStudio", "Link")
    username = config.get("CarrolliStudio", "User_ID")
    password = config.get("CarrolliStudio", "Password")

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

                    print(f"Attempt {attempt} Failed -> {ref_id}")
                    print(str(e))

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
                    else:
                        print("Reloading page")
                        await page.reload()
                        await page.wait_for_load_state("networkidle")

                    print("Navigating to Jobs → Upload Documents")

                    jobs = page.get_by_text("Jobs", exact=True)
                    await jobs.wait_for(state="visible", timeout=15000)
                    await jobs.click()

                    upload_docs = page.get_by_text("Upload Documents", exact=True)
                    await upload_docs.wait_for(state="visible")
                    await upload_docs.click()

        print("\nAll Jobs Processed")

        try:
            print("Logging out...")

            profile_btn = page.get_by_text("Carroll", exact=True)
            await profile_btn.click()

            logout_btn = page.get_by_role("menuitem", name="Sign Out")
            await logout_btn.click()

            print("Logout Successful")

        except Exception as e:
            print("Logout failed:", str(e))

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_istudio())