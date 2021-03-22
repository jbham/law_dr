// <a href="https://www.freepik.com/free-photos-vectors/medical">Medical photo created by kjpargeter - www.freepik.com</a>
// <a href="https://www.freepik.com/free-photos-vectors/medical">Medical photo created by kjpargeter - www.freepik.com</a>

import React, { Component } from "react";
import {
  Collapse,
  Col,
  FormGroup,
  Card,
  CardHeader,
  CardBody,
  Button,
  Input,
  Row,
  Badge,
  Label,
  Table
} from "reactstrap";
import Select from "react-select";
import makeAnimated from "react-select/animated";
import {
  getSearchFacet,
  getSpecificCatefory,
  getAllConfirmedVisitDates,
  getTextByVisitDates
} from "../../services/searchService";
import { downloadFile } from "../../services/fileService";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Spinner from "./../pdfHighlighter/Spinner";
import AWS from "aws-sdk";

import {
  PdfLoader,
  PdfHighlighter,
  Tip,
  Highlight,
  Popup,
  AreaHighlight
  // } from "react-pdf-highlighter";
} from "./../pdfHighlighter/core";

const resetHash = () => {
  window.location.hash = "";
};

const HighlightPopup = ({ comment }) =>
  comment.text ? (
    <div className="Highlight__popup">
      {comment.emoji} {comment.text}
    </div>
  ) : null;

const DEFAULT_URL = "https://arxiv.org/pdf/1708.08021.pdf";
const url = DEFAULT_URL;

const parseIdFromHash = () => {
  console.log(window.location.hash);
  console.log(window.location.hash.slice("#highlight-".length));
  return window.location.hash.slice("#highlight-".length);
};

const getNextId = () => String(Math.random()).slice(2);

const updateHash = highlight => {
  window.location.hash = `highlight-${highlight.id}`;
};

class CaseFiles extends Component {
  constructor(props) {
    super(props);
    this.onEntering = this.onEntering.bind(this);
    this.onEntered = this.onEntered.bind(this);
    this.onExiting = this.onExiting.bind(this);
    this.onExited = this.onExited.bind(this);
    this.toggle = this.toggle.bind(this);
    this.myRef = React.createRef();
    this.state = {
      collapse: [false],
      showArrow: false,
      fadeIn: true,
      timeout: 300,
      topFive: {},
      sharedStartLimit: {
        start: 0,
        limit: 25,
        max: 0,
        totalFetched: 0,
        cat: null
      },
      topFiveLoaded: false,
      rest: {},
      showAll: false,
      resultListDisplay: [],
      visitDates: [],
      vistDateSelected: null,
      searchTxt: "",
      loadMoreTextByVisitDate: Boolean,
      pdfDoc: null,
      highlights: [
        {
          content: {
            text:
              "This fuels a fast edit-refresh cycle, whichpromises an immersive coding experience that is quite appealing to creative developers."
          },
          //(102.55000305175781, 499.9259033203125, 486.5664978027344, 511.7129211425781)
          position: {
            boundingRect: {
              x1: 170.916603386260982,
              y1: 833.209805538793945,
              x2: 810.944130566790813,
              y2: 852.854834456768757,
              width: 991.199911523876953,
              height: 1291.799976811071861
            },
            rects: [
              {
                x1: 170.916603386260982,
                y1: 833.209805538793945,
                x2: 810.944130566790813,
                y2: 852.854834456768757,
                width: 991.199911523876953,
                height: 1291.799976811071861
              }
            ],
            pageNumber: 3
          },
          comment: {
            text: "immersive coding experience!",
            emoji: ""
          },
          id: "2599712881412761"
        }
      ]
    };
  }

  loadCategories = async () => {
    try {
      var id = this.props.match.params.id;
      const { data } = await getSearchFacet(id);
      let topFive = { ...this.state.topFive };
      let rest = { ...this.state.rest };
      const tfc = [
        "Injury or Poisoning",
        "Sign or Symptom",
        "Body Part, Organ, or Organ Component",
        "Anatomical Abnormality",
        "Diagnostic Procedure"
      ];
      Object.keys(data).map(function(key) {
        if (tfc.includes(key)) {
          if (key == "Body Part, Organ, or Organ Component") {
            topFive["Body Part/Organ"] = data[key];
          } else {
            topFive[key] = data[key];
          }
        } else {
          rest[key] = data[key];
        }
      });
      let topFiveLoadedOrNot =
        Object.keys(topFive).length > 0 && topFive.constructor === Object
          ? true
          : false;
      this.setState({
        topFive,
        rest,
        topFiveLoaded: topFiveLoadedOrNot
      });
    } catch (ex) {
      console.log(ex.response);
    }
  };

