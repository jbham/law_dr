import { createSlice } from "@reduxjs/toolkit";
import { apiCallBegan } from "./api";
import moment from "moment";
import { appUrl, cases } from "../config.json";
import { getJWT } from "../services/authService";

const slice = createSlice({
  name: "cases",
  initialState: {
    cases: [],
    loading: false,
    lastFetch: null,
    fields: [],
    info: false,
    errors: {},
    success: {},
    noCase: true,
    case_number: "",
  },
  reducers: {
    casesModalToggle: (cases, action) => {
      cases.info = action.payload.info;
    },
    casesCaseNumber: (cases, action) => {
      cases.case_number = action.payload.case_number;
    },
    casesRequested: (cases, action) => {
      cases.loading = true;
    },
    caseFetchFailed: (cases, action) => {
      cases.loading = false;
    },
    caseNumberReceived: (cases, action) => {
      cases.case_number = action.payload.case_number;
      cases.errors = action.payload.errors;
    },

    casesFetched: (cases, action) => {
      const data = action.payload;
      let fields = [];
      // lists.push(data);
      for (var i = 0; i < data.length; i++) {
        for (const [key, value] of Object.entries(data[i])) {
          //   console.log(key, value);
          if (!fields.includes(key)) {
            fields.push(key);
          }
        }
      }
      fields.push("Actions");
      cases.cases = data;
      cases.loading = false;
      cases.lastFetch = Date.now();
      cases.fields = fields;
    },
    caseCreateValidationError: (cases, action) => {
      cases.errors = action.payload.errors;
    },

    caseCreated: (cases, action) => {
      //   console.log("casecreateddddd", cases, action);
      cases.success.message = `Case '${action.payload.name}' successfully created`;
      cases.info = false;
      cases.case_number = "";
    },
  },
});

export const {
  casesRequested,
  caseFetchFailed,
  caseCreated,
  casesFetched,
  casesModalToggle,
  caseCreateValidationError,
  caseNumberReceived,
} = slice.actions;

export default slice.reducer;

// Action creators:

export const createCaseOnServer = () => async (dispatch, getState) => {
  const url = appUrl + cases.caseCreateUrl;
  const { case_number } = getState().cases;

  const token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { Authorization: AuthStr };

  return dispatch(
    apiCallBegan({
      url,
      method: "post",
      data: { name: case_number },
      headers,
      onSuccess: caseCreated.type,
    })
  );
};

export const loadCases = () => async (dispatch, getState) => {
  const url = appUrl + cases.caseUrl;
  const { lastFetch } = getState().cases;

  const diffInMinutes = moment().diff(moment(lastFetch), "minutes");
  if (diffInMinutes < 10) return;

  const token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { Authorization: AuthStr };

  return dispatch(
    apiCallBegan({
      url,
      onStart: casesRequested.type,
      onSuccess: casesFetched.type,
      onError: caseFetchFailed.type,
      headers,
    })
  );
};
