import { createStore } from "redux";
import configureStore from "./configureStore";
import { set } from "./sidebar";

// const initialState = {
//   sidebarShow: localStorage.getItem("sidebarShow")
//     ? localStorage.getItem("sidebarShow")
//     : "responsive",
// };

// const changeState = (state = initialState, { type, ...rest }) => {
//   switch (type) {
//     case "set":
//       return { ...state, ...rest };
//     default:
//       return state;
//   }
// };

const store = configureStore();

// store.dispatch(set({ sidebarShow: false }));
export default store;
