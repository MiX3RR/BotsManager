import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk
import darkdetect
from queue import Queue, Empty
import logging
from pathlib import Path
import pygetwindow as gw
import sys
import json
import codecs
# UTF-8 encoding setup
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
# Configuration
CONFIG_FILE = 'cfg.json'

def load_config():
    default_config = {
        'paths_to_scan': [
            r"C:\Users\MiXeRR\Desktop\BotsTG\BotsPyrogramm",
            r"C:\Users\MiXeRR\Desktop\BotsTG\BotsTelethon"
        ],
        'exclude_folders': ["venv", "sessions", ".git", "bot"],
        'checkbox_states': {},
        'is_dark_mode': True,
        'background_mode': False
    }    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default_config

def save_config(config_data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

config = load_config()

# Global variables
background_mode = None
background_labels = []
log_queue = Queue()
script_processes = {}
script_labels = []
is_dark_mode = config.get('is_dark_mode', darkdetect.isDark())
root = None
log_text = None
checkbox_vars_1 = {}
checkbox_vars_2 = {}
checkbox_vars_3 = {}
kill_button_pairs = []
status_indicators = []

def update_bot_config(scripts):
    bot_names = [os.path.basename(os.path.dirname(script)) for script in scripts]
    # Update multithread_bots list
    if 'multithread_bots' not in config:
        config['multithread_bots'] = []
    # Initialize bot settings if not exists
    if 'bot_settings' not in config:
        config['bot_settings'] = {}
    # Update settings for each bot
    for bot_name in bot_names:
        if bot_name not in config['bot_settings']:
            config['bot_settings'][bot_name] = {
                'is_multithread': False,
                'last_checkbox': '1'  # Default checkbox state
            }
    
    save_config(config)

def on_checkbox_click(script, current_var, other_vars):
    if current_var.get() == 1:
        for other_var in other_vars:
            other_var.set(0)
    
    script_folder = os.path.basename(os.path.dirname(script))
    # Save checkbox states
    config['checkbox_states'][script_folder] = {
        'path': script,
        'states': {
            '1': checkbox_vars_1[script].get(),
            '2': checkbox_vars_2[script].get(),
            '3': checkbox_vars_3[script].get()
        }
    }
    # Update bot settings
    if script_folder in config['bot_settings']:
        for idx, state in enumerate(['1', '2', '3'], 1):
            if config['checkbox_states'][script_folder]['states'][str(idx)] == 1:
                config['bot_settings'][script_folder]['last_checkbox'] = str(idx)
                break
    
    save_config(config)
# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("script_monitor.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def log_message(message: str, show_in_gui: bool = True):
    logging.info(message)
    if show_in_gui:
        log_queue.put(message)

def show_credits():
    credits_window = tk.Toplevel(root)
    credits_window.title("О программе")
    credits_window.geometry("400x300")  # Reduced size
    credits_window.resizable(False, False)
    
    style = ttk.Style()
    style.configure("Credits.TLabel", font=("Arial", 9))  # Smaller font
    style.configure("Header.TLabel", font=("Arial", 10, "bold"))  # Smaller header font

    main_frame = ttk.Frame(credits_window, padding="10")  # Reduced padding
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main_frame, text="Bots Manager", style="Header.TLabel").pack(pady=5)
    ttk.Label(main_frame, text="Версия 1.0", style="Credits.TLabel").pack()

    ttk.Label(main_frame, text="\nНазначение программы:", style="Header.TLabel").pack(pady=5)
    purpose_text = """Программа предназначена для управления и мониторинга (фоновых процессов).
Позволяет запускать, останавливать и отслеживать состояние ботов в режиме реального времени."""
    ttk.Label(main_frame, text=purpose_text, style="Credits.TLabel", wraplength=350).pack()

    ttk.Label(main_frame, text="\nРазработчики:", style="Header.TLabel").pack(pady=5)
    credits_text = """Рзработка ввелась при помощи: Cody (AI Assistant)
Идея: MiXeRR & Satoshi
Тестирование: MiXeRR"""
    ttk.Label(main_frame, text=credits_text, style="Credits.TLabel").pack()

    ttk.Label(main_frame, text="\n© 2024 Все права защищены(pizdezh)", style="Credits.TLabel").pack(pady=10)

    ttk.Button(main_frame, text="Закрыть", command=credits_window.destroy).pack(pady=5)


