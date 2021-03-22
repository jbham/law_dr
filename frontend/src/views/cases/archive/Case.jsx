// https://codepen.io/ayoungh/pen/xqRbeR
import React, { Component } from "react";
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
} from "@coreui/react";
// import TreeMenu from "react-simple-tree-menu";
// import "../../../node_modules/react-simple-tree-menu/dist/main.css";
import "react-toastify/dist/ReactToastify.css";
import { getAllFilesForCase } from "../../services/caseService";

const CaseFilesTable = React.lazy(() => import("./CaseFilesTable"));

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

class Case extends Component {
  constructor(props) {
    super(props);
    this.myRef = React.createRef();
    console.log("this the props from Case file", props);
    this.state = {
      casePrevPageObject: props.location.state,
      activeTab: "files",
      caseParentFiles: [],
      caseChildrenFiles: [],
      fields: [],
      caseRowDetails: [],
    };
  }

  componentDidMount() {
    this.fetchFilesInCase();
  }

  tabToggler = (tab) => {
    console.log("this is tab", tab);
    if (this.state.activeTab !== tab) {
      this.setState({
        activeTab: tab,
      });
      localStorage.setItem("activeTab", tab);
    }
  };

  getCreatedDate = () => {
    var sdf = new Date(this.state.casePrevPageObject.item.created_date); //.toDateString().substring(4);
    return sdf.toLocaleString();
  };

  formatBytes = (bytes, decimals = 2) => {
    if (bytes === 0) return "0 Bytes";

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  };

  groupBy = (list) => {
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
                list[i][key] = this.formatBytes(value);
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
          parentFiles[j]["total_split_files"] =
            parentFiles[j]["children"].length;
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

  fetchFilesInCase = async () => {
    try {
      var id = this.props.match.params.id;
      // console.log("This is props match id: " + id);
      const { data } = await getAllFilesForCase(id);

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

      const parentFiles = this.groupBy(data);

      for (var i = 0; i < parentFiles.length; i++) {
        for (const [key] of Object.entries(data[i])) {
          if (!fields.includes(key) && !childFields.includes(key)) {
            fields.push(key);
          }
        }
      }

      fields.push("Actions");

      // let childrenFields =
      this.setState({
        caseParentFiles: parentFiles,
        fields,
        // childrenFileFields: childrenFields
      });
    } catch (ex) {
      if ("message" in ex) {
        console.log("This is ex from fetchFilesInCase:", ex["message"]);
        // errors["message"] = ex["message"];
      } else if ("response" in ex) {
        console.log(
          "This is ex from fetchFilesInCase:",
          ex["response"]["data"]["detail"]
        );
        // errors["message"] = ex["response"]["data"]["detail"];
      }
    }
  };

  render() {
    //https://dowjones.github.io/react-dropdown-tree-select/#/story/readme

    const { caseParentFiles, casePrevPageObject, fields } = this.state;

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
                    <h5 style={{ margin: 0 }}>
                      {casePrevPageObject.item.name}
                    </h5>
                    <small>
                      <span style={{ marginRight: "20px" }}>
                        {`Created on: ${this.getCreatedDate()}`}
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
                      to={`/cases/${casePrevPageObject.item.id}`}
                      style={
                        this.state.activeTab === "files"
                          ? caseStyles.linkActive
                          : caseStyles.linkInActive
                      }
                      onClick={() => {
                        this.tabToggler("files");
                      }}
                    >
                      Files
                    </CNavLink>
                  </CNavItem>
                  <CNavItem>
                    <CNavLink
                      data-tab="analyze"
                      to={`/cases/${casePrevPageObject.item.id}/analyze`}
                      style={
                        this.state.activeTab === "analyze"
                          ? caseStyles.linkActive
                          : caseStyles.linkInActive
                      }
                      onClick={() => {
                        this.tabToggler("analyze");
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
        {this.state.activeTab === "files" && caseParentFiles.length > 0 && (
          <CaseFilesTable
            caseFiles={caseParentFiles}
            fields={fields}
            // caseChildrenFiles={caseChildrenFiles}
          ></CaseFilesTable>
        )}
        {this.state.activeTab === "analyze" && caseParentFiles.length > 0 && (
          <div className="">Test</div>
        )}
        <Switch>
          <Route
            path={`/cases/${casePrevPageObject.item.id}/analyze`}
            // component={CaseFilesV1}
            render={(props) => (
              <CFade>
                {console.log(
                  "This is the props from case return swithc route",
                  props
                )}
                {/* <CaseFilesV1 {...props} /> */}
              </CFade>
            )}
          />
        </Switch>
      </div>
    );
  }
}

export default Case;
