import telebot
import json
import os
from telebot import types

# =========================
# CONFIG
# =========================
TOKEN = "8795490156:AAHPWObArzRkwPLojcbdk4S5BsN-hjIkNSU"
ADMIN_ID = 8525980303

bot = telebot.TeleBot(TOKEN)

# =========================
# FILES & DIRECTORIES
# =========================
USERS_FILE = "users.json"
JOBS_FILE = "jobs.json"
APPLICATIONS_FILE = "applications.json"
SAVED_JOBS_FILE = "saved_jobs.json"
CV_DIR = "cv_files/"

# Ensure folders and files exist
if not os.path.exists(CV_DIR):
    os.makedirs(CV_DIR)

def ensure_file(file_name):
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

ensure_file(USERS_FILE)
ensure_file(JOBS_FILE)
ensure_file(APPLICATIONS_FILE)
ensure_file(SAVED_JOBS_FILE)

# =========================
# JSON HELPERS
# =========================
def load_json(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Database Getters and Setters
def get_users(): return load_json(USERS_FILE)
def save_users(data): save_json(USERS_FILE, data)
def get_jobs(): return load_json(JOBS_FILE)
def save_jobs(data): save_json(JOBS_FILE, data)
def get_applications(): return load_json(APPLICATIONS_FILE)
def save_applications(data): save_json(APPLICATIONS_FILE, data)
def get_saved_jobs(): return load_json(SAVED_JOBS_FILE)
def save_saved_jobs(data): save_json(SAVED_JOBS_FILE, data)

# =========================
# MENUS
# =========================
def user_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("👤 Profile", "💼 Jobs")
    markup.row("🔍 Search Jobs", "⭐ Saved Jobs")
    markup.row("📄 Applications", "📤 Upload CV")
    markup.row("ℹ️ Help")
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ Post Job", "📋 All Jobs")
    markup.row("👥 Users", "📄 Applications")
    markup.row("📊 Statistics", "📢 Broadcast")
    markup.row("🗑 Delete Job")
    return markup

# =========================
# START COMMAND
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    name = message.from_user.first_name or "User"
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"👋 Welcome Admin {name}", reply_markup=admin_menu())
    else:
        bot.send_message(message.chat.id, f"ሰላም {name} 👋\n\nወደ SiraLink V2.0 እንኳን በደህና መጡ", reply_markup=user_menu())

# =========================
# USER: PROFILE SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text == "👤 Profile")
def profile_menu(message):
    users = get_users()
    user_id = str(message.from_user.id)
    
    if user_id in users:
        data = users[user_id]
        cv_status = "✅ Uploaded" if data.get('cv_path') else "❌ Missing"
        bot.send_message(
            message.chat.id,
            f"👤 **Your Profile**\n\n📝 Name: {data.get('name','-')}\n📞 Phone: {data.get('phone','-')}\n🎓 Education: {data.get('education','-')}\n💼 Department: {data.get('department','-')}\n📄 CV Status: {cv_status}"
        )
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("✏️ Edit Profile")
        markup.row("🔙 Back")
        bot.send_message(message.chat.id, "Choose option:", reply_markup=markup)
    else:
        msg = bot.send_message(message.chat.id, "👤 Enter Full Name:")
        bot.register_next_step_handler(msg, get_name)

@bot.message_handler(func=lambda m: m.text in ["✏️ Edit Profile", "✏️ Edit Profile"])
def edit_profile(message):
    msg = bot.send_message(message.chat.id, "👤 Enter Full Name:")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    temp = {"name": message.text}
    msg = bot.send_message(message.chat.id, "📞 Enter Phone Number:")
    bot.register_next_step_handler(msg, lambda m: get_phone(m, temp))

def get_phone(message, temp):
    temp["phone"] = message.text
    msg = bot.send_message(message.chat.id, "🎓 Enter Education Level:")
    bot.register_next_step_handler(msg, lambda m: get_education(m, temp))

