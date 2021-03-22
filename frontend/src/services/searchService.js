import axios from "axios";
import { appUrl, search } from "../config.json";
import { getJWT } from "./authService";

export async function getSearchFacet(caseId) {
  var payload = { case_id: caseId };
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };

  let config = {
    headers: { Authorization: AuthStr },
    params: payload
  };
  const url = appUrl + search.searchParent + search.searchUrl;
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}

export async function getSpecificCatefory(fileId, start, limit, cat) {
  var payload = { file_id: fileId, start: start, limit: limit, category: cat };
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };

  let config = {
    headers: { Authorization: AuthStr },
    params: payload
  };

  const url = appUrl + search.searchParent + search.searchCategory;
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}

export async function getAllConfirmedVisitDates(fileId) {
  var payload = { file_id: fileId };
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  let config = {
    headers: { Authorization: AuthStr },
    params: payload
  };

  const url = appUrl + search.searchParent + search.visitDates;
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}

// most likely going to be deprecated
export async function getTextByVisitDates(fileId, cvd, txt, start, limit) {
  var payload = {
    file_id: fileId,
    cvd: cvd,
    txt: txt,
    start: start,
    limit,
    limit
  };
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  let config = {
    headers: { Authorization: AuthStr },
    params: payload
  };

  const url = appUrl + search.searchParent + search.vdt;
  console.log(url, config);
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}

export async function getAllCnfmdVisitDatesWithFileIds(caseId) {
  var payload = { case_id: caseId };
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);

  let config = {
    headers: { Authorization: AuthStr },
    params: payload
  };

  const url = appUrl + search.searchParent + search.vddoc;
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}

export async function getPresetCatFilters(caseId, cat) {
  var payload = { case_id: caseId, category: cat };
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  let config = {
    headers: { Authorization: AuthStr },
    params: payload
  };
  const url = appUrl + search.searchParent + search.presetCatFilters;
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}

export async function getShowMePDF(caseId) {
  var payload = { case_id: caseId };
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };

  let config = {
    headers: { Authorization: AuthStr },
    params: payload
  };
  const url = appUrl + search.searchParent + search.listofpdfs;
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}

export async function getChildFiles(caseId, fileId) {
  var payload = { case_id: caseId, file_id: fileId };
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };

  let config = {
    headers: { Authorization: AuthStr },
    params: payload
  };
  const url = appUrl + search.searchParent + search.childfiles;
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}

export async function getpdfCords(caseId, m_id) {
  var payload = { case_id: caseId, m_id: m_id };
  var token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { headers: { Authorization: AuthStr } };

  let config = {
    headers: { Authorization: AuthStr },
    params: payload
  };
  const url = appUrl + search.searchParent + search.pdfcords;
  const response = await axios.get(url, config);
  console.log(response);
  return response;
}
