const path = require("path");

const api = `${process.env.CANON_STATS_API}/data`;
const spawn = require("child_process").spawn;

const BASE_URL = process.env.CANON_STATS_BASE_URL || "/api/stats";
const ENGINE = process.env.CANON_STATS_PYTHON_ENGINE || "python3";

module.exports = function (app) {
  ["eci", "rca", "proximity", "relatedness", "opportunity_gain"].forEach(endpoint => {
    app.get(`${BASE_URL}/${endpoint}`, (req, res) => {
      const pyFilePath = path.join(__dirname, "../complexity_endpoints.py");
      const py = spawn(ENGINE, ["-W", "ignore", pyFilePath, JSON.stringify(req.query), api, endpoint]);
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
        } catch (e) {
          return res.json({ error: e.toString() });
        }
      });
    });
  });

  app.get(`${BASE_URL}/network`, (req, res) => {
    const pyFilePath = path.join(__dirname, "../network_endpoints.py");
    const py = spawn(ENGINE, ["-W", "ignore", pyFilePath, JSON.stringify(req.query), api]);
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
      } catch (e) {
        return res.json({ error: e.toString() });
      }
    });
  });
};