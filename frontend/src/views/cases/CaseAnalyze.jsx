import React, { Component, useRef, useState } from "react";
import { useSelector, useDispatch } from "react-redux";

import { CRow, CCol, CSpinner } from "@coreui/react";
import Select from "react-select";
import makeAnimated from "react-select/animated";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { CInput, CCard, CCardBody } from "@coreui/react";
import {
  loadAllVisitDates,
  setLastSearchedTerm,
} from "../../store/caseAnalysis";

const VisitDates = React.lazy(() => import("./VisitDates"));

const CaseAnalyze = (props) => {
  const dispatch = useDispatch();
  const [searchTerm, setSearchTerm] = useState();

  const { loading } = useSelector((state) => state.caseAnalysis);

  const searchEnterKeyPressed = (e) => {
    if (e.key === "Enter") {
      console.log("do validate");
      dispatch(setLastSearchedTerm(searchTerm));
      dispatch(loadAllVisitDates(null, searchTerm, null, null));
    }
  };

  const handleChangeInSearchTerm = ({ currentTarget: input }) => {
    setSearchTerm(input.value);
  };

  return (
    <div>
      <CCard>
        <CCardBody>
          {loading && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                position: "absolute",
                top: "50%",
                left: "50%",
                alignItems: "center",
                transform: "translateX(-50%) translateY(-50%)",
                zIndex: 9999,
                backgroundColor: "rgb(247, 247, 247, 0.8)",
                height: "100%",
                width: "100%",
                paddingTop: "50px",
                borderRadius: "0.25rem",
                paddingTop: "300px",
              }}
            >
              <CSpinner grow size="lg" color="primary" />
              Please wait while we load data...
            </div>
          )}
          <div
            style={{
              display: "inline-flex",
              marginBottom: "16px",
              width: "25%",
              flexWrap: "wrap",
              position: "relative",
              flexShrink: "0",
              alignItems: "center",
            }}
          >
            <CInput
              id="input3-group2"
              name="input3-group2"
              placeholder="Search"
              style={{
                width: "calc(100% - 38px)",
                padding: "8px 36px",
                borderRadius: "18px",
                position: "relative",
              }}
              onKeyDown={searchEnterKeyPressed}
              onChange={handleChangeInSearchTerm}
            />
            <FontAwesomeIcon
              icon={faSearch}
              color="#7b848f"
              style={{ right: "auto", left: "18px", position: "absolute" }}
            />
          </div>
          <VisitDates
          //   scrollToRef={scrollToRef}
          />
        </CCardBody>
      </CCard>
    </div>
  );
};

export default CaseAnalyze;
