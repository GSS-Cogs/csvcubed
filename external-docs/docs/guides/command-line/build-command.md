# build command

The build command is used to construct a new cube from its source file(s).  

The source files must include a tidy-data.csv and optionally a cube-config.json.  
Refer to the [qube-config quickstart](../../quick-start/qube-config.md) for an overview of how to construct these files.

**Syntax:**  
``csvcubed build [OPTIONS] TIDY_CSV_PATH``

**Arguments:**

| Argument      | Description                                                     |
|---------------|-----------------------------------------------------------------|
| TIDY_CSV_PATH | The file path to the cube data file, formatted as tidy data csv |

**Options:**

| Option                      | Description                                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------|
| --help / -h                 | Show the command help text.                                                                                     |
| --config / -c               | The file path for the cube configuration json file.                                                             |
| --out / -o                  | The output directory path where the build output is written. The default is './out'                             |
| --ignore-validation-errors  | Set this option to continue building the cube when errors are found.                                            |
| --validation-errors-to-file | Save validation errors to `validation-errors.json` in the output directory.                                     |
| --log-level                 | Set the desired logging level to one of 'crit', 'err', 'warn', 'info' and 'debug'.  <br/> The default is 'warn' |

## Configuration

### `--config` / `-c`

To create a cube using a [qube-config.json](../qube-config.md#configuration) file, use the `-c` option, e.g.

```bash
csvcubed build my-data-file.csv -c my-qube-config.json
```

## Logging

### `--validation-errors-to-file`

Setting this flag will result in any validation errors being written to the `validation-errors.json` file in the [output directory](#output-directory).  If no errors are encountered then the file is not written.

Common validation errors are documented in the [error guide](../errors/index.md)

### `--log-level`

Allows you to set the level of messages that are logged with `debug` being the most verbose and `err` the least. The default level is `warn`, at this level you will see messages with a level of `warn`, `err` and `crit`.

If errors occur then setting the log level to `info` or `debug` will yield additional messages and details to help diagnose the issue.

```bash
csvcubed build --log-level debug my-data.csv
```

### Log output

Processing and validation messages are written to both console and a log file during processing of the cube build command. The verbosity of the logging is governed by the `--log-level` option. The log messages can be used to help identify and resolve issues that are experienced when building your cube.

The log path is dependant upon the operating system in-use, the following are typical paths, these may also be influenced by your system configuration.

| Operating System | Typical Log Path                                                       |
|------------------|------------------------------------------------------------------------|
| **Windows**      | `C:\Users\[UserName]\AppData\Local\csvcubed\csvcubed-cli\Logs\out.log` |
| **Linux**        | `/home/[UserName]/.cache/csvcubed/csvcubed-cli/Logs/out.log`           |
| **MacOS**        | `/home/[UserName]/Library/Logs/csvcubed/csvcubed-cli/Logs/out.log`     |

### Log Retention

A new log file is created daily, with backups being saved for 7 days in the same location. Older logs are overwritten in a cyclic manner with the oldest being replaced first.

## Output Directory

### `--out` / `-o`

When the cube is built the default output path is `./out`. This may be changed by setting output option to an alternative path.

## Build Command Errors

When errors are encountered refer to the [errors guide](../errors/index.md) for help on understanding and resolving them.

## Examples

### Building a cube without configuration

Building a cube without providing a [qube-config.md](../qube-config.md#configuration) configuration file relies upon the [convention-first approach](../qube-config.md#convention-first-method).

To build a cube using only a csv data file. For guidance on the correct data structure refer to the [Shaping your data](../shape-data.md) guide, the 'standard approach' is recommended as a good starting point.

```bash
csvcubed build ./source/cube_data.csv
```

> `Build Complete`

Indicates that a cube was created and was written to the [output directory](#output-directory) (default: `./out`).

### Building a cube from data and configuration file

This is referred to as the [configuration-first approach](../qube-config.md#convention-first-method)  

The cube config json file must adhere to the structures defined in the [cube config schema](https://purl.org/csv-cubed/qube-config/v1.0).  

For help on constructing the config json refer to the [qube-config quickstart](../../quick-start/qube-config.md) or the more detailed [Configuration Guide]("../qube-config/#configuration")

To build a cube using both configuration and data files the command is shown below.  

```bash
csvcubed build --config=./source/cube_config.json ./source/cube_data.csv
```

> `Build Complete`

Indicates that a cube was created and written to the default [output directory](#output-directory) (default: `./out`).
