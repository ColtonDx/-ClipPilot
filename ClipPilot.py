import tkinter as tk
from tkinter import simpledialog, messagebox
import pyperclip
import requests
import keyboard
import threading
import configparser
import os
import re

CONFIG_FILE = "ClipPilot.conf"

# === Validation ===
def is_valid_url(url):
    return re.match(r"^https://.+\.azure\.com/.+", url)

def test_connection(api_url, api_key):
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello!"}
        ]
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return "choices" in data and len(data["choices"]) > 0
    except Exception:
        return False

# === Setup Wizard ===
def launch_setup_wizard():
    wizard = tk.Tk()
    wizard.withdraw()

    messagebox.showinfo("ClipPilot Setup", "Welcome! Let's configure your ClipPilot settings.")

    # === API URL ===
    while True:
        api_url = simpledialog.askstring("API URL", "Enter your Azure API URL:", parent=wizard)
        if api_url is None:
            messagebox.showinfo("Setup Cancelled", "Setup was cancelled.")
            wizard.quit()
            wizard.destroy()
            return
        if not is_valid_url(api_url):
            messagebox.showerror("Invalid URL", "Please enter a valid Azure endpoint URL.")
            continue
        break

    # === API Key ===
    api_key = simpledialog.askstring("API Key", "Enter your Azure API Key:", parent=wizard)
    if api_key is None or api_key.strip() == "":
        messagebox.showinfo("Setup Cancelled", "Setup was cancelled.")
        wizard.quit()
        wizard.destroy()
        return

    # === Test Connection ===
    messagebox.showinfo("Testing Connection", "Checking your API credentials...")
    if not test_connection(api_url, api_key):
        messagebox.showerror("Connection Failed", "Could not connect to Azure OpenAI. Please check your URL and key.")
        wizard.quit()
        wizard.destroy()
        return

    # === Hotkey ===
    hotkey = simpledialog.askstring("Hotkey", "Customize hotkey (default is ctrl+shift+c):", parent=wizard)
    if hotkey is None or hotkey.strip() == "":
        hotkey = "ctrl+shift+c"

    # === Save Config ===
    config = configparser.ConfigParser()
    config["ClipPilot"] = {
        "api_url": api_url,
        "api_key": api_key,
        "hotkey": hotkey
    }

    with open(CONFIG_FILE, "w") as f:
        config.write(f)

    messagebox.showinfo("Setup Complete", f"✅ Config saved to {CONFIG_FILE}. Launching ClipPilot...")
    wizard.quit()
    wizard.destroy()



# === Load Config ===
if not os.path.exists(CONFIG_FILE):
    launch_setup_wizard()

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

try:
    API_KEY = config.get("ClipPilot", "api_key")
    API_URL = config.get("ClipPilot", "api_url")
    current_hotkey = config.get("ClipPilot", "hotkey", fallback="ctrl+shift+c")
except Exception as e:
    raise ValueError(f"Invalid or missing config values: {e}")

if not API_KEY or not API_URL:
    raise ValueError("Missing API key or API URL in ClipPilot.conf")

# === Prompt Presets ===
PROMPTS = [
    "Simplify this",
    "Summarize this",
    "Translate to plain English",
    "Turn into bullet points",
    "Extract action items"
]

# === GUI Root ===
root = tk.Tk()
root.withdraw()

# === Prompt Menu ===
class PromptPopup(tk.Toplevel):
    def __init__(self, master, clipboard_text):
        super().__init__(master)
        self.clipboard_text = clipboard_text
        self.title("Clipboard Copilot")
        self.geometry("300x300+600+300")
        self.configure(bg="#f0f0f0")
        self.focus_force()

        tk.Label(self, text="Choose a prompt:", bg="#f0f0f0", font=("Segoe UI", 10, "bold")).pack(pady=10)

        for prompt in PROMPTS:
            tk.Button(self, text=prompt, command=lambda p=prompt: self.send_prompt(p)).pack(fill=tk.X, padx=20, pady=2)

        tk.Button(self, text="Custom prompt...", command=self.custom_prompt).pack(fill=tk.X, padx=20, pady=10)
        tk.Button(self, text="Cancel", command=self.destroy).pack(fill=tk.X, padx=20, pady=5)

        self.bind("<Escape>", lambda e: self.destroy())

    def send_prompt(self, prompt):
        full_prompt = f"{prompt}:\n\n{self.clipboard_text}"
        self.destroy()
        threading.Thread(target=lambda: ResponseWindow(root, "", full_prompt), daemon=True).start()


    def custom_prompt(self):
        self.destroy()
        CustomPromptWindow(root, self.clipboard_text)

def call_chatgpt(self, user_input):
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            reply = data["choices"][0]["message"]["content"]
            root.after(0, lambda: ResponseWindow(root, reply, user_input))  # ✅ Pass initial_prompt
        else:
            root.after(0, lambda: messagebox.showerror("API Error", "No response content received."))
    except Exception:
        root.after(0, lambda: messagebox.showerror("API Error", "Request failed. Please check your configuration."))

