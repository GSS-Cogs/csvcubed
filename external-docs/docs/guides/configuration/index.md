# Configuring a cube

This document provides an overview of how csvcubed configures your cube. For an introduction to the topic take a look at the quick start guides on [designing a CSV](../../quick-start/designing-csv.md) and [linking data](../../quick-start/linking-data.md).

There are two ways to use csvcubed to generate a valid statistical cube:

* **The [configuration by convention](./convention.md) approach** allows you to create a cube with minimal configuration.
* **The [qube-config.json](./qube-config/index.md) approach** where you have the full power to configure your cube.

A mixture of the two approaches can be a good way to start building CSV-W cubes:

1. Start with the [configuration by convention](./convention.md) approach for all columns.
2. Define [catalogue metadata](./qube-config/metadata.md) to make it easier to discover your data.
3. Provide explicit column definitions on a column-by-column basis to start [linking data](../../quick-start/linking-data.md).
