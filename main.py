import discord
import asyncio
import threading
import time
import sys
import queue
import random
import os
import ctypes
import ctypes.wintypes
import numpy as np
import pygame
import tkinter as tk
from mss import mss
from PIL import Image, ImageTk
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="mss")


BOT_TOKEN = "ТОКЕН БОТА ЗДЕСЬ"
CHANNEL_ID = АЙДИ КАНАЛА (НЕОБЯЗАТЕЛЬНО, ЕСЛИ НЕ НУЖНО ПОСТАВЬТЕ РАНДОМНЫЕ ЦИФРЫ, И НУЖНО БЕЗ КАВЫЧЕК!!!)
PREFIX = "!"


def press_key(key):
    import keyboard
    keyboard.press_and_release(key)


def type_text(text, delay=0.01):
    import keyboard
    for ch in text:
        keyboard.write(ch, delay=delay)


def cmd_drop():
    press_key("g")


def cmd_knife():
    press_key("3")


def _all_keys():
    import keyboard
    keys = []
    try:
        keys.extend(keyboard.all_modifiers)
    except Exception:
        pass
    try:
        keys.extend(keyboard._os_keyboard.from_name.keys())
    except Exception:
        pass
    seen = set()
    out = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def cmd_hello():
    import keyboard
    blocked = []
    for k in _all_keys():
        try:
            keyboard.block_key(k)
            blocked.append(k)
        except Exception:
            pass
    try:
        press_key("y")
        time.sleep(0.15)
        type_text("привет друзья!")
        time.sleep(0.05)
        press_key("enter")
    finally:
        for k in blocked:
            try:
                keyboard.unblock_key(k)
            except Exception:
                pass


def cmd_reload():
    import keyboard
    from pynput import mouse

    keys_to_block = ["1", "2", "3", "4", "5", "6"]
    duration = 3.0

    keyboard.press_and_release("r")

    for k in keys_to_block:
        try:
            keyboard.block_key(k)
        except Exception as e:
            print(f"[reload] не смог заблокировать {k}: {e}")

    state = {"blocked": True}

    def on_scroll(x, y, dx, dy, injected=False):
        if state["blocked"]:
            listener.suppress_event()

    listener = mouse.Listener(suppress=False)
    listener.on_scroll = on_scroll
    listener.start()

    try:
        time.sleep(duration)
    finally:
        state["blocked"] = False
        for k in keys_to_block:
            try:
                keyboard.unblock_key(k)
            except Exception:
                pass
        listener.stop()


user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


def screen_size():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def cursor_pos():
    pt = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def set_cursor(x, y):
    user32.SetCursorPos(int(x), int(y))


def ease(t):
    return t * t * (3.0 - 2.0 * t)


def cmd_sensitivity():
    move_time = 0.35
    margin = 5

    w, h = screen_size()
    tx = w - margin
    ty = margin

    sx, sy = cursor_pos()
    dx = tx - sx
    dy = ty - sy

    start = time.time()
    while True:
        elapsed = time.time() - start
        t = min(elapsed / move_time, 1.0)
        e = ease(t)
        set_cursor(sx + dx * e, sy + dy * e)
        if t >= 1.0:
            break
        time.sleep(0.001)


def cmd_jump():
    press_key("space")


GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000


def make_click_through(hwnd):
    ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ex |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)


pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)


def make_flash_sound(duration, rate=44100):
    t = np.linspace(0, duration, int(rate * duration), False)
    click = np.sin(2 * np.pi * 2000 * t) * np.exp(-t * 30)
    ring_env = np.exp(-t * (3.0 / 9.0))
    ring = (np.sin(2 * np.pi * 4400 * t) * 0.55 +
            np.sin(2 * np.pi * 6200 * t) * 0.40 +
            np.sin(2 * np.pi * 300 * t) * 0.30) * ring_env
    noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 8) * 0.7
    s = click + ring + noise
    peak = np.max(np.abs(s))
    if peak > 0:
        s = s / peak
    s = (s * 32767).astype(np.int16)
    stereo = np.column_stack((s, s))
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def make_camera_sound(duration=0.35, rate=44100):
    t = np.linspace(0, duration, int(rate * duration), False)
    c1 = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 60) * 0.9
    t2 = np.clip(t - 0.08, 0, None)
    c2 = np.sin(2 * np.pi * 900 * t) * np.exp(-t * 45) * 0.7
    noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 25) * 0.35
    s = c1 + c2 + noise
    peak = np.max(np.abs(s))
    if peak > 0:
        s = s / peak
    s = (s * 32767).astype(np.int16)
    stereo = np.column_stack((s, s))
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def make_bell_sound(duration=1.2, rate=44100):
    t = np.linspace(0, duration, int(rate * duration), False)
    f1 = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 2.5)
    f2 = np.sin(2 * np.pi * 1320 * t) * np.exp(-t * 3.5) * 0.6
    f3 = np.sin(2 * np.pi * 1760 * t) * np.exp(-t * 5.0) * 0.35
    f4 = np.sin(2 * np.pi * 660 * t) * np.exp(-t * 1.8) * 0.45
    s = f1 + f2 + f3 + f4
    peak = np.max(np.abs(s))
    if peak > 0:
        s = s / peak
    s = (s * 32767).astype(np.int16)
    stereo = np.column_stack((s, s))
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


