import hashlib
import os
import time
from pathlib import Path

FILES_DIR = Path("./Files")
BASELINE_FILE = Path("./baseline.txt")


def calculate_file_hash(filepath):
    """Calculate the SHA-512 hash of a file."""
    sha512 = hashlib.sha512()

    try:
        with open(filepath, "rb") as file:
            while chunk := file.read(8192):
                sha512.update(chunk)

        return sha512.hexdigest()

    except (PermissionError, FileNotFoundError, OSError):
        return None


def erase_baseline_if_already_exists():
    """Delete baseline.txt if it already exists."""
    if BASELINE_FILE.exists():
        BASELINE_FILE.unlink()


def collect_baseline():
    """Create a new baseline of files and their SHA-512 hashes."""

    if not FILES_DIR.exists():
        print(f"[ERROR] Directory not found: {FILES_DIR.resolve()}")
        return

    erase_baseline_if_already_exists()

    files = [file for file in FILES_DIR.iterdir() if file.is_file()]

    with open(BASELINE_FILE, "w", encoding="utf-8") as baseline:

        for file in files:
            filepath = file.resolve()
            file_hash = calculate_file_hash(filepath)

            if file_hash:
                baseline.write(f"{filepath}|{file_hash}\n")

    print(f"[+] Baseline created successfully.")
    print(f"[+] Files recorded: {len(files)}")
    print(f"[+] Baseline saved to: {BASELINE_FILE.resolve()}")


def load_baseline():
    """Load baseline.txt into a dictionary."""

    file_hash_dictionary = {}

    if not BASELINE_FILE.exists():
        print("[ERROR] baseline.txt does not exist.")
        print("Create a baseline first using option A.")
        return None

    with open(BASELINE_FILE, "r", encoding="utf-8") as baseline:

        for line in baseline:
            line = line.strip()

            if not line:
                continue

            try:
                filepath, file_hash = line.split("|", 1)
                file_hash_dictionary[filepath] = file_hash

            except ValueError:
                print(f"[WARNING] Invalid baseline entry: {line}")

    return file_hash_dictionary


def monitor_files():
    """Continuously monitor files against the saved baseline."""

    if not FILES_DIR.exists():
        print(f"[ERROR] Directory not found: {FILES_DIR.resolve()}")
        return

    file_hash_dictionary = load_baseline()

    if file_hash_dictionary is None:
        return

    print()
    print("Monitoring files...")
    print("Press Ctrl+C to stop.")
    print()

    # Used to prevent the same alert from printing every second.
    previous_alerts = set()

    try:

        while True:
            time.sleep(1)

            current_files = [
                file for file in FILES_DIR.iterdir()
                if file.is_file()
            ]

            current_paths = set()

            # Check for created or modified files
            for file in current_files:

                filepath = str(file.resolve())
                current_paths.add(filepath)

                current_hash = calculate_file_hash(filepath)

                if current_hash is None:
                    continue

                # New file
                if filepath not in file_hash_dictionary:

                    alert = ("created", filepath)

                    if alert not in previous_alerts:
                        print(f"[CREATED] {filepath}")
                        previous_alerts.add(alert)

                # Modified file
                elif file_hash_dictionary[filepath] != current_hash:

                    alert = ("changed", filepath)

                    if alert not in previous_alerts:
                        print(f"[CHANGED] {filepath}")
                        previous_alerts.add(alert)

                else:
                    # Remove old change alert if file returns
                    # to its original baseline hash.
                    previous_alerts.discard(("changed", filepath))

            # Check for deleted baseline files
            for filepath in file_hash_dictionary:

                if filepath not in current_paths:

                    alert = ("deleted", filepath)

                    if alert not in previous_alerts:
                        print(f"[DELETED] {filepath}")
                        previous_alerts.add(alert)

                else:
                    previous_alerts.discard(("deleted", filepath))

    except KeyboardInterrupt:
        print()
        print("Monitoring stopped.")


def main():

    print()
    print("What would you like to do?")
    print()
    print("    A) Collect new Baseline?")
    print("    B) Begin monitoring files with saved Baseline?")
    print()

    response = input("Please enter 'A' or 'B': ").strip().upper()

    print()

    if response == "A":
        collect_baseline()

    elif response == "B":
        monitor_files()

    else:
        print("Invalid selection. Please enter A or B.")


if __name__ == "__main__":
    main()
