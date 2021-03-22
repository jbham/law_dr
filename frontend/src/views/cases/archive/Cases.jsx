import React, { Component } from "react";
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
// import FormClass from "../../common/form";
// import CaseComponent from "./CaseComponent";
import { getAllCases, createBackendCase } from "../../services/fileService";
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

class Cases extends Component {
  // eslint-disable-next-line no-useless-constructor
  constructor(props) {
    super(props);
    console.log("this is the props");
    console.log(props);
    this.state = {
      cases: [],
      fields: [],
      info: false,
      errors: {},
      success: {},
      noCase: true,
      case_number: "",
    };
  }

  loading = () => (
    <div className="animated fadeIn pt-1 text-center">Loading...</div>
  );

  schema = {
    case_number: Joi.string().min(3).max(30).strip().required(),
  };

  toggleInfo = () => {
    this.setState({
      info: !this.state.info,
    });
  };

  fetchCases = async () => {
    try {
      const { data } = await getAllCases();
      // let lists = [...this.state.cases];
      let fields = [];
      // lists.push(data);
      for (var i = 0; i < data.length; i++) {
        for (const [key, value] of Object.entries(data[i])) {
          console.log(key, value);
          if (!fields.includes(key)) {
            fields.push(key);
          }
        }
      }
      fields.push("Actions");
      this.setState({
        cases: data,
        fields,
      });
    } catch (ex) {
      console.log("This is ex from fetchCases:");
      console.log(ex);
      const noCase = { ...this.state.noCase };
      this.setState({ noCase: !noCase });
    }
  };

  componentDidMount() {
    this.fetchCases();
  }

  validateProperty = ({ name, value }) => {
    const obj = { [name]: value };
    const schema = { [name]: this.schema[name] };
    const { error } = Joi.validate(obj, schema);
    return error ? error.details[0].message : null;
  };

  handleChange = ({ currentTarget: input }) => {
    const errors = { ...this.state.errors };
    const errorMessage = this.validateProperty(input);
    if (errorMessage) {
      errors["message"] = errorMessage;
      errors["has_error"] = true;
      this.setState({ errors, case_number: null });
    } else {
      errors["has_error"] = false;
      errors["message"] = null;
      this.setState({ errors, case_number: input.value });
    }
    console.log(this.state.data);
  };

  createCase = async () => {
    try {
      await createBackendCase(this.state.case_number);
      const success = { ...this.state.success };
      success[
        "message"
      ] = `Case '${this.state.case_number}' successfully created`;
      this.setState({
        info: !this.state.info,
        success,
      });
      this.fetchCases();
    } catch (ex) {
      const noCase = { ...this.state.noCase };
      const errors = { ...this.state.errors };
      if ("message" in ex) {
        console.log("This is ex from fetchCases:", ex["message"]);
        errors["message"] = ex["message"];
      } else if ("response" in ex) {
        console.log(
          "This is ex from fetchCases:",
          ex["response"]["data"]["detail"]
        );
        errors["message"] = ex["response"]["data"]["detail"];
      }

      errors["has_error"] = true;
      this.setState({ noCase: !noCase, errors });
    }
  };

  render() {
    const { cases, errors, success, fields, case_number } = this.state;

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
                onClick={this.toggleInfo}
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
                show={this.state.info}
                onClose={this.toggleInfo}
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
                      onChange={this.handleChange}
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
                    onClick={this.createCase}
                  >
                    Create
                  </CButton>{" "}
                  <CButton color="secondary" onClick={this.toggleInfo}>
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
                          console.log(item);
                          return (
                            <td>
                              <CLink
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
}

export default Cases;
