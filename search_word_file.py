import argparse
import os
import shutil


def search_in_file(file_path, text):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return text in file.read().lower()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="ISO-8859-1") as file:
                return text in file.read().lower()
        except UnicodeDecodeError:
            print(f"Could not decode file: {file_path}")
            return False


def search_in_files(directory: str, extension: str, text: str, target_directory: str):
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith("." + extension):
                file_path = os.path.join(root, file)
                if search_in_file(file_path, text.lower()):
                    print(f"Text found in: {file_path}")
                    shutil.copy2(file_path, os.path.join(target_directory, file))


def main():
    parser = argparse.ArgumentParser(
        description="Text for a text in all files with a specific extension."
    )
    parser.add_argument("directory", type=str, help="Directory to search in")
    parser.add_argument("extension", type=str, help="File extension to look for")
    parser.add_argument("text", type=str, help="Text to search for")
    parser.add_argument("target_directory", type=str, help="Directory to copy files to")
    args = parser.parse_args()

    search_in_files(args.directory, args.extension, args.text, args.target_directory)


if __name__ == "__main__":
    main()