def get_education(message, temp):
    temp["education"] = message.text
    msg = bot.send_message(message.chat.id, "💼 Enter Department (IT, Finance, etc.):")
    bot.register_next_step_handler(msg, lambda m: get_department(message, m, temp))

def get_department(orig_msg, message, temp):
    temp["department"] = message.text
    users = get_users()
    user_id = str(message.from_user.id)
    
    # Retain CV if editing profile
    old_cv = users.get(user_id, {}).get("cv_path", None)

    users[user_id] = {
        "telegram_id": message.from_user.id,
        "username": message.from_user.username,
        "name": temp["name"],
        "phone": temp["phone"],
        "education": temp["education"],
        "department": temp["department"],
        "cv_path": old_cv
    }
    save_users(users)
    bot.send_message(message.chat.id, "✅ Profile Saved Successfully", reply_markup=user_menu())

# =========================
# USER: UPLOAD CV (PDF)
# =========================
@bot.message_handler(func=lambda m: m.text == "📤 Upload CV")
def ask_cv(message):
    msg = bot.send_message(message.chat.id, "📄 Please send your CV as a **PDF Document**:")
    bot.register_next_step_handler(msg, save_cv)

def save_cv(message):
    if message.content_type != 'document' or not message.document.file_name.lower().endswith('.pdf'):
        bot.send_message(message.chat.id, "❌ Error: Please send a valid PDF file.", reply_markup=user_menu())
        return

    users = get_users()
    user_id = str(message.from_user.id)
    
    if user_id not in users:
        bot.send_message(message.chat.id, "❌ Please fill out your 👤 Profile first before uploading a CV.")
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_path = os.path.join(CV_DIR, f"{user_id}_cv.pdf")
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        users[user_id]["cv_path"] = file_path
        save_users(users)
        bot.send_message(message.chat.id, "✅ CV Uploaded successfully!", reply_markup=user_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed to save CV: {str(e)}")

# =========================
# USER: SEARCH JOBS
# =========================
@bot.message_handler(func=lambda m: m.text == "🔍 Search Jobs")
def search_jobs_init(message):
    msg = bot.send_message(message.chat.id, "🔍 Enter keyword to search (Job Title, Company, or Category):")
    bot.register_next_step_handler(msg, process_search)

def process_search(message):
    query = message.text.lower()
    jobs = get_jobs()
    found = False

    for job_id, job in jobs.items():
        if (query in job['title'].lower() or 
            query in job['company'].lower() or 
            query in job['department'].lower()):
            
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("Apply 💼", callback_data=f"apply_{job_id}"),
                types.InlineKeyboardButton("Save ⭐", callback_data=f"save_{job_id}")
            )
            
            bot.send_message(
                message.chat.id,
                f"💼 **{job['title']}**\n🏢 Company: {job['company']}\n💰 Salary: {job.get('salary','-')}\n📅 Deadline: {job.get('expiry','-')}\n\n🎯 Req: {job.get('requirements','-')}",
                reply_markup=markup
            )
            found = True
            
    if not found:
        bot.send_message(message.chat.id, "❌ No jobs matched your search query.")

# =========================
# USER: SAVED JOBS
# =========================
@bot.message_handler(func=lambda m: m.text == "⭐ Saved Jobs")
def view_saved_jobs(message):
    saved = get_saved_jobs()
    jobs = get_jobs()
    user_id = str(message.from_user.id)
    
    user_saved = saved.get(user_id, [])
    if not user_saved:
        bot.send_message(message.chat.id, "⭐ You haven't saved any jobs yet.")
        return
        
    for job_id in user_saved:
        if job_id in jobs:
            job = jobs[job_id]
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Apply Now 💼", callback_data=f"apply_{job_id}"))
            bot.send_message(message.chat.id, f"⭐ **Saved Job**\n\n💼 {job['title']}\n🏢 {job['company']}\n🎯 {job['department']}", reply_markup=markup)