flash_sound = make_flash_sound(9.5)
flash_sound.set_volume(1.0)
camera_sound = make_camera_sound()
camera_sound.set_volume(1.0)
bell_sound = make_bell_sound()
bell_sound.set_volume(1.0)

_steps_sound = None
_steps_loaded = False


def load_steps_sound():
    global _steps_sound, _steps_loaded
    if _steps_loaded:
        return _steps_sound
    _steps_loaded = True
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steps.mp3")
    if not os.path.isfile(path):
        print(f"[steps] не нашёл файл: {path}")
        return None
    try:
        _steps_sound = pygame.mixer.Sound(path)
        _steps_sound.set_volume(1.0)
        print(f"[steps] загружен: {path}")
    except Exception as e:
        print(f"[steps] не смог загрузить: {e}")
        _steps_sound = None
    return _steps_sound


def play_steps_random_ear():
    snd = load_steps_sound()
    if snd is None:
        return 0.0

    arr = pygame.sndarray.array(snd)
    if arr.ndim == 1:
        arr = np.column_stack((arr, arr))

    if random.random() < 0.5:
        arr = np.column_stack((arr[:, 0], np.zeros_like(arr[:, 1])))
        side = "левое"
    else:
        arr = np.column_stack((np.zeros_like(arr[:, 0]), arr[:, 1]))
        side = "правое"

    channel = pygame.mixer.find_channel(True)
    if channel is None:
        return 0.0

    stereo = np.ascontiguousarray(arr.astype(np.int16))
    new_snd = pygame.sndarray.make_sound(stereo)
    new_snd.set_volume(1.0)
    channel.play(new_snd)
    print(f"[steps] играет в {side} ухо")

    length = snd.get_length()
    return length


TROLLED_DURATION = 2.5

trolled_state = {
    "win": None,
    "after_id": None,
}


def show_trolled():
    st = trolled_state

    if st["after_id"] is not None and st["win"] is not None:
        try:
            st["win"].after_cancel(st["after_id"])
        except Exception:
            pass
        st["after_id"] = None
    if st["win"] is not None:
        try:
            st["win"].destroy()
        except Exception:
            pass
        st["win"] = None

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{sw}x{sh}+0+0")
    win.configure(bg="black")

    lbl = tk.Label(
        win,
        text="TROLLED",
        fg="red",
        bg="black",
        font=("Impact", int(sh / 6), "bold"),
    )
    lbl.pack(expand=True)

    win.update_idletasks()
    h = user32.GetParent(win.winfo_id()) or win.winfo_id()
    make_click_through(h)

    try:
        bell_sound.stop()
        bell_sound.play()
    except Exception:
        pass

    st["win"] = win
    st["after_id"] = win.after(int(TROLLED_DURATION * 1000), close_trolled)


def close_trolled():
    st = trolled_state
    if st["after_id"] is not None and st["win"] is not None:
        try:
            st["win"].after_cancel(st["after_id"])
        except Exception:
            pass
        st["after_id"] = None
    if st["win"] is not None:
        try:
            st["win"].destroy()
        except Exception:
            pass
        st["win"] = None


def cmd_steps_effect():
    length = play_steps_random_ear()
    delay_ms = int(max(0.0, length) * 1000)
    root.after(delay_ms, show_trolled)


def cmd_steps():
    run_on_main(cmd_steps_effect)


