import { createSlice } from "@reduxjs/toolkit";
import { apiCallBegan } from "./api";
import moment from "moment";
import { appUrl, cases } from "../config.json";
import { getJWT } from "../services/authService";

const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
};

const groupBy = (list) => {
  var parentId = [];
  var parentFiles = [];

  // prepare parents
  list.forEach((item) => {
    if (!parentId.includes(item.id)) {
      parentId.push(item.id);
      item["children"] = [];
      item["total_split_files"] = 0;
      parentFiles.push(item);
    }
  });

  // append children

  for (var j = 0; j < parentFiles.length; j++) {
    for (var i = 0; i < list.length; i++) {
      if (list[i]["id"] === parentFiles[j]["id"]) {
        for (const [key, value] of Object.entries(list[i])) {
          if (
            [
              "terms_extraction_status",
              "file_process_status",
              "file_split_status",
            ].includes(key)
          ) {
            if (value === 2) {
              list[i][key] = "Successful";
            } else if (value === 1) {
              list[i][key] = "Processing";
            } else if (value === 0) {
              list[i][key] = "Initiated";
            } else if (value === 3) {
              list[i][key] = "Failed";
            }
          }

          if (key === "new_file_name") {
            var fd = value.split("/");
            list[i][key] = fd[fd.length - 1];
            list[i]["original_file_name"] = value;
          }

          if (key === "size") {
            if (Number.isInteger(list[i][key])) {
              list[i][key] = formatBytes(value);
            }
          }
        }

        parentFiles[j]["children"].push({
          parentId: parentFiles[j]["id"],
          file_process_status: list[i]["file_process_status"],
          file_split_status: list[i]["file_split_status"],
          terms_extraction_status: list[i]["terms_extraction_status"],
          new_file_name: list[i]["new_file_name"],
          total_split_pages: list[i]["total_split_pages"],
          split_file_id: list[i]["split_file_id"],
          original_file_name: list[i]["original_file_name"],
        });
        parentFiles[j]["total_split_files"] = parentFiles[j]["children"].length;
        delete parentFiles[j]["file_process_status"];
        delete parentFiles[j]["file_split_status"];
        delete parentFiles[j]["terms_extraction_status"];
        delete parentFiles[j]["new_file_name"];
        delete parentFiles[j]["total_split_pages"];
        delete parentFiles[j]["original_file_name"];
      }
    }
  }
  return parentFiles;
};

const slice = createSlice({
  name: "case",
  initialState: {
    caseDetails: {},
    activeTab: "files",
    caseParentFiles: [],
    fields: [],
    loading: false,
    lastFetch: null,
  },
  reducers: {
    caseBeingViewed: (currentCase, action) => {
      currentCase.caseDetails = action.payload;
    },
    // used when a user copies and pastes link and we dont have caseDetails in store
    caseDetailsRefreshed: (currentCase, action) => {
      currentCase.caseDetails = action.payload;
    },
    setActiveTab: (currentCase, action) => {
      currentCase.activeTab = action.payload;
      //   localStorage.setItem("activeTab", action.payload);
    },
    caseFilesRequested: (currentCase, action) => {
      currentCase.loading = true;
    },
    caseFilesFetched: (currentCase, action) => {
      const data = action.payload;
      let fields = [];
      let childFields = [
        "file_process_status",
        "file_split_status",
        "terms_extraction_status",
        "new_file_name",
        "children",
        "total_split_pages",
        "original_file_name",
      ];

      const parentFiles = groupBy(data);

      for (var i = 0; i < parentFiles.length; i++) {
        for (const [key] of Object.entries(data[i])) {
          if (!fields.includes(key) && !childFields.includes(key)) {
            fields.push(key);
          }
        }
      }

      fields.push("Actions");

      currentCase.caseParentFiles = parentFiles;
      currentCase.fields = fields;
      currentCase.loading = false;
      currentCase.lastFetch = Date.now();
    },
    caseFilesFetchFailed: (currentCase, action) => {
      currentCase.loading = false;
    },
  },
});

export const {
  caseBeingViewed,
  caseDetailsRefreshed,
  setActiveTab,
  caseFilesRequested,
  caseFilesFetched,
  caseFilesFetchFailed,
} = slice.actions;
export default slice.reducer;

export const loadCaseFiles = (id) => async (dispatch, getState) => {
  if (id) {
    const url = appUrl + cases.caseUrl + id + cases.caseFiles;
    const { lastFetch } = getState().currentCase;

    const diffInMinutes = moment().diff(moment(lastFetch), "minutes");
    if (diffInMinutes < 10) return;

    const token = await getJWT();
    const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
    const headers = { Authorization: AuthStr };

    return dispatch(
      apiCallBegan({
        url,
        onStart: caseFilesRequested.type,
        onSuccess: caseFilesFetched.type,
        onError: caseFilesFetchFailed.type,
        headers,
      })
    );
  }
};

export const loadACase = (id) => async (dispatch, getState) => {
  const url = appUrl + cases.caseUrl + id;

  const token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { Authorization: AuthStr };

  return dispatch(
    apiCallBegan({
      url,
      onSuccess: caseDetailsRefreshed.type,
      headers,
    })
  );
};
