import os
from cli.package import ParamTuple


def convertType(t: str) -> str:
    match t:
        case "string":
            return "str"
    return t


def getParams(params) -> list[str]:
    return [f"{x[0]}: {convertType(x[1])}" for x in params]


def generate(output_directory: str, name: str, params: ParamTuple, body: str) -> bool:
    print(f"Generating Python function named {name}")
    dir = f"{output_directory}/{name}"
    if not os.path.isdir(dir):
        os.makedirs(dir)

    with open(f"{dir}/{name}.py", "w") as out:
        out.write(f"def {name}({', '.join(getParams(params))}):\n")
        out.write(f"{body}\n" if body is not None else "    print('Hello Python!')\n")

    with open(f"{dir}/requirements.txt", "w"):
        pass

    return True
