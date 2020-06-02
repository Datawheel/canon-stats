const express = require("express");
const app = express(),
      jwt = require("jsonwebtoken");
const path = require("path");

const {
  CANON_PORT,
  CANON_STATS_API,
  CANON_STATS_BASE_URL,
  CANON_STATS_PYTHON_ENGINE,
  OLAP_PROXY_SECRET
} = process.env;

const api = CANON_STATS_API;
const port = CANON_PORT || "8000";
const spawn = require("child_process").spawn;

const BASE_URL = CANON_STATS_BASE_URL || "/api/stats";
const ENGINE = CANON_STATS_PYTHON_ENGINE || "python3";

const options = {
  "complexity": ["eci", "pci", "rca", "proximity", "relatedness", "opportunity_gain"],
  "correlation": ["correlation"],
  "network": ["network"],
  "regressions": ["ols", "logit", "arima", "probit", "prophet"]
};

const getApiToken = (headers, user) => {
  const authLevel = {
    auth_level: 10,
    sub: "server",
    status: "valid"
  };

  return {apiToken: headers["x-tesseract-jwt-token"] || 
  jwt.sign(
    authLevel,
    OLAP_PROXY_SECRET,
    {expiresIn: "30m"}
  ), authLevel: authLevel.auth_level};
}

const serverApiToken = OLAP_PROXY_SECRET ? jwt.sign(
  {
    auth_level: 10,
    sub: "server",
    status: "valid"
  },
  OLAP_PROXY_SECRET,
  {expiresIn: "30m"}
) : "";

Object.entries(options).forEach(d => {
  d[1].forEach(endpoint => {
    app.get(`${BASE_URL}/${endpoint}`, (req, res) => {
      const {headers, query, user} = req;
      const {apiToken, authLevel} = OLAP_PROXY_SECRET 
        ? getApiToken(headers, user) 
        : {authLevel: 0};

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
      const py = spawn(
        ENGINE,
        ["-W", "ignore", pyPath, apiQuery, api, endpoint, apiHeaders, authLevel, apiServerHeaders]
      );
      let respString = "";
      let traceback = "";
  
      // build response string based on results of python script
      py.stdout.on("data", data => {
        respString += data.toString()
      });
      // catch errors
      py.stderr.on("data", data => {
        traceback += data.toString();
      });
      // return response
      py.stdout.on("end", () => {
        try {
          const dataResult = JSON.parse(respString);
          return res.json(dataResult);
        }
        catch (error) {
          const {debug} = req.query;
          const output = {
            error: error.toString()
          }
          if (debug && debug === "true") output.traceback = traceback.split("\r\n");
          const errorCode = traceback.includes("This cube is not public") ? 401 : 404;
          return res.status(errorCode).json(output);
        }
      });
    });
  });
});


app.listen(port, () => {
  console.log(`Listening to requests on http://localhost:${port}`);
});
