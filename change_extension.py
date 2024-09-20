import os
import argparse


def add_extension_to_files(directory: str, extension: str) -> None:
    for filename in os.listdir(directory):
        if not filename.endswith(extension):
            new_filename = f"{filename}.{extension}"
            os.rename(
                os.path.join(directory, filename), os.path.join(directory, new_filename)
            )
            print(f"Renamed {filename} to {new_filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Add extension to all files in a directory."
    )
    parser.add_argument("directory", type=str, help="Directory to process")
    parser.add_argument("extension", type=str, help="Extension to add")
    args = parser.parse_args()

    add_extension_to_files(args.directory, args.extension)


if __name__ == "__main__":
    main()
