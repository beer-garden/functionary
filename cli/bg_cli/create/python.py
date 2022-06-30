import pathlib
import shutil


def generate(output_directory: str, name: str) -> bool:
    print(f"Generating Python function named {name}")
    dir = pathlib.Path(output_directory) / name
    if not dir.exists():
        dir.mkdir()

    basepath = pathlib.Path(__file__).parent.resolve() / "templates" / "python"

    shutil.copy2(basepath / "functions.py", dir)
    shutil.copy2(basepath / "requirements.txt", dir)
    shutil.copy2(basepath / "Dockerfile", dir)

    return True
