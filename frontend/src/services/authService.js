import axios from "axios";
import {
  appUrl,
  loginUrl,
  // tokenVerify,
  // userListUrl,
  user,
} from "../config.json";
// import jwtDecode from "jwt-decode";
import { Auth } from "aws-amplify";

export async function login(email, password) {
  // const payload = { username: email, password: password };
  // console.log("this us payload");
  // console.log(payload);
  // const response = axios.post(appUrl + loginUrl.authenticate, payload);
  // console.log(response);
  // return response;

  var bodyFormData = new FormData();
  bodyFormData.set("username", email);
  bodyFormData.set("password", password);
  const response = await axios.post(
    appUrl + loginUrl.authenticate,
    bodyFormData
  );
  console.log(response);
  return response;
}

// export async function verifyToken(token) {
//   // const payload = { token: token };
//   // const response = axios.post(appUrl + tokenVerify, payload);
//   const newToken = jwtDecode(token);

//   return newToken;
// }

export async function getJWT() {
  // return localStorage.getItem("token");

  try {
    const user = Auth.currentSession();
    console.log("user");
    console.log(user);
    return user;
  } catch (ex) {
    console.log("getJWT");
    console.log(ex);
  }
}

export async function removeTokenFromLS() {
  const token = await getJWT();
  console.log("temoving token", token);
  for (var i = 0; i < localStorage.length; i++) {
    console.log(localStorage.getItem(localStorage.key(i)));
  }
  localStorage.removeItem("token");
}

export async function getCurrentUser() {}

export async function getUserList() {
  const AuthStr = "Bearer ".concat(localStorage.getItem("token"));
  const headers = { headers: { Authorization: AuthStr } };
  const response = await axios.get(appUrl + user.userListUrl, headers);

  console.log("response");
  console.log(response);
  return response;
}

export async function userCreate(data) {
  console.log("this is data from userCreate");
  console.log(data);

  const AuthStr = "Bearer ".concat(localStorage.getItem("token"));
  const headers = { headers: { Authorization: AuthStr } };

  const payload = data;
  const response = await axios.post(
    appUrl + user.userCreateUrl,
    payload,
    headers
  );
  console.log(response);
  return response;
}

export default {
  login,
  // verifyToken,
  getJWT,
  removeTokenFromLS,
  getCurrentUser,
  userCreate,
};
