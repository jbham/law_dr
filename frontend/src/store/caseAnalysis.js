import axios from "axios";
import { createSlice } from "@reduxjs/toolkit";
import { createSelector } from "reselect";
import { apiCallBegan } from "./api";
import moment from "moment";
import { appUrl, cases, search, file } from "../config.json";
import { getJWT } from "../services/authService";
import { loadState } from "./localStorage";

const initialTimelineState = {
  value: 0,
  previous: 0,
  showConfigurator: false,

  // timelineConfig
  minEventPadding: 20,
  maxEventPadding: 120,
  linePadding: 100,
  labelWidth: 100,
  fillingMotionStiffness: 150,
  fillingMotionDamping: 25,
  slidingMotionStiffness: 150,
  slidingMotionDamping: 25,
  stylesBackground: "#f8f8f8",
  stylesForeground: "#7b9d6f",
  stylesOutline: "#dfdfdf",
  isTouchEnabled: true,
  isKeyboardEnabled: true,
  isOpenEnding: true,
  isOpenBeginning: true,
};

const initialState = {
  lastFetchedData: [],
  lastSearchedTerm: "",
  visitDates: [],
  showMentions: {},
  dataForSelectedVisitDate: {},
  showRelations: {}, // {id of the line item : true/false}
  loading: false,
  timelineBar: initialTimelineState,
  everythingPDF: {
    pdfLoading: false,
    pdfDoc: null,
    highlights: [],
    policyData: {},
  },
};

const persistedState = loadState();

const stateToAssign =
  persistedState === undefined ? initialState : persistedState;

const slice = createSlice({
  name: "caseAnalysis",
  initialState: stateToAssign,
  reducers: {
    setTimelineBar: (timelineBar, action) => {
      console.log(timelineBar);
      timelineBar.timelineBar = action.payload;
      console.log(timelineBar);
    },
    visitDatesRequested: (visitDates, action) => {
      visitDates.loading = true;
    },
    visitDatesFetched: (visitDates, action) => {
      let visitDatesForTimeline = [];
      const data = action.payload;

      var mentionSeen = [];
      var mentionsAllowed = [
        "Medication",
        "Procedure",
        "Anatomical Site",
        "Sign or Symptoms",
        "Disease or Disorder",
      ];
      var holdingObject = {};

      var showRelationsLocal = {};

      for (var i = 0; i < data.length; i++) {
        if ("string_to_date" in data[i]) {
          visitDatesForTimeline.push(data[i]["string_to_date"]);
        }

        // separate out mentions by type
        if (data[i]["all_terms"]) {
          for (var j = 0; j < data[i]["all_terms"].length; j++) {
            if (
              mentionsAllowed.includes(
                data[i]["all_terms"][j]["annotation_type"]
              )
            ) {
              showRelationsLocal[data[i]["all_terms"][j]["id"]] = false;
              if (
                !mentionSeen.includes(
                  data[i]["all_terms"][j]["annotation_type"]
                )
              ) {
                holdingObject[data[i]["all_terms"][j]["annotation_type"]] = [
                  data[i]["all_terms"][j],
                ];
                mentionSeen.push(data[i]["all_terms"][j]["annotation_type"]);
              } else {
                holdingObject[data[i]["all_terms"][j]["annotation_type"]].push(
                  data[i]["all_terms"][j]
                );
              }
            }
          }

          var orderedHoldingObject = {};
          Object.keys(holdingObject)
            .sort()
            .forEach(function (key) {
              orderedHoldingObject[key] = holdingObject[key];
            });
          visitDates.dataForSelectedVisitDate = orderedHoldingObject;
          for (var v in mentionSeen) {
            visitDates.showMentions[mentionSeen[v]] = false;
          }
          visitDates.showRelations = showRelationsLocal;
          holdingObject = {};
        }
      }

      visitDates.visitDates = visitDatesForTimeline;
      visitDates.loading = false;
      visitDates.lastFetchedData = data;
    },
    visitDatesFetchFailed: (visitDates, action) => {
      // visitDates.loading = false;
    },
    hideShowMentions: (visitDates, action) => {
      visitDates.showMentions = action.payload;
    },
    handleShowRelations: (visitDates, action) => {
      visitDates.showRelations = action.payload;
    },
    setLastSearchedTerm: (visitDates, action) => {
      visitDates.lastSearchedTerm = action.payload;
      visitDates.timelineBar = initialTimelineState;
    },
    // pdf related actions
    pdfRequested: (visitDates, action) => {
      visitDates.everythingPDF.pdfLoading = true;
    },
    pdfPolicyFetched: (visitDates, action) => {
      visitDates.everythingPDF.policyData = action.payload;
    },
    pdfFetched: (visitDates, action) => {
      visitDates.everythingPDF.pdfDoc = action.payload;
      visitDates.everythingPDF.pdfLoading = true;
    },
    pdfFailed: (visitDates, action) => {
      // TODO:
    },
  },
});