def get_scripts(paths, exclude_dirs=None):
    scripts = []
    for base_path in paths:
        base_path = Path(base_path)
        for root, dirs, files in os.walk(base_path):
            root_path = Path(root)
            
            current_dir = root_path.name
            if exclude_dirs and current_dir in exclude_dirs:
                dirs.clear()
                continue
                
            if exclude_dirs:
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            if "main.py" in files:
                full_path = root_path / "main.py"
                scripts.append(str(full_path))
    
    return scripts

def run_script(script_path):
    script_dir = os.path.dirname(script_path)
    button_name = os.path.basename(script_dir)
    process = None
    
    selected_index = "1"
    if script_path in checkbox_vars_3 and checkbox_vars_3[script_path].get() == 1:
        selected_index = "3"
    elif script_path in checkbox_vars_2 and checkbox_vars_2[script_path].get() == 1:
        selected_index = "2"
    
    if background_mode.get():
        python_path = sys.executable.replace('python.exe', 'pythonw.exe')
        terminal_command = [
            python_path,
            os.path.join(script_dir, 'main.py'),
            '-a', selected_index
        ]
        
        process = subprocess.Popen(
            terminal_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=script_dir,
            creationflags=subprocess.CREATE_NO_WINDOW,
            text=True,
            encoding='utf-8'
        )
        
        threading.Thread(
            target=monitor_process_errors,
            args=(process, button_name),
            daemon=True
        ).start()
    else:
        terminal_command = f'start cmd /k "title {button_name} && cd /d {script_dir} && python main.py -a {selected_index}"'
        process = subprocess.Popen(
            terminal_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    log_message(f"Launched bot: {button_name} {'(background mode)' if background_mode.get() else ''} with index {selected_index}")
    return process
def monitor_process_errors(process, bot_name):
   while True:
        error_line = process.stderr.readline()
        if error_line:
            if "--- Logging error ---" in error_line:
                log_message(f"⚠️ {bot_name}: Logging error detected")
            elif error_line.strip():
                log_message(f"⚠️ {bot_name}: {error_line.strip()}")
        
        if process.poll() is not None:
            break
        
        time.sleep(0.1)

def kill_process(script_path):
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_dir)
    
    try:
        cmd = f'powershell "Get-WmiObject Win32_Process | Where-Object {{$_.Name -eq \'pythonw.exe\' -and $_.CommandLine -like \'*{script_dir}*\'}} | Select-Object ProcessId | Format-List"'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        pid = None
        for line in result.stdout.splitlines():
            if 'ProcessId' in line:
                pid = line.split(':')[1].strip()
                break
        
        if pid:
            kill_cmd = f'taskkill /F /PID {pid}'
            subprocess.run(kill_cmd, shell=True)
            
            if script_path in script_processes:
                del script_processes[script_path]
                
            log_message(f"Successfully terminated bot: {script_name}")
        else:
            cmd2 = f'wmic process where "name=\'pythonw.exe\' and commandline like \'%{script_dir}%\'" get processid'
            result2 = subprocess.run(cmd2, capture_output=True, text=True, shell=True)
            
            if result2.stdout.strip():
                pid = result2.stdout.splitlines()[1].strip()
                kill_cmd = f'taskkill /F /PID {pid}'
                subprocess.run(kill_cmd, shell=True)
                log_message(f"Successfully terminated bot (method 2): {script_name}")
            else:
                log_message(f"No running process found for: {script_name}")
            
    except Exception as e:
        log_message(f"Error terminating {script_name}: {str(e)}")

def monitor_scripts(scripts, script_labels):
    while True:
        for script_path, label in zip(scripts, script_labels):
            button_name = os.path.basename(os.path.dirname(script_path))
            try:
                windows = gw.getWindowsWithTitle(button_name)
                update_gui_element(label, 
                    text="✅" if windows else "❌",
                    foreground="green" if windows else "red"
                )
            except Exception:
                update_gui_element(label, text="❌", foreground="red")
        time.sleep(0.1)

