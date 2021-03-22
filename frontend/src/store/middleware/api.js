import axios from "axios";
import * as actions from "../api";

// example request
// const action = {
//   type: "apiCallBegan",
//   payload: {
//     url: "",
//     method: "get",
//     data: {},
//     onSuccess: "onSuccess",
//     onError: "onError",
//   },
// };

const api = (store) => (next) => async (action) => {
  if (action.type !== actions.apiCallBegan.type) return next(action);

  const {
    url,
    method,
    data,
    headers,
    onStart,
    onSuccess,
    onError,
    params,
  } = action.payload;
  console.log(url, method, data, headers, onStart, onSuccess, onError, params);

  if (onStart) store.dispatch({ type: onStart });
  next(action);

  try {
    const response = await axios.request({
      baseURL: url,
      //   url,
      method,
      data,
      headers,
      params,
    });
    // General
    store.dispatch(actions.apiCallSuccess(response.data));

    // Specific
    if (onSuccess) store.dispatch({ type: onSuccess, payload: response.data });
  } catch (error) {
    console.log(error);
    // General
    store.dispatch(actions.apiCallFailed(error.message));

    // Specific
    if (onError) store.dispatch({ type: onError, payload: error.message });
  }
};

export default api;