  showHideAllCate = () => {
    this.setState({ showAll: !this.state.showAll });
  };

  fetchCat = async (cat, startAt0) => {
    console.log(":Test");

    var id = this.props.match.params.id;
    const { limit, cat: previous_cat } = this.state.sharedStartLimit;
    if (previous_cat != cat) {
      const { data } = await getSpecificCatefory(id, startAt0, limit, cat);

      let sharedStartLimit = { ...this.state.sharedStartLimit };
      sharedStartLimit.start = startAt0 + limit;
      sharedStartLimit.max = data.numFound;
      sharedStartLimit.totalFetched = data.docs.length;
      sharedStartLimit.cat = cat;
      this.setState({
        resultListDisplay: data.docs,
        sharedStartLimit,
        pdfDoc: null
      });
      console.log(this.state);
      this.scrollToMyRef();
    } else {
      toast.warn("Selection already displayed");
    }
  };

  searchTextByVisitDate = async startAt0 => {
    var id = this.props.match.params.id;
    const { vistDateSelected: vds, searchTxt } = this.state;
    let sharedStartLimit = { ...this.state.sharedStartLimit };

    const { data } = await getTextByVisitDates(
      id,
      vds,
      searchTxt,
      startAt0,
      sharedStartLimit.limit
    );
    console.log(data);

    console.log(startAt0, sharedStartLimit.limit);
    sharedStartLimit.start = startAt0 + sharedStartLimit.limit;
    sharedStartLimit.max = data["numFound"];
    sharedStartLimit.totalFetched = data["docs"].length;
    this.setState({
      resultListDisplay: data["docs"],
      sharedStartLimit,
      loadMoreTextByVisitDate: true,
      pdfDoc: null
    });
    console.log(this.state);
    this.scrollToMyRef();
  };

  sharedLoadMore = async () => {
    var id = this.props.match.params.id;
    let cl = [...this.state.resultListDisplay];
    const { start, limit, cat, totalFetched } = this.state.sharedStartLimit;
    const { loadMoreTextByVisitDate } = this.state;

    let data = null;

    if (loadMoreTextByVisitDate === true) {
      const { vistDateSelected: vds, searchTxt } = this.state;
      data = await getTextByVisitDates(id, vds, searchTxt, start, limit);
    } else {
      data = await getSpecificCatefory(id, start, limit, cat);
    }

    const { data: newData } = data;

    if (newData) {
      cl.push(...newData.docs);
      let sharedStartLimit = { ...this.state.sharedStartLimit };
      sharedStartLimit.start = start + limit;
      sharedStartLimit.totalFetched = totalFetched + newData.length;
      sharedStartLimit.cat = cat;
      this.setState({
        resultListDisplay: cl,
        sharedStartLimit
      });
    }
  };

  loadAllConfirmedVisitDates = async () => {
    var id = this.props.match.params.id;
    const { data } = await getAllConfirmedVisitDates(id);
    let visitDates = [...this.state.visitDates];
    for (var i = 0; i < data.length; i++) {
      var d = {
        value: i,
        label: data[i]["confirmed_visit_date"],
        isFixed: true
      };
      visitDates.push(d);
    }

    this.setState({ visitDates });
  };

