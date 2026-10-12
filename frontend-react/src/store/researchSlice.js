import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  researchQuestion: "",
  researchResults: null,
  loading: false,
  error: null,
};

const researchSlice = createSlice({
  name: "research",
  initialState,
  reducers: {
    setResearchQuestion: (state, action) => {
      state.researchQuestion = action.payload;
    },

    setResearchResults: (state, action) => {
      state.researchResults = action.payload;
    },

    setLoading: (state, action) => {
      state.loading = action.payload;
    },

    setError: (state, action) => {
      state.error = action.payload;
    },

    clearResearch: (state) => {
      state.researchQuestion = "";
      state.researchResults = null;
      state.loading = false;
      state.error = null;
    },
  },
});

export const {
  setResearchQuestion,
  setResearchResults,
  setLoading,
  setError,
  clearResearch,
} = researchSlice.actions;

export default researchSlice.reducer;
