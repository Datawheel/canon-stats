const express = require("express");
const path = require("path");

const api = process.env.CANON_STATS_API;
const app = express();
const port = process.env.CANON_PORT || "3300";
const spawn = require("child_process").spawn;

const BASE_URL = process.env.CANON_STATS_BASE_URL || "/api/stats";

app.get(`${BASE_URL}/eci`, (req, res) => {
  const pyFilePath = path.join(__dirname, "../complexity_endpoints.py");
  const py = spawn(
    "python3",
    ["-W", "ignore", pyFilePath, JSON.stringify(req.query), api, "eci"]
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


app.get(`${BASE_URL}/rca`, (req, res) => {
  const pyFilePath = path.join(__dirname, "../complexity_endpoints.py");
  const py = spawn(
    "python3",
    ["-W", "ignore", pyFilePath, JSON.stringify(req.query), api, "rca"]
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
      console.error(`\nrespString:\n${respString}`);
      return res.json({error: e});
    }
  });
});


app.get(`${BASE_URL}/relatedness`, (req, res) => {
  const pyFilePath = path.join(__dirname, "../complexity_endpoints.py");
  const py = spawn(
    "python3",
    ["-W", "ignore", pyFilePath, JSON.stringify(req.query), api, "relatedness"]
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
      console.error(`\nrespString:\n${respString}`);
      return res.json({error: "Hello"});
    }
  });
});

app.listen(port, () => {
  console.log(`Listening to requests on http://localhost:${port}`);
});