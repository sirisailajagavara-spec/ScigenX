import { configureStore } from "@reduxjs/toolkit";
import researchReducer from "./researchSlice";

export const store = configureStore({
  reducer: {
    research: researchReducer,
  },
});

export default store;