  dnFile = async index => {
    this.setState({ pdfDoc: null });
    var id = this.props.match.params.id;
    var m = { ...this.state.resultListDisplay[index] };
    console.log(this.state);

    // Get file location and credentials to fetch from s3 directly
    const { data } = await downloadFile(
      m["file_id"],
      m["file_state_id"],
      m["id"]
    );

    let loc = data["loc"];
    let bucket = data["bucket"];
    let AccessKeyId = data["response"]["AccessKeyId"];
    let SecretAccessKey = data["response"]["SecretAccessKey"];
    let SessionToken = data["response"]["SessionToken"];

    AWS.config.update({
      region: "us-west-2",
      accessKeyId: AccessKeyId,
      secretAccessKey: SecretAccessKey,
      sessionToken: SessionToken
    });

    var s3 = new AWS.S3();

    const param = {
      Bucket: bucket,
      Key: loc
    };

    try {
      const response = await s3.getObject(param).promise();
      console.log(response);
      this.setState(
        { pdfDoc: response.Body }
        // , function afterStateChange() {}
      );
    } catch (err) {
      console.error(err);
    }

    setTimeout(() => {
      updateHash(this.state.highlights[0]);
    }, 500);
  };

  searchTxtHandler = e => {
    console.log(e.currentTarget.value);
    this.setState({
      searchTxt: e.currentTarget.value
    });
  };

  vistDateSelected = optionSelected => {
    let vds = "";
    if (optionSelected) {
      optionSelected.map((o, i) => {
        if (i > 0) {
          vds += ",";
        }
        console.log(o.label, i);
        vds = vds + o.label;
      });
    }
    this.setState({
      vistDateSelected: vds
    });
  };

  scrollToHighlightFromHash = () => {
    const highlight = this.getHighlightById(parseIdFromHash());

    if (highlight) {
      this.scrollViewerTo(highlight);
    }
  };

  getHighlightById(id: string) {
    const { highlights } = this.state;

    return highlights.find(highlight => highlight.id === id);
  }

  addHighlight(highlight: T_NewHighlight) {
    const { highlights } = this.state;

    console.log("Saving highlight", highlight);

    this.setState({
      highlights: [{ ...highlight, id: getNextId() }, ...highlights]
    });
  }

  updateHighlight(highlightId: string, position: Object, content: Object) {
    console.log("Updating highlight", highlightId, position, content);

    this.setState({
      highlights: this.state.highlights.map(h => {
        return h.id === highlightId
          ? {
              ...h,
              position: { ...h.position, ...position },
              content: { ...h.content, ...content }
            }
          : h;
      })
    });
  }

  scrollViewerTo = (highlight: any) => {};

  componentDidMount() {
    this.loadCategories();
    this.loadAllConfirmedVisitDates();
    window.addEventListener(
      "hashchange",
      this.scrollToHighlightFromHash,
      false
    );
  }

  scrollToMyRef = () =>
    this.myRef.current.scrollIntoView({
      behavior: "smooth",
      block: "nearest"
    });

  handleCollpase = e => {
    console.log("collasping...", e);

    const prevState = this.state.collapse;
    const state = prevState.map((x, index) => (e === index ? !x : x));
    console.log(e, state);
    this.setState({
      collapse: state
    });
  };

  handleMouseHover = () => {
    this.setState({ showArrow: !this.state.showArrow });
  };

  onEntering() {
    this.setState({ status: "Opening..." });
  }

  onEntered() {
    this.setState({ status: "Opened" });
  }

  onExiting() {
    this.setState({ status: "Closing..." });
  }

  onExited() {
    this.setState({ status: "Closed" });
  }

  toggle() {
    this.setState({ collapse: !this.state.collapse });
  }

