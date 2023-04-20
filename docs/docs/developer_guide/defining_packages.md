# Defining Packages

In Functionary, all functions must be defined as part of a package. A package is
simply a logical grouping of one or more functions. How you organize your
functions is up to you, but typically it makes sense to group related functions
together into a package.

In addition to the actual code that makes up the functions in a package, it is
also necessary to describe the package and its functions so Functionary is able
to render forms in the UI and validate parameters when tasking. This package
description is done via a YAML file named `package.yaml`.

A full example of this file can be seen in the
[Getting Started](../getting_started/create_a_package.md#describe-your-package).
The schema for the package.yaml is described below.

!!! note "Schema File"

    A schema file for the package.yaml can be downloaded
    [here](/static/utils/package_yaml_schema.json). Configuring your IDE to use
    this schema to validate your pacakge.yaml can help ensure that your package
    definition is correctly formatted.

## version

`required`

The schema version of the package.yaml. Currently the only valid option is
`1.0`.

```yaml
version: 1.0
```

## package

`required`

This consists of a few properties that describe the package itself, as well as
an array of `functions` to describe the individual functions.

```yaml
package:
  name: str
  display_name: str
  summary: str
  language: str
```

### name

`required`

Friendly identifier for your package. This must be unique for any environment in
which the package gets published and cannot be changed once the package is
published.

### display_name

`optional`

An alternative name to display in the UI for your package. This value is not
required to be unique in an environment, it may also contain spaces. Defaults to
the value of `name` if left unset.

### summary

`optional`

A short summary of the package's purpose. This is what will be displayed in
package list view in the UI.

### description

`optional`

A more detailed description of the package. This will be displayed on the detail
page for the package.

## language

`required`

The language that your function code is written in. This value is mainly used to
determine how to properly containerize and execute your function code. The exact
list of valid values could vary from deployment to deployment, but the default
options include:

- python
- javascript

```yaml
language: ["python"|"javascript"]
```

## functions

`required`

This is an array of entries that include details about the functions within your
package.

```yaml
functions:
  - name: str
    display_name: str
    summary: str
    description: str
    return_type: ["boolean"|"date"|"datetime"|"file"|"float"|"integer"|"json"|"string"|"text"]
    parameters:
      - name: str
        description: str
        type: ["boolean"|"date"|"datetime"|"file"|"float"|"integer"|"json"|"string"|"text"]
        required: bool
```

### name

`required`

The name of your function in the code itself. It must match the name of the
function exactly.

### display_name

`optional`

An alternative name to display in the UI for your function. This value is not
required to follow the function naming conventions of your language (it may
contain spaces, for example).

### summary

`optional`

A short summary of the function's purpose. This is what will be displayed in
function list view in the UI.

### description

`optional`

A more detailed description of the function. This will be displayed on the
execution page for the function.

### return_type

`optional`

Declares what type of data is expected to return from the function. This is not
strictly enforced, but is instead for informational purposes for those executing
the function. Valid values are:

- boolean
- date
- datetime
- file
- float
- integer
- json
- string
- text

### parameters

`required`

An array of the parameters that the function takes. If the function takes no
parameters, this should be set to an empty an array (`[]`) rather than being
omitted.

#### name

`required`

The name of the parameter. This should match the parameter name in the function
signature exactly.

#### description

`optional`

A brief description of the parameter. This will be displayed near the input
field on the tasking form.

#### type

`required`

The data type of the parameter. This is not the native data type of the function
that the language is written in, but rather one of the following Functionary
data types:

- boolean
- date
- datetime
- file
- float
- integer
- json
- string
- text

For more details regarding parameter types, their usage, and how each type is
represented when executing functions, see the
[Parameter Types](../developer_guide/parameter_types.md) section of the
Developer Guide.

#### required

`optional`

Denotes if the parameter is required. Defaults to `false`.

#### default

`optional`

Default value that will be used to pre-populate the tasking form. The value set
here is used _only_ for the purposes of the form in the UI. It will not be
inserted as a default when no value is supplied for the parameter. If you want a
default value to be used when none is supplied, you must write your actual
function to behave this way.
