const app = require("./app");
const port = 8081;

const server = app.listen(port, '0.0.0.0', function () {
  console.log("Web App Hosted at http://localhost:%s", port);
});