# === Custom Prompt Window ===
class CustomPromptWindow(tk.Toplevel):
    def __init__(self, master, clipboard_text):
        super().__init__(master)
        self.clipboard_text = clipboard_text
        self.title("Custom Prompt")
        self.geometry("400x150+600+300")
        self.focus_force()

        tk.Label(self, text="Enter your custom prompt:").pack(pady=10)
        self.entry = tk.Entry(self, width=50)
        self.entry.pack(pady=5)
        tk.Button(self, text="Send", command=self.send).pack(pady=10)

    def send(self):
        prompt = self.entry.get().strip()
        if prompt:
            full_prompt = f"{prompt}:\n\n{self.clipboard_text}"
            threading.Thread(target=self.call_chatgpt, args=(full_prompt,), daemon=True).start()
            self.destroy()

def call_chatgpt(self, user_input):
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            reply = data["choices"][0]["message"]["content"]
            root.after(0, lambda: ResponseWindow(root, reply, user_input))  # ✅ Pass initial_prompt
        else:
            root.after(0, lambda: messagebox.showerror("API Error", "No response content received."))
    except Exception:
        root.after(0, lambda: messagebox.showerror("API Error", "Request failed. Please check your configuration."))

# === Response Window ===
class ResponseWindow(tk.Toplevel):
    def __init__(self, master, initial_response, initial_prompt):
        super().__init__(master)
        self.title("Conversation")
        self.geometry("500x500+600+300")

        self.conversation_history = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": initial_prompt},
            {"role": "assistant", "content": initial_response}
        ]

        tk.Label(self, text="ClipPilot Conversation:", font=("Segoe UI", 10, "bold")).pack(pady=5)

        self.textbox = tk.Text(self, wrap=tk.WORD, state=tk.NORMAL)
        self.textbox.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        self.textbox.insert(tk.END, f"🧑 You: {initial_prompt}\n\n🤖 Copilot: {initial_response}\n\n")
        self.textbox.config(state=tk.DISABLED)

        self.reply_entry = tk.Entry(self, width=60)
        self.reply_entry.pack(pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Send Reply", command=self.send_reply).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Copy All", command=self.copy_conversation).pack(side=tk.LEFT, padx=5)

    def send_reply(self):
        user_input = self.reply_entry.get().strip()
        if not user_input:
            return

        self.reply_entry.delete(0, tk.END)
        self.conversation_history.append({"role": "user", "content": user_input})

        threading.Thread(target=self.call_chatgpt, args=(self.conversation_history,), daemon=True).start()

    def call_chatgpt(self, messages):
        headers = {
            "api-key": API_KEY,
            "Content-Type": "application/json"
        }
        payload = {"messages": messages}

        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                reply = data["choices"][0]["message"]["content"]
                self.conversation_history.append({"role": "assistant", "content": reply})
                self.root_display_reply(reply)
            else:
                self.root_display_reply("[No response received.]")
        except Exception:
            self.root_display_reply("[Request failed. Check your config.]")

    def root_display_reply(self, reply):
        self.textbox.config(state=tk.NORMAL)
        self.textbox.insert(tk.END, f"🤖 Copilot: {reply}\n\n")
        self.textbox.config(state=tk.DISABLED)
        self.textbox.see(tk.END)

    def copy_conversation(self):
        full_text = self.textbox.get("1.0", tk.END).strip()
        pyperclip.copy(full_text)
        messagebox.showinfo("Copied", "Conversation copied to clipboard.")

# === System Tray Icon ===
import pystray
from pystray import MenuItem as item
from PIL import Image
import subprocess

def open_config():
    subprocess.Popen(["notepad.exe", CONFIG_FILE])

def exit_app(icon, item):
    icon.stop()
    root.quit()

def create_tray_icon():
    image = Image.open("ClipPilot_Logo.ico") 
    menu = (
        item("Open Config", lambda: open_config()),
        item("Exit", exit_app)
    )
    icon = pystray.Icon("ClipPilot", image, "ClipPilot", menu)
    threading.Thread(target=icon.run, daemon=True).start()


# === Hotkey Listener ===
def launch_popup():
    clipboard_text = pyperclip.paste().strip()
    if clipboard_text:
        root.after(0, lambda: PromptPopup(root, clipboard_text))
    else:
        root.after(0, lambda: messagebox.showwarning("Empty Clipboard", "Clipboard is empty."))

def start_hotkey_listener():
    keyboard.add_hotkey(current_hotkey, launch_popup)
    print(f"📋 ClipPilot hotkey listener running... Press {current_hotkey} to activate.")
    keyboard.wait()

# === Main ===
if __name__ == "__main__":
    create_tray_icon()
    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    root.mainloop()
