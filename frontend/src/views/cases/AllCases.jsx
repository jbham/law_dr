import React, { useEffect, useState } from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  loadCases,
  casesModalToggle,
  caseCreateValidationError,
  caseCreated,
  caseNumberReceived,
  createCaseOnServer,
} from "../../store/cases";

import { caseBeingViewed } from "../../store/case";
import Joi from "joi-browser";
import {
  CCard,
  CCol,
  CRow,
  CForm,
  CFormGroup,
  CButton,
  CModal,
  CModalHeader,
  CModalFooter,
  CModalBody,
  CInput,
  CAlert,
  CToast,
  CToastBody,
  CToastHeader,
  CToaster,
  CLink,
  CCardBody,
  CDataTable,
} from "@coreui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faLink, faPlus } from "@fortawesome/free-solid-svg-icons";

const localToaster = (key, position, title, message) => {
  return (
    <CToaster position={position} key={"toaster" + position}>
      <CToast key={"toast" + key} show={true} autohide={5000} fade={true}>
        <CToastHeader closeButton={true}>{title}</CToastHeader>
        <CToastBody>{message}</CToastBody>
      </CToast>
    </CToaster>
  );
};

const loading1 = (
  <div
    className="d-flex justify-content-center align-items-center text-muted"
    style={{ width: "100%", height: "80vh", flexDirection: "column" }}
  >
    If there are cases, then they will appear. Click Add Case to create a new
    case
  </div>
);

function AllCases(props) {
  const dispatch = useDispatch();
  const {
    cases,
    loading,
    fields,
    success,
    errors,
    case_number,
    info,
  } = useSelector((state) => state.cases);

  //   console.log(cases, loading, fields, success, errors, case_number, info);

  useEffect(() => {
    dispatch(loadCases());
  }, []);

  const createCase = () => {
    dispatch(createCaseOnServer({ case_number }));
  };

  const toggleInfo = () => {
    dispatch(casesModalToggle({ info: !info }));
  };

  const validateProperty = ({ name, value }) => {
    var sch = {
      case_number: Joi.string().min(3).max(30).strip().required(),
    };
    const obj = { [name]: value };
    const schema = { [name]: sch[name] };
    const { error } = Joi.validate(obj, schema);
    return error ? error.details[0].message : null;
  };

  const handleChange = ({ currentTarget: input }) => {
    const errorMessage = validateProperty(input);
    if (errorMessage) {
      //   errors["message"] = errorMessage;
      //   errors["has_error"] = true;
      dispatch(
        caseCreateValidationError({
          errors: { message: errorMessage, has_error: true },
        })
      );
    } else {
      dispatch(
        caseNumberReceived({
          errors: { message: errorMessage, has_error: false },
          case_number: input.value,
        })
      );
    }
  };

  const setCaseBeingViewed = (item) => {
    dispatch(caseBeingViewed(item));
  };

  return (
    <div className="animated fadeIn" style={{ paddingTop: "0px" }}>
      <CRow className="align-items-right">
        <CCol>
          <h3>Cases</h3>
        </CCol>
        <CCol>
          {success.message &&
            localToaster(1, "bottom-right", "Notification", success.message)}

          <div className="float-right">
            <CButton
              block
              shape="pill"
              color="info"
              className=""
              onClick={toggleInfo}
            >
              <FontAwesomeIcon
                icon={faPlus}
                // color="#7b848f"
                // style={{ marginRight: "10px" }}
              />{" "}
              &nbsp; Add Case
            </CButton>
          </div>
        </CCol>
      </CRow>
      <CRow>
        <CCol>
          <div className="card-header-actions">
            <CModal
              show={info}
              onClose={toggleInfo}
              // className={"modal-info " + this.props.className}
            >
              <CModalHeader closeButton>
                <strong>Create New Case</strong>
              </CModalHeader>
              <CModalBody>
                <CForm>
                  <CFormGroup row />{" "}
                  <CInput
                    id="case_number"
                    name="case_number"
                    onChange={handleChange}
                    autoFocus={true}
                    type="text"
                    placeholder="Case Name"
                  />
                  &nbsp;
                  <small>
                    {errors.has_error && (
                      <CAlert color="danger">{errors.message}</CAlert>
                    )}
                  </small>
                </CForm>
              </CModalBody>
              <CModalFooter>
                <CButton
                  color="info"
                  disabled={errors.has_error || case_number.length === 0}
                  onClick={createCase}
                >
                  Create
                </CButton>{" "}
                <CButton color="secondary" onClick={toggleInfo}>
                  Cancel
                </CButton>
              </CModalFooter>
            </CModal>
          </div>

          {/* {cases.length > 0 ? (
              //   <CRow>
              //     {cases.map((id) => (
              //       <CCol xs="12" sm="6" lg="3">
              //         <CaseComponent
              //           header={id.name}
              //           mainText={id.customer_name}
              //           icon="fa fa-cogs"
              //           color="primary"
              //           footer
              //           link={`/cases/${id.id}`}
              //         />
              //       </CCol>
              //     ))}
              //   </CRow>
              // ) : (
              //   this.loading
              // )} */}
          {/* {noCase ? null : (
                <large className="text-muted text-center">
                  No Case found. Click Create to create a new case.
                </large>
              )} */}
        </CCol>
      </CRow>

      {cases.length > 0 ? (
        <CCard style={{ marginTop: "10px" }}>
          <CCardBody>
            <CRow>
              <CCol xs="12" sm="12" md="12" lg="12">
                <div style={{ background: "white", paddingBottom: "5px" }}>
                  <CDataTable
                    items={cases}
                    fields={fields}
                    // dark
                    hover
                    striped
                    bordered
                    clickableRows
                    sorter={{ resetable: true }}
                    outlined
                    // size="sm"
                    itemsPerPage={10}
                    pagination
                    scopedSlots={{
                      Actions: (item) => {
                        // console.log(item);
                        return (
                          <td>
                            <CLink
                              onClick={() => setCaseBeingViewed(item)}
                              to={{
                                pathname: `/cases/${item.id}`,
                                state: { item: item },
                              }}
                            >
                              <FontAwesomeIcon
                                icon={faLink}
                                color="#7b848f"
                                // style={{ marginRight: "10px" }}
                              />{" "}
                              Open{" "}
                            </CLink>
                          </td>
                        );
                      },
                    }}
                  />
                </div>
              </CCol>
            </CRow>
          </CCardBody>
        </CCard>
      ) : (
        loading1
      )}
    </div>
  );
}

export default AllCases;
