const header = {
  alg: "HS256",
  typ: "JWT"
};

const payload = {
  username: pm.environment.get("username"),
  password: pm.environment.get("password"),
  exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour expiry
};

const secret = pm.environment.get("jwt_secret");

// Postman has CryptoJS built in
function base64url(source) {
  return CryptoJS.enc.Base64.stringify(source)
    .replace(/=+$/, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
}

const encodedHeader = base64url(CryptoJS.enc.Utf8.parse(JSON.stringify(header)));
const encodedPayload = base64url(CryptoJS.enc.Utf8.parse(JSON.stringify(payload)));

const signature = CryptoJS.HmacSHA256(
  encodedHeader + "." + encodedPayload,
  secret
);

const encodedSignature = base64url(signature);

const token = `${encodedHeader}.${encodedPayload}.${encodedSignature}`;

pm.environment.set("jwt_token", token);
