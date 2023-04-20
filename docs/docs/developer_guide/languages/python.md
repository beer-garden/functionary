# Python

## Package Structure

A Functionary package is simply a directory that contains at least three files:

| File             | Description                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| functions.py     | Contains all of the functions that will be available in your package                                    |
| package.yaml     | Describes your package and the functions it contains. See [Defining Packages](../defining_packages.md). |
| requirements.txt | Lists Python dependencies needed for your functions                                                     |

## Organizing your Code

Any additional files or folders that you place in the directory will be included
in your package as well. You are by no means required to put all of your code
into the `functions.py` file. You are free to structure your code however you
like and can import other modules and packages. The only requirement is that the
function be exposed via the `functions.py`.

## Managing Dependencies

If your functions require external dependencies, they are not required to be
present within the package directory. You can list your dependencies in the
`requirements.txt` file and they will be installed via pip during the package
build process.

## Function Parameter Types

The parameter types available when describing your functions in the
`package.yaml` are the same regardless of what language your functions are
written in. Because of this, the parameter types do not map directly to native
Python types. The data types map as follows:

| Functionary Type | Python Type                         | Note                       |
| ---------------- | ----------------------------------- | -------------------------- |
| boolean          | bool                                |                            |
| date             | str                                 | ex: "2023-08-16"           |
| datetime         | str                                 | ex: "2023-08-16T12:35:06Z" |
| file             | str                                 | download url               |
| float            | float                               |                            |
| integer          | int                                 |                            |
| json             | dict \| list \| str \| int \| float |                            |
| string           | str                                 |                            |
| text             | str                                 |                            |

For more details on the various types, their usage, and how they appear on
tasking forms in the UI, see the
[Parameter Types](../developer_guide/parameter_types.md) section of the
Developer Guide.