# =========================
# ADMIN: POST JOB (V2.0 FEAT)
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Post Job")
def post_job(message):
    if message.from_user.id != ADMIN_ID: return
    temp = {}
    msg = bot.send_message(message.chat.id, "💼 Job Title:")
    bot.register_next_step_handler(msg, lambda m: get_job_title(m, temp))

def get_job_title(message, temp):
    temp["title"] = message.text
    msg = bot.send_message(message.chat.id, "🏢 Company Name:")
    bot.register_next_step_handler(msg, lambda m: get_company(m, temp))

def get_company(message, temp):
    temp["company"] = message.text
    msg = bot.send_message(message.chat.id, "📍 Location:")
    bot.register_next_step_handler(msg, lambda m: get_location(m, temp))

def get_location(message, temp):
    temp["location"] = message.text
    msg = bot.send_message(message.chat.id, "🎯 Category/Department (e.g. IT, Finance):")
    bot.register_next_step_handler(msg, lambda m: get_dept_job(m, temp))

def get_dept_job(message, temp):
    temp["department"] = message.text
    msg = bot.send_message(message.chat.id, "💰 Salary (e.g. 15,000 ETB or Negotiable):")
    bot.register_next_step_handler(msg, lambda m: get_salary_job(m, temp))

def get_salary_job(message, temp):
    temp["salary"] = message.text
    msg = bot.send_message(message.chat.id, "📋 Job Requirements:")
    bot.register_next_step_handler(msg, lambda m: get_reqs_job(m, temp))

def get_reqs_job(message, temp):
    temp["requirements"] = message.text
    msg = bot.send_message(message.chat.id, "📅 Expiry Date (DD/MM/YYYY):")
    bot.register_next_step_handler(msg, lambda m: get_expiry_job(m, temp))

def get_expiry_job(message, temp):
    temp["expiry"] = message.text
    msg = bot.send_message(message.chat.id, "📝 Detailed Description:")
    bot.register_next_step_handler(msg, lambda m: final_save_job(m, temp))

def final_save_job(message, temp):
    temp["description"] = message.text
    jobs = get_jobs()
    job_id = str(len(jobs) + 1)
    jobs[job_id] = temp
    save_jobs(jobs)
    
    bot.send_message(message.chat.id, f"✅ Job Posted Successfully!\nID: {job_id}", reply_markup=admin_menu())
    notify_matching_users(job_id, temp)

def notify_matching_users(job_id, job):
    users = get_users()
    for uid, data in users.items():
        if data.get("department", "").lower() == job["department"].lower():
            try:
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("Apply ✨", callback_data=f"apply_{job_id}"),
                    types.InlineKeyboardButton("Save ⭐", callback_data=f"save_{job_id}")
                )
                bot.send_message(
                    int(uid),
                    f"🔔 **New Job Match In Your Department!**\n\n💼 {job['title']}\n🏢 {job['company']}\n💰 Salary: {job['salary']}\n📅 Deadline: {job['expiry']}\n\n📝 Description: {job['description']}",
                    reply_markup=markup
                )
            except: pass

