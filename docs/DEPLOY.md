# Deployment
Last updated: 2020-08-04.

## Release a new version
Canon-stats has automated releasing a new version of the library. You just need to update on [package.json](../package.json) the version number, and run in your terminal `publish.sh`.

### 1) Update package.json's version
```
{
  "name": "@datawheel/canon-stats",
  "version": "0.6.2",
  ...
}
```
### 2) Build the version...

In the terminal, run:
```
. publish.sh
```
This command will build a new version.