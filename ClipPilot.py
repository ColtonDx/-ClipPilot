import tkinter as tk
from tkinter import messagebox
import pyperclip
import requests
import keyboard
import threading

# === CONFIG ===
API_KEY = "your_azure_api_key_here"
API_URL = "your_azure_foundry_endpoint_url"

PROMPTS = [
    "Simplify this",
    "Summarize this",
    "Translate to plain English",
    "Turn into bullet points",
    "Extract action items"
]

# === GLOBAL ROOT INSTANCE ===
root = tk.Tk()
root.withdraw()  # Hide the main window, used only for spawning popups

# === POPUP MENU ===
class PromptPopup(tk.Toplevel):
    def __init__(self, master, clipboard_text):
        super().__init__(master)
        self.clipboard_text = clipboard_text
        self.title("Clipboard Copilot")
        self.geometry("300x250+600+300")
        self.overrideredirect(True)
        self.configure(bg="#f0f0f0")
        self.focus_force()

        tk.Label(self, text="Choose a prompt:", bg="#f0f0f0", font=("Segoe UI", 10, "bold")).pack(pady=10)

        for prompt in PROMPTS:
            tk.Button(self, text=prompt, command=lambda p=prompt: self.send_prompt(p)).pack(fill=tk.X, padx=20, pady=2)

        tk.Button(self, text="Custom prompt...", command=self.custom_prompt).pack(fill=tk.X, padx=20, pady=10)

    def send_prompt(self, prompt):
        full_prompt = f"{prompt}:\n\n{self.clipboard_text}"
        threading.Thread(target=self.call_chatgpt, args=(full_prompt,), daemon=True).start()
        self.destroy()

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
                root.after(0, lambda: ResponseWindow(root, reply))
            else:
                root.after(0, lambda: messagebox.showerror("API Error", "No response content received."))
        except Exception:
            root.after(0, lambda: messagebox.showerror("API Error", "Request failed. Please check your configuration."))

# === CUSTOM PROMPT WINDOW ===
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
                root.after(0, lambda: ResponseWindow(root, reply))
            else:
                root.after(0, lambda: messagebox.showerror("API Error", "No response content received."))
        except Exception:
            root.after(0, lambda: messagebox.showerror("API Error", "Request failed. Please check your configuration."))

# === RESPONSE WINDOW ===
class ResponseWindow(tk.Toplevel):
    def __init__(self, master, response_text):
        super().__init__(master)
        self.title("Response")
        self.geometry("500x400+600+300")

        tk.Label(self, text="ChatGPT Response:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        self.textbox = tk.Text(self, wrap=tk.WORD)
        self.textbox.insert(tk.END, response_text)
        self.textbox.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        tk.Button(self, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(pady=10)

    def copy_to_clipboard(self):
        pyperclip.copy(self.textbox.get("1.0", tk.END).strip())
        messagebox.showinfo("Copied", "Response copied to clipboard.")

# === HOTKEY LISTENER ===
def launch_popup():
    clipboard_text = pyperclip.paste().strip()
    if clipboard_text:
        root.after(0, lambda: PromptPopup(root, clipboard_text))
    else:
        root.after(0, lambda: messagebox.showwarning("Empty Clipboard", "Clipboard is empty."))

def start_hotkey_listener():
    keyboard.add_hotkey("ctrl+shift+c", launch_popup)
    print("📋 Copilot hotkey listener running... Press Ctrl+Shift+C to activate.")
    keyboard.wait()

# === MAIN ===
if __name__ == "__main__":
    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    root.mainloop()
