const baseUrl = pm.environment.get("base_url") || "http://localhost:8000";
const username = pm.environment.get("username");
const password = pm.environment.get("password");

pm.sendRequest(
  {
    url: `${baseUrl}/Login`,
    method: "POST",
    header: { "Content-Type": "application/json" },
    body: {
      mode: "raw",
      raw: JSON.stringify({
        Username: username,
        Password: password
      })
    }
  },
  function (err, res) {
    if (err) {
      console.log("Login error:", err);
      return;
    }
    const data = res.json();
    pm.environment.set("jwt_token", data.access_token);
  }
);
