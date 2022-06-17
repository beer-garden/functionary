import pathlib
from bg_cli.package import ParamTuple


def convertType(t: str) -> str:
    match t:
        case "string":
            return "str"
    return t


def getParams(params) -> list[str]:
    return [f"{x[0]}: {convertType(x[1])}" for x in params]


def generate(output_directory: str, name: str, params: ParamTuple, body: str) -> bool:
    print(f"Generating Python function named {name}")
    dir = pathlib.Path(output_directory) / name
    if not dir.exists():
        dir.mkdir()

    pyOutputFile = dir / f"{name}.py"
    with pyOutputFile.open("w"):
        fileText = f"def {name}({', '.join(getParams(params))}):\n"
        fileText += f"{body}\n" if body is not None else "    print('Hello Python!')\n"
        pyOutputFile.write_text(fileText)

    reqOutputFile = dir / "requirements.txt"
    with reqOutputFile.open("w"):
        pass

    return True
