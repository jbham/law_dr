import axios from "axios";
import { appUrl, cases } from "../config.json";
import { getJWT } from "./authService";

export async function getAllMentions(case_id) {
  var token = await getJWT();
  // const AuthStr = "Bearer ".concat(localStorage.getItem("token"));
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };
  const url = appUrl + cases.caseUrl + case_id + cases.caseMentions;
  const response = await axios.get(url, headers);
  console.log(response);
  return response;
}

export async function getAllFilesForCase(case_id) {
  var token = await getJWT();
  // const AuthStr = "Bearer ".concat(localStorage.getItem("token"));
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };
  const url = appUrl + cases.caseUrl + case_id + cases.caseFiles;
  const response = await axios.get(url, headers);
  console.log(response);
  return response;
}
