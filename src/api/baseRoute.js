const express = require("express");
const app = express(),
      path = require("path");

const { getApiToken } = require("./apiHelpers");
const {
  CANON_PORT,
  CANON_STATS_API,
  CANON_STATS_BASE_URL,
  CANON_STATS_PYTHON_ENGINE,
  OLAP_PROXY_SECRET
} = process.env;

const api = `${CANON_STATS_API}/data`;
const port = CANON_PORT || "8000";
const spawn = require("child_process").spawn;

const BASE_URL = CANON_STATS_BASE_URL || "/api/stats";
const ENGINE = CANON_STATS_PYTHON_ENGINE || "python3";

const options = {
  "complexity": ["eci", "rca", "proximity", "relatedness", "opportunity_gain"],
  "network": ["network"],
  "regressions": ["ols", "logit", "arima", "probit", "prophet"]
};

module.exports = function (app) {
  Object.entries(options).forEach(d => {
    d[1].forEach(endpoint => {
      app.get(`${BASE_URL}/${endpoint}`, (req, res) => {
        const { headers, query, user } = req;
        const config = OLAP_PROXY_SECRET ? {
          "x-tesseract-jwt-token": getApiToken(headers, user)
        } : {};

        const apiHeaders = JSON.stringify(config),
              apiQuery = JSON.stringify(query);

        const pyPath = path.join(__dirname, `../${d[0]}_endpoints.py`);
        const py = spawn(ENGINE, ["-W", "ignore", pyPath, apiQuery, api, endpoint, apiHeaders]);
        let respString = "";
        let traceback = "";

        // build response string based on results of python script
        py.stdout.on("data", data => respString += data.toString());
        // catch errors
        py.stderr.on("data", data => {
          traceback += data.toString();
        });
        // return response
        py.stdout.on("end", () => {
          try {
            const dataResult = JSON.parse(respString);
            return res.json(dataResult);
          } catch (error) {
            const { debug } = req.query;
            const output = {
              error: error.toString()
            };
            if (debug && debug === "true") output.traceback = traceback.split("\r\n");
            return res.json(output);
          }
        });
      });
    });
  });
};