# =========================
# SYSTEM: APPLY & SAVE ACTIONS
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith(("apply_", "save_")))
def handle_job_callbacks(call):
    action, job_id = call.data.split("_")
    user_id = str(call.from_user.id)
    jobs = get_jobs()
    
    if job_id not in jobs:
        bot.answer_callback_query(call.id, "Job not found!")
        return

    if action == "save":
        saved = get_saved_jobs()
        if user_id not in saved: saved[user_id] = []
        if job_id in saved[user_id]:
            bot.answer_callback_query(call.id, "Already saved!")
        else:
            saved[user_id].append(job_id)
            save_saved_jobs(saved)
            bot.answer_callback_query(call.id, "Job added to Saved List! ⭐")
            
    elif action == "apply":
        users = get_users()
        if user_id not in users or not users[user_id].get("cv_path"):
            bot.answer_callback_query(call.id, "❌ Submit your CV via 'Upload CV' button first!", show_alert=True)
            return
            
        apps = get_applications()
        if user_id not in apps: apps[user_id] = []
        
        if any(item["job_id"] == job_id for item in apps[user_id]):
            bot.answer_callback_query(call.id, "Already Applied for this job!")
            return
            
        apps[user_id].append({
            "job_id": job_id,
            "job_title": jobs[job_id]["title"],
            "company": jobs[job_id]["company"],
            "status": "Pending"
        })
        save_applications(apps)
        bot.answer_callback_query(call.id, "Application Submitted!")
        bot.send_message(call.message.chat.id, f"✅ Applied to **{jobs[job_id]['title']}** at {jobs[job_id]['company']}. Status: Pending.")
        
        # Notify Admin with Actionable Buttons
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Approve ✅", callback_data=f"adm_approve_{user_id}_{job_id}"),
            types.InlineKeyboardButton("Reject ❌", callback_data=f"adm_reject_{user_id}_{job_id}")
        )
        bot.send_message(
            ADMIN_ID, 
            f"📥 **New Application Received**\n\n👤 Applicant: {users[user_id]['name']}\n📞 Phone: {users[user_id]['phone']}\n💼 Job: {jobs[job_id]['title']}\n🏢 Company: {jobs[job_id]['company']}",
            reply_markup=markup
        )
        # Send CV Document to Admin
        with open(users[user_id]["cv_path"], "rb") as cv_f:
            bot.send_document(ADMIN_ID, cv_f, caption=f"📄 CV of {users[user_id]['name']}")