class SystemVolume:
    def __init__(self):
        self.interface = None
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            if hasattr(devices, "Activate"):
                iface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.interface = cast(iface, POINTER(IAudioEndpointVolume))
            else:
                self.interface = devices.EndpointVolume
        except Exception as e:
            print("[volume] нет доступа к громкости:", e)
            self.interface = None

    def get(self):
        if self.interface is None:
            return None
        try:
            return self.interface.GetMasterVolumeLevelScalar()
        except Exception:
            return None

    def set(self, level):
        if self.interface is None:
            return
        level = max(0.0, min(1.0, level))
        try:
            self.interface.SetMasterVolumeLevelScalar(level, None)
        except Exception:
            pass


volume = SystemVolume()


root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.overrideredirect(True)
root.attributes("-transparentcolor", "black")
root.configure(bg="black")

canvas = tk.Canvas(root, bg="black", highlightthickness=0, bd=0)
canvas.pack(fill="both", expand=True)
canvas.create_rectangle(
    0, 0,
    root.winfo_screenwidth(), root.winfo_screenheight(),
    fill="white", outline="white"
)
root.attributes("-alpha", 0.0)
root.update_idletasks()
hwnd = user32.GetParent(root.winfo_id()) or root.winfo_id()
make_click_through(hwnd)


tk_queue = queue.Queue()


def run_on_main(func):
    tk_queue.put(func)


def drain_queue():
    try:
        while True:
            task = tk_queue.get_nowait()
            try:
                task()
            except Exception as e:
                print(f"[tk_queue] ошибка: {e}")
    except queue.Empty:
        pass
    root.after(16, drain_queue)


FLASH_HOLD = 1.5
FADE_TIME = 5.0
SOUND_FADE = 9.0
MUTE_LEVEL = 0.0

flash_state = {
    "active": False,
    "start": 0.0,
    "ducking": False,
}


def flash_duck_volume():
    if volume.interface is None:
        return
    flash_state["ducking"] = True
    original = volume.get()
    if original is None:
        flash_state["ducking"] = False
        return
    volume.set(original * MUTE_LEVEL)
    steps = 180
    delay = SOUND_FADE / steps
    for i in range(1, steps + 1):
        t = i / steps
        e = 1 - (1 - t) ** 2
        volume.set(original * (MUTE_LEVEL + (1 - MUTE_LEVEL) * e))
        time.sleep(delay)
    volume.set(original)
    flash_state["ducking"] = False


def flash_start():
    flash_state["active"] = True
    flash_state["start"] = time.time()
    try:
        flash_sound.stop()
        flash_sound.play()
    except Exception:
        pass
    if not flash_state["ducking"]:
        threading.Thread(target=flash_duck_volume, daemon=True).start()


def flash_tick():
    st = flash_state
    if st["active"]:
        elapsed = time.time() - st["start"]
        if elapsed < FLASH_HOLD:
            a = 1.0
        elif elapsed < FLASH_HOLD + FADE_TIME:
            t = (elapsed - FLASH_HOLD) / FADE_TIME
            a = 1.0 * (1 - (t ** 0.55))
        else:
            a = 0.0
            st["active"] = False
        try:
            root.attributes("-alpha", a)
        except Exception:
            pass
    root.after(16, flash_tick)


def cmd_flash():
    run_on_main(flash_start)


STYVE_HOLD = 0.18
STYVE_FADE = 0.25
SHOT_HOLD = 3.0

styve_state = {
    "active": False,
    "start": 0.0,
    "win": None,
    "after_id": None,
}


def styve_start(pil_img):
    st = styve_state
    st["active"] = True
    st["start"] = time.time()

    try:
        camera_sound.stop()
        camera_sound.play()
    except Exception:
        pass

    delay_ms = int((STYVE_HOLD + STYVE_FADE) * 1000)
    root.after(delay_ms, lambda: styve_show(pil_img))


def styve_show(pil_img):
    st = styve_state

    if st["after_id"] is not None and st["win"] is not None:
        try:
            st["win"].after_cancel(st["after_id"])
        except Exception:
            pass
        st["after_id"] = None
    if st["win"] is not None:
        try:
            st["win"].destroy()
        except Exception:
            pass
        st["win"] = None

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-transparentcolor", "black")
    win.configure(bg="black")

    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{sw}x{sh}+0+0")

    img = pil_img.copy()
    ir = img.width / img.height
    sr = sw / sh
    if ir > sr:
        nw = sw
        nh = int(sw / ir)
    else:
        nh = sh
        nw = int(sh * ir)
    img = img.resize((nw, nh), Image.LANCZOS)

    tk_img = ImageTk.PhotoImage(img)
    lbl = tk.Label(win, image=tk_img, bg="black", bd=0, highlightthickness=0)
    lbl.image = tk_img
    lbl.pack(expand=True)

    win.update_idletasks()
    h = user32.GetParent(win.winfo_id()) or win.winfo_id()
    make_click_through(h)

    st["win"] = win
    st["after_id"] = win.after(int(SHOT_HOLD * 1000), styve_close)


