#!/usr/bin/env node

/**
 * Run `node release.js`
 */

const {Octokit} = require("@octokit/rest");
const shell = require("shelljs");
const execAsync = require("./execAsync");

const {GITHUB_TOKEN: token} = process.env;

module.exports = cliRelease();

/**
 * Executes the `release` subcommand for canon.
*/
async function cliRelease() {
  process.chdir("../");

  const packageManifest = shell.cat("./package.json").toString();
  const {name, version} = JSON.parse(packageManifest);

  let minor = version.split(".");
  const prerelease = parseFloat(minor[0]) === 0;
  minor = minor.slice(0, minor.length - 1).join(".");

  try {
    const stdout = await execAsync("git log -- `git describe --tags --abbrev=0`...HEAD");
    const body = stdout.length ? stdout : `${name}@${version}`;

    await execAsync("git add --all");
    await execAsync(`git commit -m \"compiles ${name}@${version}\"`);
    shell.echo("git commit");

    await execAsync(`git tag ${name}@${version}`);
    shell.echo("git tag");

    await execAsync("git push origin --follow-tags");
    shell.echo("git push");

    const octokit = new Octokit({
      auth: token
    });

    await octokit.repos.createRelease({
      owner: "datawheel",
      repo: "canon-stats",
      tag_name: `${name}@${version}`,
      name: `${name}@${version}`,
      body,
      prerelease
    }).catch(error => {
      shell.echo(`package: ${name}`);
      shell.echo(`version: ${version}`);
      shell.echo(`body: ${body}`);
      shell.echo(`prerelease: ${prerelease}`);
      shell.echo(error.message);
      shell.exit(1);
    });
    shell.echo("release pushed");

    shell.exit(0);
  }
  catch (e) {
    shell.echo(e);
    shell.exit(1);
  }
}