  render() {
    const {
      topFive,
      rest,
      showAll,
      topFiveLoaded,
      resultListDisplay,
      sharedStartLimit,
      visitDates,
      highlights,
      pdfDoc
    } = this.state;

    return (
      <div
        className="animated fadeIn"
        style={{
          paddingTop: "10px",
          marginLeft: "-20px"
        }}
      >
        <ToastContainer />
        {/* <CardBody>
          <Button onClick={this.toggle}>Show/Hide Filters</Button>
        </CardBody> */}
        <Collapse
          isOpen={this.state.collapse}
          onEntering={this.onEntering}
          onEntered={this.onEntered}
          onExiting={this.onExiting}
          onExited={this.onExited}
        >
          {" "}
          <Row>
            <Col
              sm="3"
              style={{
                width: "100%",
                height: "100%",
                overflow: "hidden"
              }}
            >
              <h5>
                <strong className="text-muted">
                  {showAll === true ? "All Filters" : "Top Filters"}
                </strong>
              </h5>
              <hr
                style={{
                  marginTop: "-0.1em",
                  marginBottom: "1em"
                }}
              ></hr>

              {/* {{
                  width: "100%",
                  height: "100%",
                  overflowY: "scroll",
                  paddingRight: "17px",
                  boxSizing: "content-box"
                }} */}
              <div
                style={{
                  height: "15vw",
                  overflow: "auto",
                  position: "relative",
                  paddingRight: "17px"
                }}
              >
                {topFiveLoaded === true ? (
                  Object.keys(topFive).map(key => {
                    return (
                      <Row key={key}>
                        <Col>
                          <Button
                            key={key}
                            color="link"
                            size="sm"
                            onClick={() => this.fetchCat(key, 0)}
                          >
                            {key} ({topFive[key]})
                          </Button>
                        </Col>
                      </Row>
                    );
                  })
                ) : (
                  <div className="d-flex justify-content-center">
                    <div
                      className="spinner-border text-secondary"
                      role="status"
                    >
                      <span className="sr-only">Loading...</span>
                    </div>
                  </div>
                )}

                {showAll === true && topFiveLoaded === true
                  ? Object.keys(rest).map(key => {
                      return (
                        <Row key={key}>
                          <Col>
                            <Button
                              key={key}
                              color="link"
                              size="sm"
                              text-left
                              onClick={() => this.fetchCat(key, 0)}
                            >
                              {key} ({rest[key]})
                            </Button>
                          </Col>
                        </Row>
                      );
                    })
                  : null}

                {topFiveLoaded === true && (
                  <Row>
                    <Col>
                      <Button
                        color="link"
                        size="sm"
                        onClick={() => this.showHideAllCate()}
                      >
                        {showAll === true ? "Hide" : "Show all"}
                      </Button>
                    </Col>
                  </Row>
                )}
              </div>
            </Col>

            <Col sm="9">
              <h5>
                <strong className="text-muted">More ways to filter</strong>
              </h5>
              <hr
                style={{
                  marginTop: "-0.1em",
                  marginBottom: "1em"
                }}
              ></hr>

              <Select
                closeMenuOnSelect={false}
                components={makeAnimated()}
                // defaultValue={[colourOptions[4], colourOptions[5]]}
                isMulti
                placeholder="Visit Date"
                options={visitDates}
                onChange={this.vistDateSelected}
              />
              <Row>
                <Col sm="3">
                  <FormGroup row style style={{ marginTop: "1em" }}>
                    <Col md="12">
                      <Input
                        type="text"
                        id="input1-group2"
                        name="input1-group2"
                        placeholder="Search"
                        onChange={this.searchTxtHandler}
                      />
                    </Col>
                    <Col md="9">
                      <Button
                        type="button"
                        color="primary"
                        block
                        style={{ marginTop: "1em" }}
                        onClick={() => this.searchTextByVisitDate(0)}
                      >
                        Search <i className="fa fa-search"></i>
                      </Button>
                    </Col>
                  </FormGroup>
                </Col>
                <Col sm="3">
                  <FormGroup check inline style={{ marginTop: "1em" }}>
                    <Input
                      className="form-check-input"
                      type="checkbox"
                      id="inline-checkbox1"
                      name="inline-checkbox1"
                      value="option1"
                    />
                    <Label
                      className="form-check-label"
                      check
                      htmlFor="inline-checkbox1"
                    >
                      Show only visit date(s)
                    </Label>
                  </FormGroup>
                </Col>
              </Row>
            </Col>
          </Row>
        </Collapse>{" "}
        {/* <Col
            style={{
              width: "0.5px",
              backgroundColor: "#eeeeee",
              marginLeft: "5px",
              marginRight: "5px"
            }}
          ></Col> */}
        <div ref={this.myRef}>
          <Row>
            <Col
              sm="6"
              style={{
                height: "50vw",
                overflowY: "auto",
                position: "relative"
              }}
            >
              <div style={{ fontSize: "14px" }}>
                <Card>
                  <CardHeader>
                    <i className="fa fa-align-justify"></i> Simple Table
                  </CardHeader>
                  <CardBody>
                    <Table responsive hover>
                      <thead>
                        <tr>
                          <th className="text-center" style={{ width: "25%" }}>
                            Text
                          </th>
                          <th className="text-center" style={{ width: "25%" }}>
                            PDF excerpt
                          </th>
                          <th className="text-center" style={{ width: "25%" }}>
                            Visit Date
                          </th>
                          <th className="text-center" style={{ width: "25%" }}>
                            Last modified date
                          </th>
                        </tr>
                      </thead>

                      <tbody>
                        {resultListDisplay.map((cat, index) => (
                          <tr
                            key={index}
                            style={{
                              backgroundColor:
                                cat.polarity === 1
                                  ? "#BDF4C1"
                                  : cat.polarity === -1
                                  ? "#F4C7BD"
                                  : "none"
                            }}
                          >
                            <td
                              className="text-center"
                              onClick={() => this.dnFile(index)}
                            >
                              {cat.text}
                            </td>
                            <td className="text-center">
                              ...
                              {cat.full_text.substring(
                                0,
                                cat.full_text.indexOf(cat.text)
                              )}
                              <strong>
                                {cat.full_text.substring(
                                  cat.full_text.indexOf(cat.text),
                                  cat.full_text.indexOf(cat.text) +
                                    cat.text.length
                                )}
                              </strong>
                              {cat.full_text.substring(
                                cat.full_text.indexOf(cat.text) +
                                  cat.text.length,
                                cat.full_text.length
                              )}
                              ...
                            </td>
                            <td className="text-center">
                              {cat.confirmed_visit_date}
                            </td>
                            <td className="text-center">{cat.modified_date}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </CardBody>
                </Card>
              </div>
              {sharedStartLimit.start < sharedStartLimit.max ? (
                <Col className="text-center">
                  <Button
                    outline
                    color="link"
                    className="pull-center"
                    onClick={() => this.sharedLoadMore()}
                  >
                    Click to load more...
                  </Button>
                </Col>
              ) : null}
            </Col>
            <Col
              sm="6"
              style={{
                height: "50vw",
                overflowY: "auto",
                position: "relative"
              }}
            >
              {pdfDoc && (
                <PdfLoader url={pdfDoc} beforeLoad={<Spinner />}>
                  {pdfDocument => (
                    <PdfHighlighter
                      pdfDocument={pdfDocument}
                      enableAreaSelection={event => event.altKey}
                      onScrollChange={resetHash}
                      scrollRef={scrollTo => {
                        this.scrollViewerTo = scrollTo;

                        this.scrollToHighlightFromHash();
                      }}
                      onSelectionFinished={(
                        position,
                        content,
                        hideTipAndSelection,
                        transformSelection
                      ) => (
                        <Tip
                          onOpen={transformSelection}
                          onConfirm={comment => {
                            this.addHighlight({ content, position, comment });

                            hideTipAndSelection();
                          }}
                        />
                      )}
                      highlightTransform={(
                        highlight,
                        index,
                        setTip,
                        hideTip,
                        viewportToScaled,
                        screenshot,
                        isScrolledTo
                      ) => {
                        const isTextHighlight = !Boolean(
                          highlight.content && highlight.content.image
                        );

                        const component = isTextHighlight ? (
                          <Highlight
                            isScrolledTo={isScrolledTo}
                            position={highlight.position}
                            comment={highlight.comment}
                          />
                        ) : (
                          <AreaHighlight
                            highlight={highlight}
                            onChange={boundingRect => {
                              this.updateHighlight(
                                highlight.id,
                                {
                                  boundingRect: viewportToScaled(boundingRect)
                                },
                                { image: screenshot(boundingRect) }
                              );
                            }}
                          />
                        );

                        return (
                          <Popup
                            popupContent={<HighlightPopup {...highlight} />}
                            onMouseOver={popupContent =>
                              setTip(highlight, highlight => popupContent)
                            }
                            onMouseOut={hideTip}
                            key={index}
                            children={component}
                          />
                        );
                      }}
                      highlights={highlights}
                    />
                  )}
                </PdfLoader>
              )}
            </Col>
          </Row>
        </div>
      </div>
    );
  }
}

export default CaseFiles;
