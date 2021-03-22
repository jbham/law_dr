import React, { useState, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";

import {
  CDataTable,
  CButton,
  CCardBody,
  CCard,
  CContainer,
  CModal,
  CModalHeader,
  CModalTitle,
  CModalBody,
} from "@coreui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import {
  faCheckCircle,
  faExclamationCircle,
  faSpinner,
} from "@fortawesome/free-solid-svg-icons";

import { loadCaseFiles } from "../../store/case";

const CaseFileTable = (props) => {
  const [details, setDetails] = useState([]);
  const [large, setLarge] = useState(false);

  const dispatch = useDispatch();
  const {
    caseDetails,
    activeTab,
    caseParentFiles,
    fields,
    loading,
  } = useSelector((state) => state.currentCase);

  const toggleDetails = (index) => {
    const position = details.indexOf(index);
    let newDetails = details.slice();
    if (position !== -1) {
      newDetails.splice(position, 1);
    } else {
      newDetails = [...details, index];
    }
    setDetails(newDetails);
  };

  useEffect(() => {
    dispatch(loadCaseFiles(caseDetails["id"]));
  }, [caseDetails]);

  const closeModelAndToggleIndex = (index) => {
    toggleDetails(index);
    setLarge(!large);
  };

  const getBadge = (status) => {
    switch (status) {
      case "Successful":
        return (
          <FontAwesomeIcon
            icon={faCheckCircle}
            color="#0fa873"
            style={{ marginLeft: "75px" }}
          />
        );
      case "Processing":
        return <FontAwesomeIcon icon={faSpinner} />;
      case "Initiated":
        return <FontAwesomeIcon icon={faSpinner} />;
      case "Failed":
        return <FontAwesomeIcon icon={faExclamationCircle} color="#F90606" />;
      default:
        return <FontAwesomeIcon icon={faSpinner} />;
    }
  };

  return (
    <div>
      <CCard>
        <CCardBody>
          <CContainer fluid>
            {/* {console.log("whaaaaaat", props.caseFiles, props.fields)} */}
            <CDataTable
              items={caseParentFiles}
              fields={fields}
              columnFilter={caseParentFiles.length > 0 ? true : false}
              responsive
              loading={loading}
              tableFilter={caseParentFiles.length > 1 ? true : false}
              border
              itemsPerPageSelect={caseParentFiles.length > 0 ? true : false}
              itemsPerPage={10}
              hover
              sorter
              pagination
              scopedSlots={{
                Actions: (item, index) => {
                  return (
                    <td className="py-2">
                      <CButton
                        color="info"
                        variant="outline"
                        shape="square"
                        size="sm"
                        onClick={() => {
                          toggleDetails(index);
                        }}
                      >
                        {/* {details.includes(index) ? "Hide" : "Show"} */}
                        Show Files
                      </CButton>
                      {"  "}
                      <CButton
                        color="danger"
                        variant="outline"
                        shape="square"
                        size="sm"
                        onClick={() => {
                          toggleDetails(index);
                        }}
                      >
                        Delete
                      </CButton>
                    </td>
                  );
                },
                details: (item, index) => {
                  return (
                    //   <CCollapse show={details.includes(index)}></CCollapse>
                    <CModal
                      show={details.includes(index)}
                      onClose={() => {
                        closeModelAndToggleIndex(index);
                      }}
                      size="xl"
                      style={{ width: "120%" }}
                      closeOnBackdrop={false}
                    >
                      <CModalHeader closeButton>
                        <CModalTitle>
                          <span className="text-muted">File Name: </span>{" "}
                          {item.name}
                        </CModalTitle>
                      </CModalHeader>
                      <CModalBody>
                        <CDataTable
                          items={item.children}
                          fields={[
                            "split_file_id",
                            "new_file_name",
                            "file_process_status",
                            "file_split_status",
                            "terms_extraction_status",
                            "total_split_pages",
                            "Actions",
                          ]}
                          columnFilter
                          responsive
                          border
                          tableFilter
                          itemsPerPageSelect
                          itemsPerPage={10}
                          hover
                          sorter
                          pagination
                          scopedSlots={{
                            file_process_status: (item) => (
                              <td>{getBadge(item.file_process_status)}</td>
                            ),
                            file_split_status: (item) => (
                              <td>{getBadge(item.file_split_status)}</td>
                            ),
                            terms_extraction_status: (item) => (
                              <td>{getBadge(item.terms_extraction_status)}</td>
                            ),
                            Actions: () => {
                              return (
                                <td className="py-2">
                                  <CButton
                                    color="info"
                                    variant="outline"
                                    shape="square"
                                    size="sm"
                                    onClick={() => {
                                      toggleDetails(index);
                                    }}
                                  >
                                    {/* {details.includes(index) ? "Hide" : "Show"} */}
                                    View File
                                  </CButton>
                                  {"  "}
                                  <CButton
                                    color="danger"
                                    variant="outline"
                                    shape="square"
                                    size="sm"
                                    onClick={() => {
                                      toggleDetails(index);
                                    }}
                                  >
                                    Delete
                                  </CButton>
                                </td>
                              );
                            },
                          }}
                        />
                      </CModalBody>
                    </CModal>
                  );
                },
              }}
            />
          </CContainer>
        </CCardBody>
      </CCard>
    </div>
  );
};

export default CaseFileTable;
