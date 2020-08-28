const express = require("express");
const app = express(),
      jwt = require("jsonwebtoken"),
      path = require("path"),
      yn = require("yn");

const {
  CANON_PORT,
  CANON_STATS_API,
  CANON_STATS_BASE_URL,
  CANON_STATS_LOGGING,
  CANON_STATS_PYTHON_ENGINE,
  CANON_STATS_TIMEOUT,
  OLAP_PROXY_SECRET
} = process.env;

const api = CANON_STATS_API;
const port = CANON_PORT || "8000";
const spawn = require("child_process").spawn;
const timeout = CANON_STATS_TIMEOUT * 1;

const BASE_URL = CANON_STATS_BASE_URL || "/api/stats";
const ENGINE = CANON_STATS_PYTHON_ENGINE || "python3";
const LOGGING = CANON_STATS_LOGGING || false;

const options = {
  "complexity": ["eci", "pci", "rca", "proximity", "relatedness", "opportunity_gain"],
  "network": ["network"],
  "regressions": ["ols", "logit", "arima", "probit", "prophet"],
  "summary": ["rolling"]
};

const getApiToken = (headers, user) => {
  const authLevel = {
    auth_level: user ? user.role : 0,
    sub: user ? user.id : "localhost",
    status: "valid"
  };

  return {
    apiToken: headers["x-tesseract-jwt-token"] || jwt.sign(authLevel, OLAP_PROXY_SECRET, { expiresIn: "30m" }),
    authLevel: authLevel.auth_level
  };
};

const serverApiToken = OLAP_PROXY_SECRET ? jwt.sign({
  auth_level: 10,
  sub: "server",
  status: "valid"
}, OLAP_PROXY_SECRET, {expiresIn: "30m"}) : "";

module.exports = function (app) {
  for (const d of Object.entries(options)) {
    for (const endpoint of d[1]) {
      app.get(`${BASE_URL}/${endpoint}`, (req, res) => {
        const {headers, query, user} = req;
        const {debug} = req.query;
        const {apiToken, authLevel} = OLAP_PROXY_SECRET ? getApiToken(headers, user) : {authLevel: 0};
        let timeoutId = null;
        let timedOut = false;

        const config = OLAP_PROXY_SECRET ? {
          "x-tesseract-jwt-token": apiToken
        } : {};

        const serverConfig = OLAP_PROXY_SECRET ? {
          "x-tesseract-jwt-token": serverApiToken
        } : {};

        const apiHeaders = JSON.stringify(config),
              apiServerHeaders = JSON.stringify(serverConfig),
              apiQuery = JSON.stringify(query);

        const pyPath = path.join(__dirname, `../${d[0]}_endpoints.py`);

        // Spawn a child process:
        //  Using {detached : true} as a 2nd argument
        //  allows killing of all of child's descendants.
        //  refs: http://azimi.me/2014/12/31/kill-child_process-node-js.html
        //        https://github.com/nodejs/node-v0.x-archive/issues/1811
        const py = spawn(ENGINE, 
          ["-W", "ignore", pyPath, apiQuery, endpoint, apiHeaders, authLevel, apiServerHeaders], 
          {detached: true});
        let respString = "";
        let traceback = "";

        // build response string based on results of python script
        py.stdout.on("data", data => respString += data.toString());
        
        // catch stderr errors
        py.stderr.on("data", data => traceback += data.toString());

        // return response
        py.stdout.on("end", () => {
          try {
            const dataResult = JSON.parse(respString);
            return res.json(dataResult);
          } 
          catch (error) {
            const output = {
              error: error.toString()
            };
            if (yn(debug) && yn(LOGGING)) output.traceback = traceback.split("\r\n");
            const errorCode = traceback.includes("This cube is not public") ? 401 : 404;
            return res.status(errorCode).json(output);
          }
        });

        py.on("close", () => {
          /* If we timed_out already, nothing to do. */
          if (timedOut) {
            return; // timeoutId has already been called
          }
          // Cancel the timeout timer (defined below).
          if (timeoutId) {
            clearTimeout(timeoutId);
          }
          // Log when process closes
          if (yn(debug) && yn(LOGGING)) console.log("process closed");
        });

        // ensure timeout is set and is an actual number
        if(!isNaN(timeout)) {
          timeoutId = setTimeout(() => {
            if (yn(LOGGING)) {
              console.log("---canon-stats timeout---");
              console.log(`endpoint: ${endpoint}`);
              console.log(`apiQuery: ${apiQuery}`);
            }
            try {
              process.kill(-py.pid, "SIGKILL");
            } catch (e) {
              py.kill();
              if (yn(LOGGING)) {
                console.log("Cannot kill canon-stats process!");
                console.log(e);
              }
            }
          }, timeout);
        }
        
        // log the error
        py.on("error", err => {
          if (yn(LOGGING)) {
            console.log("---canon-stats error---");
            console.log(`endpoint: ${endpoint}`);
            console.log(`apiQuery: ${apiQuery}`);
            console.log(err);
            console.log("---END canon-stats error---");
          }
        });

        // make sure to clear the timeout on process exit
        // if no timeout is set, do not clear
        py.on("exit", () => {
          if (timeoutId) {
            clearTimeout(timeoutId)
          }
        });

      });
    };
  };

  app.get(`${BASE_URL}/version`, (req, res) => {
    return res.json({endpoints: options, version: process.env.npm_package_version});
  });
};