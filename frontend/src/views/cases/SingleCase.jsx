import React, { useEffect, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import { useLocation } from "react-router-dom";
import { loadACase, setActiveTab, loadCaseFiles } from "../../store/case";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faFileAlt,
  faUser,
  faEnvelope,
} from "@fortawesome/free-solid-svg-icons";
import { Route, Switch } from "react-router-dom";
import {
  CCol,
  CRow,
  CContainer,
  CNav,
  CFade,
  CCard,
  CCardBody,
  CNavItem,
  CNavLink,
  CLink,
} from "@coreui/react";
import { useHistory } from "react-router";

const CaseFilesTable = React.lazy(() => import("./CaseFilesTable"));
const CaseAnalyze = React.lazy(() => import("./CaseAnalyze"));

const caseStyles = {
  linkActive: {
    color: "#006cfa",
    borderBottom: "3px solid #006cfa",
    textDecoration: "none",
    fontWeight: "500",
  },

  linkInActive: {
    color: "#4B4B4B",
  },
};

const scrollToRef = (ref) => window.scrollTo(0, ref.current.offsetTop);

const SingleCase = () => {
  const history = useHistory();
  const myRef = useRef();

  const executeScroll = () => scrollToRef(myRef);
  const location = useLocation();
  console.log(location);

  const uriCaseId = location.pathname.split("/")[2];

  const dispatch = useDispatch();
  const {
    caseDetails,
    activeTab,
    caseParentFiles,
    // fields,
    loading,
  } = useSelector((state) => state.currentCase);

  useEffect(() => {
    let subTab = location.pathname.split("/")[3];
    if (uriCaseId === "undefined") {
      dispatch(setActiveTab("files"));
      history.push("/cases/");
    } else if (caseDetails["id"] !== Number(uriCaseId)) {
      dispatch(loadACase(uriCaseId));
      if (subTab) {
        dispatch(setActiveTab(subTab));
      }
      if (!subTab) {
        dispatch(setActiveTab("files"));
      }
    }
  }, [caseDetails, caseParentFiles]);

  const getCreatedDate = () => {
    var sdf = new Date(caseDetails.created_date); //.toDateString().substring(4);
    return sdf.toLocaleString();
  };

  const tabToggler = (tab) => {
    if (activeTab !== tab) {
      dispatch(setActiveTab(tab));
    }
  };

  return (
    <div style={{ padding: "0px" }}>
      <CCard>
        <CCardBody style={{ padding: "0px 0px 0px 0px" }}>
          <CContainer fluid>
            <CRow
              style={{ borderBottom: "solid 1px #dcdfe3" }}
              className="d-flex justify-content-around"
            >
              <CCol
                style={{ padding: "10px" }}
                className="d-flex align-items-center"
              >
                <FontAwesomeIcon
                  icon={faFileAlt}
                  color="#7b848f"
                  size="2x"
                  style={{ marginRight: "10px" }}
                />
                <div>
                  <h5 style={{ margin: 0 }}>{caseDetails.name}</h5>
                  <small>
                    <span style={{ marginRight: "20px" }}>
                      {`Created on: ${getCreatedDate()}`}
                    </span>
                  </small>
                </div>
              </CCol>

              <div
                style={{
                  flexShrink: 0,
                  width: "1px",
                  // height: "100%",
                  backgroundColor: "#dcdfe3",
                }}
              ></div>
              <CCol
                style={{ padding: "10px" }}
                className="d-flex align-items-center"
              >
                <FontAwesomeIcon
                  icon={faUser}
                  color="#7b848f"
                  size="2x"
                  style={{ marginRight: "10px" }}
                />

                <div>
                  <h5 style={{ margin: 0 }}>Client Name</h5>
                  <small>
                    <span style={{ marginRight: "20px" }}>
                      Mobile: (408) 123-4567
                    </span>
                    <span>
                      <FontAwesomeIcon
                        icon={faEnvelope}
                        color="#7b848f"
                        style={{ marginRight: "2px" }}
                      />
                      awesomeuser@awesomecompany.com
                    </span>
                  </small>
                </div>
              </CCol>
            </CRow>
            <CRow style={{ paddingTop: "30px" }}>
              <CNav>
                <CNavItem>
                  <CNavLink
                    data-tab="files"
                    to={`/cases/${caseDetails.id}`}
                    style={
                      activeTab === "files"
                        ? caseStyles.linkActive
                        : caseStyles.linkInActive
                    }
                    onClick={() => {
                      tabToggler("files");
                    }}
                  >
                    Files
                  </CNavLink>
                </CNavItem>
                <CNavItem>
                  <CNavLink
                    data-tab="analyze"
                    to={`/cases/${caseDetails.id}/analyze`}
                    style={
                      activeTab === "analyze"
                        ? caseStyles.linkActive
                        : caseStyles.linkInActive
                    }
                    onClick={() => {
                      tabToggler("analyze");
                    }}
                  >
                    Analyze
                  </CNavLink>
                </CNavItem>
              </CNav>
            </CRow>
          </CContainer>
        </CCardBody>
      </CCard>
      {activeTab === "files" && (
        <CFade>
          <CaseFilesTable></CaseFilesTable>
        </CFade>
      )}
      <Switch>
        <Route
          path={`/cases/${caseDetails.id}/analyze`}
          // component={CaseFilesV1}
          render={(props) => {
            console.log("from singlecase.jsx", props);
            return (
              <CFade>
                <CaseAnalyze
                //   myref={myref}
                //   executeScroll={executeScroll}
                ></CaseAnalyze>
              </CFade>
            );
          }}
        />
      </Switch>
    </div>
  );
};

export default SingleCase;
