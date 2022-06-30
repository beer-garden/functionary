import pathlib
import shutil


def generate(output_directory: str, name: str) -> bool:
    print(f"Generating Javascript function named {name}")
    dir = pathlib.Path(output_directory) / name
    if not dir.exists():
        dir.mkdir()

    basepath = pathlib.Path(__file__).parent.resolve() / "templates" / "javascript"

    shutil.copy2(basepath / "functions.js", dir)
    shutil.copy2(basepath / "package.json", dir)
    shutil.copy2(basepath / "Dockerfile", dir)

    return True
