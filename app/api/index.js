const express = require("express");
const app = express();
const path = require("path");

const api = `${process.env.CANON_STATS_API}/data`;
const port = process.env.CANON_PORT || "8000";
const spawn = require("child_process").spawn;

const BASE_URL = process.env.CANON_STATS_BASE_URL || "/api/stats";
const ENGINE = process.env.CANON_STATS_PYTHON_ENGINE || "python3";


["eci", "rca", "proximity", "relatedness", "opportunity_gain"].forEach(endpoint => {
  app.get(`${BASE_URL}/${endpoint}`, (req, res) => {
    const pyFilePath = path.join(__dirname, "../complexity_endpoints.py");
    const py = spawn(
      ENGINE,
      ["-W", "ignore", pyFilePath, JSON.stringify(req.query), api, endpoint]
    );
    let respString = "";
  
    // build response string based on results of python script
    py.stdout.on("data", data => respString += data.toString());
    // catch errors
    py.stderr.on("data", data => console.error(`\nstderr:\n${data}`));
    // return response
    py.stdout.on("end", () => {
      try {
        const dataResult = JSON.parse(respString);
        return res.json(dataResult);
      }
      catch (e) {
        console.error(`\nrespString:\n${e}`);
        return res.json({error: e});
      }
    });
  });
});


app.get(`${BASE_URL}/network`, (req, res) => {
  const pyFilePath = path.join(__dirname, "../network_endpoints.py");
  const py = spawn(
    ENGINE,
    ["-W", "ignore", pyFilePath, JSON.stringify(req.query), api]
  );
  let respString = "";

  // build response string based on results of python script
  py.stdout.on("data", data => respString += data.toString());
  // catch errors
  py.stderr.on("data", data => console.error(`\nstderr:\n${data}`));
  // return response
  py.stdout.on("end", () => {
    try {
      const dataResult = JSON.parse(respString);
      return res.json(dataResult);
    }
    catch (e) {
      console.error(`\nrespString:\n${e}`);
      return res.json({error: e});
    }
  });
});

["ols", "logit", "arima", "probit", "prophet"].forEach(d => {
  app.get(`${BASE_URL}/${d}`, (req, res) => {
    res.header("Access-Control-Allow-Origin", "*"); // update to match the domain you will make the request from
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
 
    const pyFilePath = path.join(__dirname, "../regressions_endpoints.py");
    const py = spawn(
      ENGINE,
      ["-W", "ignore", pyFilePath, JSON.stringify(req.query), api, d]
    );
    let respString = "";
  
    // build response string based on results of python script
    py.stdout.on("data", data => respString += data.toString());
    // catch errors
    py.stderr.on("data", data => console.error(`\nstderr:\n${data}`));
    // return response
    py.stdout.on("end", () => {
      try {
        const dataResult = JSON.parse(respString);
        return res.json(dataResult);
      }
      catch (e) {
        console.error(`\nrespString:\n${e}`);
        return res.json({error: e});
      }
    });
  });
})




app.listen(port, () => {
  console.log(`Listening to requests on http://localhost:${port}`);
});
