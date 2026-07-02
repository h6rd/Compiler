import os
import sys
import shutil
import subprocess
import time
import winreg
import string
import zipfile
import urllib.request
import re
from pathlib import Path

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False

if getattr(sys, 'frozen', False):
    SCRIPT_DIR = Path(sys.executable).parent
else:
    SCRIPT_DIR = Path(__file__).parent

OUTPUT_DIR = SCRIPT_DIR

DOTA_CONTENT = None
DOTA_GAME = None
COMPILER = None

COMPILER_URL = "https://raw.githubusercontent.com/h6rd/Compiler/refs/heads/main/d2pfx_compiler.zip"

FILE_CONFIGS = {
    'png': {
        'content_subdir': 'panorama/images',
        'game_subdir': 'panorama/images',
        'output_ext': '.vtex_c',
        'needs_xml': True,
        'compile_method': 'xml'
    },
    'css': {
        'content_subdir': 'panorama/styles',
        'game_subdir': 'panorama/styles',
        'output_ext': '.vcss_c',
        'needs_xml': False,
        'compile_method': 'direct'
    },
    'xml': {
        'content_subdir': 'panorama/layout',
        'game_subdir': 'panorama/layout',
        'output_ext': '.vxml_c',
        'needs_xml': False,
        'compile_method': 'direct'
    },
    'vpcf': {
        'content_subdir': 'particles',
        'game_subdir': 'particles',
        'output_ext': '.vpcf_c',
        'needs_xml': False,
        'compile_method': 'direct'
    },
    'mp3': {
        'content_subdir': 'sounds',
        'game_subdir': 'sounds',
        'output_ext': '.vsnd_c',
        'needs_xml': False,
        'compile_method': 'direct'
    },
    'wav': {
        'content_subdir': 'sounds',
        'game_subdir': 'sounds',
        'output_ext': '.vsnd_c',
        'needs_xml': False,
        'compile_method': 'direct'
    }
}

def print_ascii_art():
    if HAS_RICH:
        width = console.size.width
        PURPLE = "#B486FF"
        WHITE = "white"

        lines = [
            r" ██████╗ ██████╗ ███╗   ███╗██████╗ ██╗██╗     ███████╗██████╗ ",
            r"██╔════╝██╔═══██╗████╗ ████║██╔══██╗██║██║     ██╔════╝██╔══██╗",
            r"██║     ██║   ██║██╔████╔██║██████╔╝██║██║     █████╗  ██████╔╝",
            r"██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██║██║     ██╔══╝  ██╔══██╗",
            r"╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ██║███████╗███████╗██║  ██║",
            r" ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝",
            "by @dota2pornfx"
        ]                                                    

        console.print()
        for line in lines[:-1]:
            console.print(Text(line.center(width), style=PURPLE))
        console.print(Text(lines[-1].center(width), style=WHITE))
        console.print()
    else:
        print("VPKTool")
        print("by @dota2pornfx")

def print_status(message, status="info"):
    if HAS_RICH:
        if status == "success":
            console.print(f"[green]✓[/green] {message}")
        elif status == "error":
            console.print(f"[red]✗[/red] {message}")
        elif status == "warning":
            console.print(f"[yellow]![/yellow] {message}")
        else:
            console.print(f"[cyan]→[/cyan] {message}")
    else:
        prefix = {"success": "[OK]", "error": "[ERR]", "warning": "[WARN]", "info": "→"}.get(status, "→")
        print(f"{prefix} {message}")

def find_steam_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
        winreg.CloseKey(key)
        return steam_path
    except:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
            winreg.CloseKey(key)
            return steam_path
        except:
            return None

def validate_dota_path(path):
    if not os.path.exists(path):
        return False
    
    compiler_path = os.path.join(path, "game", "bin", "win64", "resourcecompiler.exe")
    game_folder = os.path.join(path, "game", "dota")
    
    if not os.path.exists(compiler_path) or not os.path.exists(game_folder):
        return False
        
    return True