def monitor_background_processes(scripts):
    while True:
        for script_path, status_data in zip(scripts, status_indicators):
            canvas, indicator = status_data
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_dir)
            
            try:
                result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], 
                                     capture_output=True, 
                                     text=True)
                
                is_running = False
                for line in result.stdout.splitlines():
                    if 'python' in line.lower():
                        pid = line.split(',')[1].strip('"')
                        cmd = f'wmic process where ProcessId={pid} get CommandLine /format:csv'
                        proc_details = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                        
                        if script_path.replace('\\', '/').lower() in proc_details.stdout.lower():
                            is_running = True
                            break

                def update_indicator(cnv, ind, running):
                    color = 'green' if running else 'red'
                    cnv.itemconfig(ind, fill=color)

                root.after(0, update_indicator, canvas, indicator, is_running)

            except Exception as e:
                print(f"Monitor error for {script_name}: {e}")
                root.after(0, update_indicator, canvas, indicator, False)
                
        time.sleep(1)

def process_log_queue(log_text):
    def batch_update():
        messages = []
        try:
            while True:
                messages.append(log_queue.get_nowait())
        except Empty:
            pass

        if messages:
            log_text.configure(state='normal')
            log_text.insert(tk.END, '\n'.join(messages) + '\n')
            log_text.configure(state='disabled')
            log_text.see(tk.END)

    while True:
        root.after_idle(batch_update)
        time.sleep(0.05)
def check_git_updates(folder_path):
    try:
        print(f"Checking git updates in: {folder_path}")
        
        fetch_output = subprocess.run(
            ["git", "fetch"],
            cwd=folder_path,
            capture_output=True,
            text=True
        )
        log_message(f"Git fetch output: {fetch_output.stdout}")
        
        pull_output = subprocess.run(
            ["git", "pull"],
            cwd=folder_path,
            capture_output=True,
            text=True
        )
        log_message(f"Git pull output: {pull_output.stdout}")
        
        return True
    except Exception as e:
        log_message(f"Git check error: {str(e)}")
        return False

def check_and_install_requirements(folder_path):
    requirements_path = os.path.join(folder_path, 'requirements.txt')
    bot_name = os.path.basename(folder_path)
    
    try:
        log_message(f"📦 {bot_name}: Checking requirements...")
        
        installed = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True
        ).stdout.splitlines()
        installed = {p.split('==')[0].lower() for p in installed}
        
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        required = []
        
        for encoding in encodings:
            try:
                with open(requirements_path, 'r', encoding=encoding) as f:
                    required = f.read().splitlines()
                break
            except UnicodeError:
                continue
        
        to_install = []
        for req in required:
            if not req.strip() or req.startswith('#'):
                continue
            package = req.split('==')[0].split('>=')[0].split('<=')[0].strip().lower()
            if package not in installed:
                to_install.append(req)
        
        if not to_install:
            log_message(f"✅ {bot_name}: All packages already installed")
            return True
            
        log_message(f"📦 {bot_name}: Installing {len(to_install)} missing packages...")
        
        for package in to_install:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=True,
                    text=True,
                    check=True
                )
                log_message(f"✅ {bot_name}: Installed {package}")
            except subprocess.CalledProcessError as e:
                log_message(f"⚠️ {bot_name}: Failed to install {package}: {e.stderr}")
                continue
                
        return True
            
    except Exception as e:
        log_message(f"❌ {bot_name}: Installation error: {str(e)}")
        return False

