# JavaScript

## Package Structure

A Functionary package is simply a directory that contains at least three files:

| File         | Description                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------- |
| functions.js | Contains all of the functions that will be available in your package                                    |
| package.yaml | Describes your package and the functions it contains. See [Defining Packages](../defining_packages.md). |
| package.json | Lists JavaScript dependencies needed for your functions                                                 |

## Organizing your Code

Any additional files or folders that you place in the directory will be included
in your package as well. You are by no means required to put all of your code
into the `functions.js` file. You are free to structure your code however you
like and can import other modules and packages. The only requirement is that the
function be exposed via the `functions.js`.

## Managing Dependencies

If your functions require external dependencies, they are not required to be
present within the package directory. You can list your dependencies in the
`package.json` file and they will be installed via npm during the package build
process. You can also pre-install them and include the node_modules directory in
you package, but this should generally be unnecessary.

## Function Parameter Types

The parameter types available when describing your functions in the
`package.yaml` are the same regardless of what language your functions are
written in. Because of this, the parameter types do not map directly to native
JavaScript types. The data types map as follows:

| Functionary Type | JavaScript Type            | Note                       |
| ---------------- | -------------------------- | -------------------------- |
| boolean          | boolean                    |                            |
| date             | string                     | ex: "2023-08-16"           |
| datetime         | string                     | ex: "2023-08-16T12:35:06Z" |
| file             | string                     | download url               |
| float            | number                     |                            |
| integer          | number                     |                            |
| json             | object \| string \| number |                            |
| string           | string                     |                            |
| text             | string                     |                            |

For more details on the various types, their usage, and how they appear on
tasking forms in the UI, see the
[Parameter Types](../developer_guide/parameter_types.md) section of the
Developer Guide.