def search_all_drives():
    print_status("Searching for Dota 2 across all drives...")

    available_drives = [f"{letter}:\\" for letter in string.ascii_uppercase if os.path.exists(f"{letter}:\\")]

    common_paths = [
        "SteamLibrary\\steamapps\\common\\dota 2 beta",
        "Steam\\steamapps\\common\\dota 2 beta",
        "Program Files (x86)\\Steam\\steamapps\\common\\dota 2 beta",
        "Program Files\\Steam\\steamapps\\common\\dota 2 beta",
    ]
    
    for drive in available_drives:
        for path in common_paths:
            full_path = os.path.join(drive, path)
            if os.path.exists(full_path) and validate_dota_path(full_path):
                print_status(f"Found Dota 2 at {full_path}", "success")
                return full_path
    return None

def find_dota_path():
    steam_path = find_steam_path()
    
    if steam_path:
        print_status("Found Steam")
        default_dota = os.path.join(steam_path, "steamapps", "common", "dota 2 beta")
        if os.path.exists(default_dota) and validate_dota_path(default_dota):
            return default_dota

        library_file = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(library_file):
            try:
                with open(library_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                paths = re.findall(r'"path"\s+"([^"]+)"', content)
                for lib_path in paths:
                    lib_path = lib_path.replace("\\\\", "\\")
                    dota_path = os.path.join(lib_path, "steamapps", "common", "dota 2 beta")
                    if os.path.exists(dota_path) and validate_dota_path(dota_path):
                        return dota_path
            except Exception as e:
                print_status(f"Error parsing library folders: {e}", "error")
    
    return search_all_drives()

def download_compiler(dota_path):
    print_status("Downloading compiler addon[white]...[/white]")
    
    content_addons = os.path.join(dota_path, "content", "dota_addons")
    game_addons = os.path.join(dota_path, "game", "dota_addons")

    os.makedirs(content_addons, exist_ok=True)
    os.makedirs(game_addons, exist_ok=True)
    
    zip_path = os.path.join(SCRIPT_DIR, "d2pfx_compiler.zip")
    
    try:
        urllib.request.urlretrieve(COMPILER_URL, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(content_addons)

        game_img_compiler = os.path.join(game_addons, "d2pfx_compiler")
        os.makedirs(os.path.join(game_img_compiler, "panorama", "images"), exist_ok=True)
        print_status("Addon installed successfully", "success")

        try:
            os.remove(zip_path)
        except:
            pass
        return True
    except Exception as e:
        print_status(f"Failed to download addon: {e}", "error")
        return False

def initialize_paths():
    global DOTA_CONTENT, DOTA_GAME, COMPILER
    
    dota_path = find_dota_path()
    if not dota_path:
        print_status("Could not find Dota 2 installation", "error")
        return False

    DOTA_CONTENT = os.path.join(dota_path, "content", "dota_addons", "d2pfx_compiler")
    DOTA_GAME = os.path.join(dota_path, "game", "dota_addons", "d2pfx_compiler")
    COMPILER = os.path.join(dota_path, "game", "bin", "win64", "resourcecompiler.exe")

    if not os.path.exists(COMPILER):
        print_status("Compiler not found", "error")
        return False

    if not os.path.exists(DOTA_CONTENT) and not download_compiler(dota_path):
        return False

    for config in FILE_CONFIGS.values():
        os.makedirs(os.path.join(DOTA_CONTENT, config['content_subdir']), exist_ok=True)
        os.makedirs(os.path.join(DOTA_GAME, config['game_subdir']), exist_ok=True)
    
    print_status("Initialization complete", "success")
    return True

def update_xml(png_name):
    xml_path = os.path.join(DOTA_CONTENT, "panorama", "images", "111.xml")
    xml_content = f"""<root> 
<Panel class="AddonLoadingRoot"> 
<Image id="gamemode" class="SeqImg" src="file://{{images}}/{png_name}" />
</Panel>
</root>"""
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)

def compile_direct(file_path):
    cmd = f'"{COMPILER}" -f "{file_path}"'
    try:
        subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return True
    except:
        return False

def compile_with_xml(content_dir):
    cmd = f'"{COMPILER}" -r "{content_dir}\\*.*"'
    try:
        subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return True
    except:
        return False

def process_file(file_path):
    ext = file_path.suffix[1:].lower()
    if ext not in FILE_CONFIGS:
        return False
    
    config = FILE_CONFIGS[ext]
    file_name = file_path.name
    file_stem = file_path.stem
    
    if HAS_RICH:
        console.print(f"Processing [#B486FF]{file_name}[/#B486FF][white]...[/white]", end=" ")
    else:
        print(f"Processing {file_name}...", end=" ")

    content_dir = os.path.join(DOTA_CONTENT, config['content_subdir'])
    game_dir = os.path.join(DOTA_GAME, config['game_subdir'])
    
    dest_file = os.path.join(content_dir, file_name)
    try:
        shutil.copy2(file_path, dest_file)
    except:
        console.print("[red]Failed (copy)[/red]") if HAS_RICH else print("Failed (copy)")
        return False

    if config['compile_method'] == 'xml':
        update_xml(file_name)
        if not compile_with_xml(content_dir):
            console.print("[red]Failed (compile)[/red]") if HAS_RICH else print("Failed (compile)")
            return False
    else:
        if not compile_direct(dest_file):
            console.print("[red]Failed (compile)[/red]") if HAS_RICH else print("Failed (compile)")
            return False

    time.sleep(1)

    if ext == 'png':
        compiled_file = os.path.join(game_dir, f"{file_stem}_png.vtex_c")
        final_name = f"{file_stem}.vtex_c"
    else:
        compiled_file = os.path.join(game_dir, f"{file_stem}{config['output_ext']}")
        final_name = f"{file_stem}{config['output_ext']}"
    
    if not os.path.exists(compiled_file):
        console.print("[red]Failed (output not found)[/red]") if HAS_RICH else print("Failed (output not found)")
        return False
        
    final_output = OUTPUT_DIR / final_name
    
    try:
        if ext == 'png':
            final_game = os.path.join(game_dir, final_name)
            if os.path.exists(final_game):
                os.remove(final_game)
            os.rename(compiled_file, final_game)
            shutil.move(final_game, final_output)
        else:
            shutil.move(compiled_file, final_output)
    except:
        console.print("[red]Failed (move)[/red]") if HAS_RICH else print("Failed (move)")
        return False

    try:
        os.remove(dest_file)
        os.remove(file_path)
    except:
        pass
    
    console.print("[green]✓[/green]") if HAS_RICH else print("Done")
    return True

def main():
    print_ascii_art()

    if not initialize_paths():
        input("\nPress Enter to exit...")
        return

    all_files = []
    for ext in FILE_CONFIGS.keys():
        all_files.extend(list(SCRIPT_DIR.glob(f"*.{ext}")))
    
    if not all_files:
        print_status("No supported files found", "warning")
        if HAS_RICH:
            console.print("\n[dim]Supported formats:[/dim] png, css, xml, vpcf, mp3, wav")
        else:
            print("\nSupported formats: png, css, xml, vpcf, mp3, wav")
        input("\nPress Enter to exit...")
        return

    if HAS_RICH:
        console.print(f"\nFound [cyan]{len(all_files)}[/cyan] files to process:\n")
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="cyan")
        table.add_column(style="white")
        
        file_counts = {}
        for f in all_files:
            ext = f.suffix[1:].upper()
            file_counts[ext] = file_counts.get(ext, 0) + 1
        
        for ext, count in sorted(file_counts.items()):
            table.add_row(ext, f"{count} file{'s' if count > 1 else ''}")
        
        console.print(table)
        console.print()
    else:
        print(f"\nFound {len(all_files)} file(s) to process\n")
    
    success_count = 0
    fail_count = 0
    
    for file_path in all_files:
        if process_file(file_path):
            success_count += 1
        else:
            fail_count += 1

    if HAS_RICH:
        console.print()
        summary = f"[green]{success_count}[/green] files compiled successfully"
        if fail_count > 0:
            summary += f" • [red]{fail_count} failed[/red]"
        console.print(summary)
    else:
        print(f"\nCompleted: {success_count} successful, {fail_count} failed")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()