# =========================
# ADMIN: APPROVE / REJECT APPLICATIONS
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith(("adm_approve_", "adm_reject_")))
def handle_admin_decision(call):
    data_parts = call.data.split("_")
    action = data_parts[1]
    target_user = data_parts[2]
    job_id = data_parts[3]
    
    apps = get_applications()
    new_status = "Approved" if action == "approve" else "Rejected"
    
    if target_user in apps:
        for app in apps[target_user]:
            if app["job_id"] == job_id:
                app["status"] = new_status
                break
        save_applications(apps)
        
        bot.edit_message_text(f"Processed: Application has been **{new_status}**.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        # Notify User (Notification feature)
        try:
            bot.send_message(int(target_user), f"🔔 **Application Update!**\n\nYour application for **{app['job_title']}** has been **{new_status}** by the recruiter.")
        except: pass

# =========================
# GENERAL JOB & APPLICATION VIEWERS
# =========================
@bot.message_handler(func=lambda m: m.text == "💼 Jobs")
def view_jobs(message):
    jobs = get_jobs()
    if not jobs:
        bot.send_message(message.chat.id, "❌ No Jobs Available")
        return
    for jid, job in jobs.items():
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("Apply 💼", callback_data=f"apply_{jid}"), types.InlineKeyboardButton("Save ⭐", callback_data=f"save_{jid}"))
        bot.send_message(message.chat.id, f"🆔 ID: {jid}\n💼 Job: {job['title']}\n🏢 Company: {job['company']}\n💰 Salary: {job.get('salary','-')}\n📅 Deadline: {job.get('expiry','-')}", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📄 Applications")
def route_applications(message):
    if message.from_user.id == ADMIN_ID:
        apps = get_applications()
        users = get_users()
        if not apps:
            bot.send_message(message.chat.id, "No Applications found.")
            return
        text = "📋 **All Applications:**\n\n"
        for uid, user_apps in apps.items():
            u_name = users.get(uid, {}).get("name", "Unknown")
            for app in user_apps:
                text += f"👤 {u_name} -> 💼 {app['job_title']} [{app['status']}]\n"
        bot.send_message(message.chat.id, text[:4000])
    else:
        apps = get_applications()
        uid = str(message.from_user.id)
        if uid not in apps or not apps[uid]:
            bot.send_message(message.chat.id, "📄 You haven't applied to any jobs yet.")
            return
        text = "📄 **My Applications:**\n\n"
        for app in apps[uid]:
            text += f"💼 Job: {app['job_title']}\n🏢 Company: {app['company']}\n📌 Status: {app['status']}\n\n"
        bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📋 All Jobs" and m.from_user.id == ADMIN_ID)
def admin_all_jobs(message):
    jobs = get_jobs()
    if not jobs:
        bot.send_message(message.chat.id, "No jobs available.")
        return
    text = "📋 **Current Job Openings:**\n\n"
    for jid, job in jobs.items():
        text += f"🆔 {jid}. {job['title']} at {job['company']} ({job['department']})\n"
    bot.send_message(message.chat.id, text[:4000])

@bot.message_handler(func=lambda m: m.text == "👥 Users" and m.from_user.id == ADMIN_ID)
def admin_view_users(message):
    users = get_users()
    if not users:
        bot.send_message(message.chat.id, "No registered users.")
        return
    text = "👥 **Registered Talent Pool:**\n\n"
    for uid, u in users.items():
        text += f"👤 Name: {u.get('name','-')}\n📞 Phone: {u.get('phone','-')}\n🎯 Dept: {u.get('department','-')}\n🆔 ID: {uid}\n\n"
    bot.send_message(message.chat.id, text[:4000])

@bot.message_handler(func=lambda m: m.text == "📊 Statistics" and m.from_user.id == ADMIN_ID)
def admin_stats(message):
    users, jobs, apps = get_users(), get_jobs(), get_applications()
    total_apps = sum(len(a) for a in apps.values())
    bot.send_message(message.chat.id, f"📊 **SiraLink V2.0 Statistics**\n\n👥 Registered Users: {len(users)}\n💼 Active Jobs: {len(jobs)}\n📄 Total Applications: {total_apps}")

# =========================
# ADMIN: BROADCAST & DELETE
# =========================
@bot.message_handler(func=lambda m: m.text == "📢 Broadcast" and m.from_user.id == ADMIN_ID)
def run_broadcast(message):
    msg = bot.send_message(message.chat.id, "📢 Enter your announcement message:")
    bot.register_next_step_handler(msg, send_bulk_msg)

def send_bulk_msg(message):
    users = get_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 **Announcement from SiraLink**\n\n{message.text}")
            success += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ Broadcast sent successfully to {success} users.")

@bot.message_handler(func=lambda m: m.text == "🗑 Delete Job" and m.from_user.id == ADMIN_ID)
def ask_delete_job(message):
    msg = bot.send_message(message.chat.id, "🗑 Enter the Job ID you want to delete:")
    bot.register_next_step_handler(msg, process_delete_job)

def process_delete_job(message):
    job_id = message.text.strip()
    jobs = get_jobs()
    if job_id in jobs:
        del jobs[job_id]
        save_jobs(jobs)
        bot.send_message(message.chat.id, f"🗑 Job ID {job_id} has been removed.")
    else:
        bot.send_message(message.chat.id, "❌ Job ID not found.")

# =========================
# BACK TO MENU / HELP / FALLBACK
# =========================
@bot.message_handler(func=lambda m: m.text == "🔙 Back")
def back_to_main(message):
    bot.send_message(message.chat.id, "🏠 Main Menu", reply_markup=user_menu())

@bot.message_handler(func=lambda m: m.text == "ℹ️ Help")
def help_menu(message):
    bot.send_message(
        message.chat.id,
        "📌 **SiraLink Bot V2.0 Manual**\n\n"
        "1. **Profile**: Fill this first to save your professional background.\n"
        "2. **Upload CV**: Send your CV as a PDF file.\n"
        "3. **Jobs & Search**: Browse vacancies and click 'Apply' or 'Save' to look at them later.\n"
        "4. **Notifications**: You will automatically be notified when a company updates your application status!"
    )

@bot.message_handler(content_types=["text"])
def fallback(message): pass

# =========================
# BOOT
# =========================
print("SiraLink Bot V2.0 Started Successfully...")
bot.infinity_polling(skip_pending=True)