export const {
  setLastSearchedTerm,
  setTimelineBar,
  visitDatesRequested,
  visitDatesFetched,
  visitDatesFetchFailed,
  hideShowMentions,
  handleShowRelations,
  pdfPolicyFetched,
  pdfRequested,
  pdfFetched,
  pdfFailed,
} = slice.actions;
export default slice.reducer;

export const loadAllVisitDates = (
  newtimelineBar,
  searchTerm,
  file_id,
  file_state_id
) => async (dispatch, getState) => {
  // dispatch to update timeline

  await dispatch(visitDatesRequested());
  if (newtimelineBar) await dispatch(setTimelineBar(newtimelineBar));

  const { id } = getState().currentCase.caseDetails;
  const url = appUrl + search.searchParent + "all/"; //search.visitdates;

  const token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { Authorization: AuthStr };

  const params = {
    case_id: id,
    searchTerm: searchTerm,
    file_id: file_id,
    file_state_id: file_state_id,
  };

  await dispatch(
    apiCallBegan({
      url,
      onStart: visitDatesRequested.type,
      onSuccess: visitDatesFetched.type,
      onError: visitDatesFetchFailed.type,
      headers,
      params,
    })
  );

  if (!file_id && !file_state_id) {
    const { lastFetchedData } = getState().caseAnalysis;
    file_id = lastFetchedData[0]["file_id"];
    file_state_id = lastFetchedData[0]["file_state_id"];
  }

  return dispatch(loadPDF(file_id, file_state_id));
};

export const loadPDF = (file_id, file_state_id) => async (
  dispatch,
  getState
) => {
  const { id } = getState().currentCase.caseDetails;
  const url = appUrl + file.dnFile;

  const token = await getJWT();
  const AuthStr = "Bearer ".concat(token.accessToken.jwtToken);
  const headers = { Authorization: AuthStr };

  const params = {
    case_id: id,
    file_id,
    file_state_id,
  };

  let config = { headers, params };

  const { data } = await axios.get(url, config);
  // data = data["data"];

  dispatch(pdfPolicyFetched(data));
};

export const getRelationsByID = createSelector(
  (state) => {
    console.log(state);
    return state.caseAnalysis.dataForSelectedVisitDate;
  },
  (_, idList) => idList,
  (dataForSelectedVisitDate, idList) => {
    console.log("from getrelationiud", dataForSelectedVisitDate, idList);
    let listToReturn = [];

    Object.keys(dataForSelectedVisitDate).map((keyName, i) => {
      for (var x = 0; x < idList.length; x++) {
        for (var y = 0; y < dataForSelectedVisitDate[keyName].length; y++) {
          if (idList[x] === dataForSelectedVisitDate[keyName][y]["id"]) {
            listToReturn.push(dataForSelectedVisitDate[keyName][y]);
            // break;
          }
        }
      }
    });

    return listToReturn;
  }
);
