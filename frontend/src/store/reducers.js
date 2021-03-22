import { combineReducers } from "redux";
import casesReducers from "./cases";
import sidebarReducer from "./sidebar";
import caseReducer from "./case";
import visitDatesReducer from "./caseAnalysis";

export default combineReducers({
  cases: casesReducers,
  sidebar: sidebarReducer,
  currentCase: caseReducer,
  caseAnalysis: visitDatesReducer,
});