def start_script(script_path, script_label):
    script_dir = os.path.dirname(script_path)
    bot_name = os.path.basename(script_dir)
    venv_path = os.path.join(script_dir, 'venv')
    
    def setup_and_run():
        # Check and create venv if not exists
        if not os.path.exists(venv_path):
            log_message(f"🔧 {bot_name}: Creating virtual environment...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", venv_path],
                    check=True,
                    capture_output=True,
                    text=True
                )
                log_message(f"✅ {bot_name}: Virtual environment created successfully")
                
                # Get venv python path
                venv_python = os.path.join(venv_path, 'Scripts', 'python.exe')
                
                # Upgrade pip in new venv
                subprocess.run(
                    [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
                    check=True,
                    capture_output=True
                )
            except Exception as e:
                log_message(f"❌ {bot_name}: Failed to create virtual environment: {str(e)}")
                return

        if not check_git_updates(script_dir):
            log_message(f"⚠️ Git check failed for {bot_name}")
            return
            
        if not check_and_install_requirements(script_dir):
            log_message(f"⚠️ Dependency installation failed for {bot_name}")
            return
            
        process = run_script(script_path)
        script_processes[script_path] = process
    
    threading.Thread(target=setup_and_run, daemon=True).start()

def update_gui_element(element, **kwargs):
    try:
        root.after_idle(lambda: element.config(**kwargs))
    except Exception:
        pass

def start_all_scripts(scripts, script_labels, delay=7):
    for script, label in zip(scripts, script_labels):
        start_script(script, label)
        time.sleep(delay)

def start_selected_scripts():
    selected_scripts = []
    for script in scripts:
        if (checkbox_vars_1[script].get() == 1 or 
            checkbox_vars_2[script].get() == 1 or 
            checkbox_vars_3[script].get() == 1):
            selected_scripts.append(script)
    
    if not selected_scripts:
        log_message("⚠️ No bots selected")
        return
        
    log_message(f"🚀 Starting {len(selected_scripts)} selected bots sequentially...")
    
    def launch_sequence():
        for script in selected_scripts:
            bot_name = os.path.basename(os.path.dirname(script))
            log_message(f"Starting {bot_name}...")
            
            start_script(script, None)
            
            attempts = 0
            max_attempts = 30
            while attempts < max_attempts:
                try:
                    if not background_mode.get():
                        windows = gw.getWindowsWithTitle(bot_name)
                        if windows:
                            log_message(f"✅ {bot_name} initialized successfully")
                            break
                    else:
                        cmd = f'wmic process where "name=\'pythonw.exe\' and commandline like \'%{script}%\'" get processid'
                        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                        if result.stdout.strip():
                            log_message(f"✅ {bot_name} initialized successfully")
                            break
                except Exception:
                    pass
                    
                time.sleep(1)
                attempts += 1
                
            if attempts >= max_attempts:
                log_message(f"⚠️ Timeout waiting for {bot_name} to initialize")
                
            time.sleep(5)
    
    threading.Thread(target=launch_sequence, daemon=True).start()

def update_kill_buttons_visibility():
    is_background = background_mode.get()
    for btn, row_frame in kill_button_pairs:
        if is_background:
            btn.pack(side=tk.RIGHT, padx=2)
            row_frame.update_idletasks()
        else:
            btn.pack_forget()

def handle_mouse_copy(event):
    try:
        selected_text = log_text.selection_get()
        root.clipboard_clear()
        root.clipboard_append(selected_text)
        log_message("✅ Text copied to clipboard")
    except:
        pass

def on_checkbox_click(script, current_var, other_vars):
    if current_var.get() == 1:
        for other_var in other_vars:
            other_var.set(0)
    
    script_folder = os.path.basename(os.path.dirname(script))
    config['checkbox_states'][script_folder] = {
        'path': script,
        'states': {
            '1': checkbox_vars_1[script].get(),
            '2': checkbox_vars_2[script].get(),
            '3': checkbox_vars_3[script].get()
        }
    }
    save_config(config)
def create_gui(scripts):
    global root, script_labels, log_text, background_mode
    
    root = tk.Tk()
    root.title("Script Monitor")
    
    background_mode = tk.BooleanVar(value=config.get('background_mode', False))
    script_labels = []
    background_labels = []

    style = ttk.Style()
    style.theme_use("clam")

    def toggle_theme():
        global is_dark_mode        
        is_dark_mode = not is_dark_mode
        apply_theme()
        theme_button.config(text="☀️ Light Mode" if is_dark_mode else "🌙 Dark Mode")
        config['is_dark_mode'] = is_dark_mode
        save_config(config)

    def apply_theme():
        if is_dark_mode:
            dark_bg = "#1a1b26"
            dark_secondary = "#24283b"
            dark_highlight = "#414868"
            text_color = "#c0caf5"
            accent_color = "#7aa2f7"
        
            root.configure(bg=dark_bg)
            bottom_panel.configure(bg=dark_bg)
            main_container.configure(bg=dark_bg)
            content_frame.configure(bg=dark_bg)
            buttons_frame.configure(bg=dark_bg)
            log_frame.configure(bg=dark_bg)
            scrollable_frame.configure(bg=dark_bg)
        
            style.configure(".", 
                background=dark_bg,
                foreground=text_color,
                fieldbackground=dark_secondary,
                troughcolor=dark_secondary,
                selectbackground=accent_color,
                selectforeground=text_color
            )
        
            style.configure("TButton",
                background=dark_secondary,
                foreground=text_color,
                padding=5
            )
            style.map("TButton",
                background=[("active", dark_highlight), ("pressed", accent_color)],
                foreground=[("pressed", "white")]
            )
        
            style.configure("TCheckbutton",
                background=dark_bg,
                foreground=text_color
            )
            style.map("TCheckbutton",
                background=[("active", dark_bg)],
                foreground=[("active", accent_color)]
            )
        
            style.configure("TScrollbar",
                background=dark_secondary,
                troughcolor=dark_bg,
                borderwidth=0,
                arrowcolor=text_color
            )
        
            canvas.configure(
                bg=dark_bg,
                highlightbackground=dark_bg,
                highlightcolor=dark_secondary
            )
            log_text.configure(
                bg=dark_secondary,
                fg=text_color,
                insertbackground=text_color,
                selectbackground=dark_highlight,
                selectforeground=text_color,
                highlightbackground=dark_bg,
                highlightcolor=dark_secondary
            )
        
            for label in script_labels + background_labels:
                label.configure(background=dark_bg)
            
            for child in scrollable_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=dark_bg)
                
        else:
            light_bg = "#ffffff"
            light_secondary = "#f0f0f0"
            light_highlight = "#e0e0e0"
            text_color = "#000000"
            accent_color = "#0066cc"
        
            root.configure(bg=light_bg)
            bottom_panel.configure(bg=light_bg)
            main_container.configure(bg=light_bg)
            content_frame.configure(bg=light_bg)
            buttons_frame.configure(bg=light_bg)
            log_frame.configure(bg=light_bg)
            scrollable_frame.configure(bg=light_bg)
        
            style.configure(".",
                background=light_bg,
                foreground=text_color,
                fieldbackground=light_secondary,
                troughcolor=light_secondary,
                selectbackground=accent_color,
                selectforeground="white"
            )
        
            style.configure("TButton",
                background=light_secondary,
                foreground=text_color,
                padding=5
            )
            style.map("TButton",
                background=[("active", light_highlight), ("pressed", accent_color)],
                foreground=[("pressed", "white")]
            )
        
            style.configure("TCheckbutton",
                background=light_bg,
                foreground=text_color
            )
        
            style.configure("TScrollbar",
                background=light_secondary,
                troughcolor=light_bg,
                borderwidth=0,
                arrowcolor=text_color
            )
        
            canvas.configure(
                bg=light_bg,
                highlightbackground=light_bg,
                highlightcolor=light_secondary
            )
            log_text.configure(
                bg="white",
                fg=text_color,
                insertbackground=text_color,
                selectbackground=accent_color,
                selectforeground="white",
                highlightbackground=light_bg,
                highlightcolor=light_secondary
            )
        
            for label in script_labels + background_labels:
                label.configure(background=light_bg)
            
            for child in scrollable_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=light_bg)
    # Main layout containers
    main_container = tk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True)

    content_frame = tk.Frame(main_container)
    content_frame.pack(fill=tk.BOTH, expand=True)

    buttons_frame = tk.Frame(content_frame)
    buttons_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    # Scrollable canvas setup
    canvas = tk.Canvas(buttons_frame)
    buttons_scrollbar = ttk.Scrollbar(buttons_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=buttons_scrollbar.set)
    # Enhanced scrolling
    def handle_scroll(event, widget):
        if event.state == 0:
            widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
    
    canvas.bind("<MouseWheel>", lambda e: handle_scroll(e, canvas))
    
    def bind_scroll_to_children(parent, scroll_widget):
        for child in parent.winfo_children():
            child.bind("<MouseWheel>", lambda e: handle_scroll(e, scroll_widget))
            if child.winfo_children():
                bind_scroll_to_children(child, scroll_widget)
    
    bind_scroll_to_children(scrollable_frame, canvas)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    buttons_scrollbar.pack(side=tk.RIGHT, fill="y")
    # Log frame setup
    log_frame = tk.Frame(content_frame)
    log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    log_text = tk.Text(log_frame, wrap=tk.WORD, state='disabled', width=30)
    log_text.bind('<Control-c>', lambda e: handle_mouse_copy(e))
    log_text.bind('<Button-3>', handle_mouse_copy)
    log_text.bind("<MouseWheel>", lambda e: handle_scroll(e, log_text))
    
    log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    log_text.configure(yscrollcommand=log_scrollbar.set)

    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    log_scrollbar.pack(side=tk.RIGHT, fill="y")
    # Bottom control panel
    bottom_panel = tk.Frame(root)
    bottom_panel.pack(side=tk.BOTTOM, fill=tk.X)

    start_all_button = ttk.Button(
        bottom_panel, 
        text="Start All", 
        command=lambda: threading.Thread(
            target=start_all_scripts, 
            args=(scripts, script_labels), 
            daemon=True
        ).start()
    )
    start_all_button.pack(side=tk.LEFT, padx=5, pady=5)

    start_selected_button = ttk.Button(
        bottom_panel,
        text="Start Selected",
        command=start_selected_scripts
    )
    start_selected_button.pack(side=tk.LEFT, padx=5, pady=5)

    background_checkbox = ttk.Checkbutton(
        bottom_panel,
        text="Background Mode",
        variable=background_mode,
        command=update_kill_buttons_visibility,
        style="Switch.TCheckbutton"
    )
    background_checkbox.pack(side=tk.LEFT, padx=5, pady=5)

    credits_button = ttk.Button(bottom_panel, text="О программе", command=show_credits)
    credits_button.pack(side=tk.RIGHT, padx=5, pady=5)
    theme_button = ttk.Button(
        bottom_panel,
        text="☀️ Light Mode" if is_dark_mode else "🌙 Dark Mode",
        command=toggle_theme
    )
    theme_button.pack(side=tk.RIGHT, padx=5, pady=5)
    
    bottom_frame = ttk.Frame(root)
    bottom_frame.pack(side='bottom', fill='x', pady=5)

    # Create script rows
    for script in scripts:
        script_folder = os.path.basename(os.path.dirname(script))
        
        row_frame = tk.Frame(scrollable_frame)
        row_frame.pack(fill=tk.X)

        script_label = ttk.Label(row_frame, text="❌", foreground="red", width=3)
        script_label.pack(side=tk.LEFT)

        background_label = ttk.Label(row_frame, text="⚪", foreground="gray", width=3)
        background_label.pack(side=tk.LEFT)

        saved_states = config.get('checkbox_states', {}).get(script_folder, {}).get('states', {'1': 0, '2': 0, '3': 0})
        
        checkbox_vars_1[script] = tk.IntVar(value=saved_states.get('1', 0))
        checkbox_vars_2[script] = tk.IntVar(value=saved_states.get('2', 0))
        checkbox_vars_3[script] = tk.IntVar(value=saved_states.get('3', 0))

        cb1 = ttk.Checkbutton(row_frame, variable=checkbox_vars_1[script], text="1",
                             command=lambda s=script, v=checkbox_vars_1[script], 
                             o=[checkbox_vars_2[script], checkbox_vars_3[script]]: 
                             on_checkbox_click(s, v, o))
        cb2 = ttk.Checkbutton(row_frame, variable=checkbox_vars_2[script], text="2",
                             command=lambda s=script, v=checkbox_vars_2[script], 
                             o=[checkbox_vars_1[script], checkbox_vars_3[script]]: 
                             on_checkbox_click(s, v, o))
        cb3 = ttk.Checkbutton(row_frame, variable=checkbox_vars_3[script], text="3",
                             command=lambda s=script, v=checkbox_vars_3[script], 
                             o=[checkbox_vars_1[script], checkbox_vars_2[script]]: 
                             on_checkbox_click(s, v, o))
        
        cb1.pack(side=tk.LEFT, padx=2)
        cb2.pack(side=tk.LEFT, padx=2)
        cb3.pack(side=tk.LEFT, padx=2)

        button = ttk.Button(
            row_frame, 
            text=script_folder, 
            command=lambda s=script, l=script_label: start_script(s, l)
        )
        button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        kill_button = ttk.Button(
            row_frame,
            text="Kill",
            command=lambda s=script: kill_process(s)
        )
        kill_button_pairs.append((kill_button, row_frame))
        if background_mode.get():
            kill_button.pack(side=tk.RIGHT, padx=2)

        script_labels.append(script_label)
        background_labels.append(background_label)

    def on_closing():
        config['background_mode'] = background_mode.get()
        save_config(config)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    apply_theme()
    return root

if __name__ == "__main__":
    scripts = get_scripts(config['paths_to_scan'], config['exclude_folders'])
    update_bot_config(scripts)  # Add this line
    root = create_gui(scripts)
    
    monitoring_thread = threading.Thread(target=monitor_scripts, args=(scripts, script_labels), daemon=True)
    monitoring_thread.start()

    background_monitoring_thread = threading.Thread(target=monitor_background_processes, args=(scripts,), daemon=True)
    background_monitoring_thread.start()

    log_thread = threading.Thread(target=process_log_queue, args=(log_text,), daemon=True)
    log_thread.start()

    root.mainloop()