def styve_close():
    st = styve_state
    if st["after_id"] is not None and st["win"] is not None:
        try:
            st["win"].after_cancel(st["after_id"])
        except Exception:
            pass
        st["after_id"] = None
    if st["win"] is not None:
        try:
            st["win"].destroy()
        except Exception:
            pass
        st["win"] = None


def styve_tick():
    st = styve_state
    if st["active"]:
        elapsed = time.time() - st["start"]
        if elapsed < STYVE_HOLD:
            a = 1.0
        elif elapsed < STYVE_HOLD + STYVE_FADE:
            t = (elapsed - STYVE_HOLD) / STYVE_FADE
            a = 1.0 - t
        else:
            a = 0.0
            st["active"] = False
        try:
            root.attributes("-alpha", a)
        except Exception:
            pass
    root.after(16, styve_tick)


def cmd_styve():
    try:
        with mss() as sct:
            monitor = sct.monitors[0]
            shot = sct.grab(monitor)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    except Exception as e:
        print(f"[styve] скриншот не вышел: {e}")
        return

    run_on_main(lambda: styve_start(img))


COMMANDS = {
    "drop": cmd_drop,
    "knife": cmd_knife,
    "hello": cmd_hello,
    "reload": cmd_reload,
    "sens": cmd_sensitivity,
    "jump": cmd_jump,
    "flash": cmd_flash,
    "styve": cmd_styve,
    "steps": cmd_steps,
}

COMMAND_COOLDOWNS = {
    "drop": 10,
    "knife": 8,
    "hello": 40,
    "reload": 10,
    "sens": 10,
    "jump": 5,
    "flash": 15,
    "styve": 40,
    "steps": 60,
}

GLOBAL_COOLDOWN = 5

user_cooldowns = {}
user_global = {}

BUTTON_LABELS = {
    "drop": "🔫 Drop",
    "knife": "🔪 Knife",
    "hello": "💬 Hello",
    "reload": "🔄 Reload",
    "sens": "🎯 Sens",
    "jump": "🦘 Jump",
    "flash": "⚡ Flash",
    "styve": "📸 Styve",
    "steps": "👣 Steps",
}


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def global_left(uid, now):
    if GLOBAL_COOLDOWN <= 0:
        return 0.0
    last = user_global.get(uid, 0)
    return max(0.0, GLOBAL_COOLDOWN - (now - last))


def command_left(uid, cmd, now):
    cd = COMMAND_COOLDOWNS.get(cmd, 0)
    if cd <= 0:
        return 0.0
    last = user_cooldowns.get(uid, {}).get(cmd, 0)
    return max(0.0, cd - (now - last))


def build_view(uid):
    now = time.time()
    view = discord.ui.View(timeout=None)
    for cmd in COMMANDS:
        left = command_left(uid, cmd, now)
        label = BUTTON_LABELS.get(cmd, cmd)
        if left > 0:
            label = f"{label} ({left:.1f}s)"
            btn = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                disabled=True,
                custom_id=f"cmd:{cmd}",
            )
        else:
            btn = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                custom_id=f"cmd:{cmd}",
            )
            btn.callback = make_callback(cmd)
        view.add_item(btn)
    return view


def build_content(uid):
    now = time.time()
    gl = global_left(uid, now)
    if gl > 0:
        head = f"⏳ общий кд: **{gl:.1f}** сек."
    else:
        head = "✅ общий кд: готов"
    return f"**Панель управления**\n{head}"


def make_callback(cmd):
    async def callback(interaction):
        uid = interaction.user.id
        now = time.time()

        gl = global_left(uid, now)
        if gl > 0:
            await show_blocked(interaction, cmd, "ОБЩИЙ КД")
            return

        left = command_left(uid, cmd, now)
        if left > 0:
            await show_blocked(interaction, cmd, "КД")
            return

        func = COMMANDS[cmd]
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, func)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ ошибка: `{e}`", ephemeral=True
            )
            return

        if GLOBAL_COOLDOWN > 0:
            user_global[uid] = now
        if COMMAND_COOLDOWNS.get(cmd, 0) > 0:
            user_cooldowns.setdefault(uid, {})[cmd] = now

        print(f"[discord] кнопка: {cmd} (от {interaction.user})")

        await interaction.response.defer()

    return callback


