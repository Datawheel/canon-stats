const jwt = require("jsonwebtoken");
const {OLAP_PROXY_SECRET} = process.env;

const getApiToken = (headers, user) => 
  headers["x-tesseract-jwt-token"] || 
  jwt.sign(
    {
      auth_level: user ? user.role : 0,
      sub: user ? user.id : "localhost",
      status: "valid"
    },
    OLAP_PROXY_SECRET,
    {expiresIn: "30m"}
  );

module.exports = {
  getApiToken
}