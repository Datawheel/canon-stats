# Deployment
Last updated: 2020-08-04.

## Release a new version

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
npm run build
```
This command will build a new version.

### 3) Release on GitHub

NOTE: _version_ is the number of version used on [package.json](../package.json).
* Go to [https://github.com/Datawheel/canon-stats/releases/new](https://github.com/Datawheel/canon-stats/releases/new)
* **Tag version**: _version_
* **Release title**: @datawheel/canon-stats@_version_
* Click on **"Publish release"**.