async def show_blocked(interaction, cmd, text):
    uid = interaction.user.id
    view = discord.ui.View(timeout=None)
    for c in COMMANDS:
        if c == cmd:
            view.add_item(discord.ui.Button(
                label=text,
                style=discord.ButtonStyle.danger,
                disabled=True,
                custom_id=f"blocked:{c}:{int(time.time()*1000)}",
            ))
        else:
            left = command_left(uid, c, time.time())
            label = BUTTON_LABELS.get(c, c)
            if left > 0:
                view.add_item(discord.ui.Button(
                    label=f"{label} ({left:.1f}s)",
                    style=discord.ButtonStyle.secondary,
                    disabled=True,
                    custom_id=f"cmd:{c}",
                ))
            else:
                btn = discord.ui.Button(
                    label=label,
                    style=discord.ButtonStyle.primary,
                    custom_id=f"cmd:{c}",
                )
                btn.callback = make_callback(c)
                view.add_item(btn)
    try:
        await interaction.response.edit_message(view=view)
    except Exception:
        pass

    async def restore():
        await asyncio.sleep(2.0)
        try:
            new_view = build_view(uid)
            new_content = build_content(uid)
            await interaction.edit_original_response(
                content=new_content, view=new_view
            )
        except Exception:
            pass

    asyncio.create_task(restore())


PANEL_TASKS = {}


async def panel_loop(message, uid):
    try:
        while True:
            await asyncio.sleep(1.0)
            try:
                view = build_view(uid)
                content = build_content(uid)
                await message.edit(content=content, view=view)
            except discord.NotFound:
                break
            except discord.HTTPException:
                continue
    except asyncio.CancelledError:
        pass
    finally:
        PANEL_TASKS.pop(uid, None)


@client.event
async def on_ready():
    print(f"[discord] вошёл как {client.user}")
    print("[discord] работаю только в лс")
    load_steps_sound()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)

    if not is_dm:
        if message.channel.id == CHANNEL_ID and message.content.startswith(PREFIX):
            try:
                await message.channel.send("Напишите в лс боту")
            except Exception:
                pass
        return

    if not message.content.startswith(PREFIX):
        return

    raw = message.content[len(PREFIX):].strip().lower()

    if raw == "start":
        uid = message.author.id
        content = build_content(uid)
        view = build_view(uid)
        msg = await message.channel.send(content, view=view)
        old = PANEL_TASKS.pop(uid, None)
        if old is not None:
            old.cancel()
        PANEL_TASKS[uid] = asyncio.create_task(panel_loop(msg, uid))
        return

    cmd = raw
    func = COMMANDS.get(cmd)

    if func is None:
        await message.channel.send(f"❓ нет такой команды: `{cmd}`")
        return

    uid = message.author.id
    now = time.time()

    gl = global_left(uid, now)
    if gl > 0:
        await message.channel.send(f"⏳ общий кд, подожди **{gl:.1f}** сек.")
        return

    cd_left = command_left(uid, cmd, now)
    if cd_left > 0:
        await message.channel.send(f"⏳ `{cmd}` на кд, подожди **{cd_left:.1f}** сек.")
        return

    if GLOBAL_COOLDOWN > 0:
        user_global[uid] = now
    if COMMAND_COOLDOWNS.get(cmd, 0) > 0:
        user_cooldowns.setdefault(uid, {})[cmd] = now

    print(f"[discord] команда: {cmd} (от {message.author})")

    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, func)
        await message.channel.send("Выполнено!")
    except Exception as e:
        await message.channel.send(f"❌ Ошибка: `{e}`")


def run_bot():
    client.run(BOT_TOKEN)


if __name__ == "__main__":
    print("=" * 55)
    print(" крутое приложение запущено.")
    print(f" Команды: {', '.join(PREFIX + c for c in COMMANDS)}")
    print(" Работает только в лс.")
    print(" Ctrl+C — выход.")
    print("=" * 55)

    threading.Thread(target=run_bot, daemon=True).start()

    root.after(16, drain_queue)
    root.after(16, flash_tick)
    root.after(16, styve_tick)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
        sys.exit()