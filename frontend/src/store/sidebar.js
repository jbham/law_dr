import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  sidebarShow: localStorage.getItem("sidebarShow")
    ? localStorage.getItem("sidebarShow")
    : "responsive",
};

const slice = createSlice({
  name: "sidebar",
  initialState: initialState,
  reducers: {
    set: (sidebar, action) => {
      console.log("sidebarrrrrr", sidebar, action.payload.sidebarShow);
      sidebar["sidebarShow"] = action.payload.sidebarShow;
    },
  },
});

export const { set } = slice.actions;
export default slice.reducer;
