import axios from "axios";
import { appUrl, file, cases } from "../config.json";
import { getJWT } from "./authService";

export async function getFilePolicy(fileName, newCaseNumber) {
  const payload = { filename: fileName, newCase: newCaseNumber };
  // const AuthStr = "Bearer ".concat(localStorage.getItem("token"));

  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);

  const headers = { headers: { Authorization: AuthStr } };
  console.log(headers, payload);
  const response = axios.post(appUrl + file.filePolicyUrl, payload, headers);
  console.log(response);
  return response;
}

export async function updateS3UploadedFileDetails(upload_res) {
  const payload = upload_res;
  // const AuthStr = "Bearer ".concat(localStorage.getItem("token"));
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };
  console.log(headers, payload);
  const response = await axios.put(
    appUrl + file.filePolicyUrl,
    payload,
    headers
  );
  console.log("updateS3UploadedFileDetails", response);
  return response;
}

export async function getAllCases() {
  var token = await getJWT();
  // const AuthStr = "Bearer ".concat(localStorage.getItem("token"));
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };
  const response = await axios.get(appUrl + cases.caseUrl, headers);
  console.log(response);
  return response;
}

export async function createBackendCase(casenumber) {
  const payload = { name: casenumber };
  // const AuthStr = "Bearer ".concat(localStorage.getItem("token"));
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };
  const response = await axios.post(
    appUrl + cases.caseCreateUrl,
    payload,
    headers
  );
  console.log("createBackendCase");
  console.log(response);
  return response;
}

export async function downloadFile(
  m_id: string,
  caseId: integer,
  s3File: string
) {
  let payload = {};
  console.log("downloadFile testing", payload, m_id, caseId, s3File);
  // if (m_id) {
  //   payload = { m_id: m_id, case_id: caseId, fd: s3File };
  // }

  // if (s3File) {
  //   payload = { case_id: caseId, fd: s3File };
  // }

  payload = { m_id: m_id, case_id: caseId, fd: s3File };

  console.log("downloadFile testing", payload, m_id, caseId, s3File);

  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  let config = {
    headers: { Authorization: AuthStr },
    params: payload,
  };

  const url = appUrl + file.dnFile;
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}

export async function deleteFile(file_detail) {
  const payload = file_detail;

  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };
  const url = `${appUrl}${file.deleteFile}`;
  console.log(url, file_detail);
  const response = await axios.post(
    // ${`appUrl + file.deleteFile + file_detail["id"]`},
    url,
    payload,
    headers
  );
  return response;
}
