import React, { useEffect, useState, useRef, useCallback } from "react";
import { useSelector, useDispatch } from "react-redux";
import {
  loadAllVisitDates,
  setTimelineBar,
  hideShowMentions,
  getRelationsByID,
  handleShowRelations,
  visitDatesRequested,
  clearPdfDoc,
} from "../../store/caseAnalysis";
import HorizontalTimeline from "../../components/horizontalTimeline/Components/HorizontalTimeline";
import {
  CCard,
  CCardBody,
  CSpinner,
  CListGroup,
  CListGroupItem,
  CCollapse,
  CLink,
  CFade,
} from "@coreui/react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faHandPointRight,
  faChevronRight,
  faCheckCircle,
} from "@fortawesome/free-solid-svg-icons";
import AWS from "aws-sdk";

import PDFDisplay from "./PDFDisplay";

const styles = {
  arrowExpanded: {
    "webkit-transform": "rotate(90deg)",
    transform: "rotate(90deg)",
  },
};

const initialHighLights = [
  {
    content: {
      text: " Type Checking for JavaScript",
    },
    position: {
      boundingRect: {
        x1: 255.73419189453125,
        y1: 139.140625,
        x2: 574.372314453125,
        y2: 165.140625,
        width: 809.9999999999999,
        height: 1200,
      },
      rects: [
        {
          x1: 255.73419189453125,
          y1: 139.140625,
          x2: 574.372314453125,
          y2: 165.140625,
          width: 809.9999999999999,
          height: 1200,
        },
      ],
      pageNumber: 1,
    },
    comment: {
      text: "Flow or TypeScript?",
      emoji: "🔥",
    },
    id: "8245652131754351",
  },
];
export const RelatedMentions = ({ idList, takeMeToPDF }) => {
  const NumOfTodosWithIsDoneValue = useSelector((state) =>
    getRelationsByID(state, idList)
  );

  return (
    <CFade>
      {NumOfTodosWithIsDoneValue.map((f, i) => (
        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "20px minmax(120px, 1.9fr) minmax(70px, 1.4fr) minmax(90px, 1fr) minmax(90px, 1fr) minmax(90px, 1fr) minmax(170px, 1.36fr) minmax(70px, 0.36fr) minmax(70px, 0.36fr)30px",
            gridGap: 0,
            borderTop: "none",
            borderLeft: "1px solid #dcdfe3",
            borderRight: "1px solid #dcdfe3",
            borderBottom: "0.5px solid #dcdfe3",
            backgroundColor: "#f0f2f5",
          }}
        >
          <span style={{ padding: "9.5px" }}>
            <FontAwesomeIcon
              icon={faHandPointRight}
              color="#7b848f"
              // size="2x"
              // style={{ marginRight: "10px" }}
            />
          </span>

          <span
            style={{
              padding: "9.5px",
              paddingLeft: "22px",
            }}
          >
            <CLink onClick={() => takeMeToPDF(f)}>{f["text"]}</CLink>
          </span>
          <span
            style={{
              padding: "9.5px",
              paddingLeft: "7px",
            }}
          >
            <small>{f["annotation_type"]}</small>
          </span>
          <span
            style={{
              padding: "9.5px",
              paddingLeft: "7px",
            }}
          >
            {f["body_side"]}
          </span>
          <span
            style={{
              padding: "9.5px",
              paddingLeft: "7px",
            }}
          >
            {f["body_region"].map((b, bi) => (
              <span>{b}</span>
            ))}
          </span>
          <span
            style={{
              padding: "9.5px",
              paddingLeft: "7px",
            }}
          >
            {f["polarity"] === 1 ? "Yes" : "No"}
          </span>
          <span
            style={{
              padding: "9.5px",
              paddingLeft: "7px",
            }}
          >
            {""}
          </span>

          <span style={{ padding: "9.5px" }}></span>
        </div>
      ))}
    </CFade>
  );
};

const getWindowDimensions = () => {
  const { innerWidth: width, innerHeight: height } = window;
  let newHeightForFull = `${Math.round(
    100 - ((978 - (height - 170)) / 978) * 100
  )}vh`;
  let newHeightForDiv1 = `${Math.round(
    100 - ((978 - (height - 190)) / 978) * 100
  )}vh`;

  return {
    full: { overflow: "hidden", height: newHeightForFull },
    div1: { overflow: "hidden", height: newHeightForDiv1 },
  };
};

const VisitDates = (props) => {
  const dispatch = useDispatch();
  const {
    visitDates,
    loading,
    timelineBar,
    dataForSelectedVisitDate,
    showMentions,
    showRelations,
    lastSearchedTerm,
    lastFetchedData,
  } = useSelector((state) => state.caseAnalysis);

  const { policyData } = useSelector(
    (state) => state.caseAnalysis.everythingPDF
  );

  const [pdfDoc, setPdfDoc] = useState(null);
  const [highlights, setHighlights] = useState([]);

  const [windowDimensions, setWindowDimensions] = useState(
    getWindowDimensions()
  );

  const updateHash = (highlight) => {
    if (highlight) {
      window.location.hash = `highlight-${highlight.id}`;
    }
  };

  useEffect(() => {
    function handleResize() {
      setWindowDimensions(getWindowDimensions());
    }

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    updateHash(highlights[0]);
    // setTimeout(() => {
    //   updateHash(highlights[0]);
    // }, 500);
  }, [highlights]);

  useEffect(() => {
    dispatch(loadAllVisitDates(null, null, null, null));
  }, []);

  useEffect(() => {
    const getPDF = async (data) => {
      let loc = data["loc"];
      let bucket = data["bucket"];
      let AccessKeyId = data["response"]["AccessKeyId"];
      let SecretAccessKey = data["response"]["SecretAccessKey"];
      let SessionToken = data["response"]["SessionToken"];
      let region = data["response"]["region"];

      AWS.config.update({
        region: region, //"us-west-2",
        accessKeyId: AccessKeyId,
        secretAccessKey: SecretAccessKey,
        sessionToken: SessionToken,
      });

      var s3 = new AWS.S3();

      const param = {
        Bucket: bucket,
        Key: loc,
      };

      try {
        const response = await s3.getObject(param).promise();
        console.log(response);

        // dispatch(pdfFetched(response.Body));
        setPdfDoc(response.Body);
      } catch (err) {
        console.error(err);
      }
    };
    if (JSON.stringify(policyData) !== "{}") {
      getPDF(policyData);
    }
  }, [policyData]);

  const indexClickedUpdateState = (index) => {
    let newtimelineBar = { ...timelineBar };
    newtimelineBar.previous = timelineBar.value;
    newtimelineBar.value = index;

    // dispatch to fetch records for the clicked timeline
    dispatch(
      loadAllVisitDates(
        newtimelineBar,
        lastSearchedTerm,
        lastFetchedData[index]["file_id"],
        lastFetchedData[index]["file_state_id"]
      )
    );
  };

  const handleShowHideMentions = (keyName) => {
    let newshowMentions = { ...showMentions };
    newshowMentions[keyName] = !showMentions[keyName];
    dispatch(hideShowMentions(newshowMentions));
  };

  const showHideRelations = (id) => {
    let newShowRelations = { ...showRelations };
    newShowRelations[id] = !showRelations[id];
    dispatch(handleShowRelations(newShowRelations));
  };

  const takeMeToPDF = (f) => {
    console.log(f);
    //calculate coordinates:
    let cords = [];
    let pno = 0;
    cords = eval(f["full_text_bbox"]);
    pno = f["page_number"] + 1;

    let contentText = {};
    contentText["text"] = "text";

    let boundingRect = {};
    boundingRect["x1"] = cords[0] * 1.33;
    boundingRect["y1"] = cords[1] * 1.33;
    boundingRect["x2"] = cords[2] * 1.33;
    boundingRect["y2"] = cords[3] * 1.33;
    boundingRect["width"] = cords[4] * 1.33;
    boundingRect["height"] = cords[5] * 1.33;

    let rectsObj = {};

    rectsObj["x1"] = cords[0] * 1.33;
    rectsObj["y1"] = cords[1] * 1.33;
    rectsObj["x2"] = cords[2] * 1.33;
    rectsObj["y2"] = cords[3] * 1.33;
    rectsObj["width"] = cords[4] * 1.33;
    rectsObj["height"] = cords[5] * 1.33;

    let rects = [];
    rects.push(rectsObj);

    let positionObj = {};
    positionObj["boundingRect"] = boundingRect;
    positionObj["rects"] = rects;
    positionObj["pageNumber"] = pno;

    let commentObj = {};
    commentObj["text"] = "";
    commentObj["emoji"] = "";

    let mainObj = {};
    mainObj["content"] = contentText;
    mainObj["position"] = positionObj;
    mainObj["comment"] = commentObj;
    mainObj["id"] = f["id"];

    setHighlights([mainObj]);

    // setTimeout(() => {
    //   updateHash(highlights[0]);
    // }, 500);

    // setTimeout(() => {
    //   this.scrollToMyRef();
    // }, 100);
  };

  return (
    <div>
      <CCard>
        <CCardBody>
          {visitDates.length > 0 && (
            <div style={{ paddingBottom: "20px", color: "#7b848f" }}>
              <FontAwesomeIcon
                icon={faCheckCircle}
                color="#068f63"
                // size="2x"
                style={{ marginRight: "10px" }}
              />
              {visitDates.length} Visit dates located{" "}
              {lastSearchedTerm && `for "${lastSearchedTerm}"`}
            </div>
          )}
          <div
            style={{
              width: "99%",
              height: "100px",
              margin: "0 auto",
              // paddingTop: "25px",
            }}
          >
            {visitDates.length > 0 && (
              <HorizontalTimeline
                fillingMotion={{
                  stiffness: timelineBar.fillingMotionStiffness,
                  damping: timelineBar.fillingMotionDamping,
                }}
                index={timelineBar.value}
                indexClick={(index) => indexClickedUpdateState(index)}
                isKeyboardEnabled={timelineBar.isKeyboardEnabled}
                isTouchEnabled={timelineBar.isTouchEnabled}
                labelWidth={timelineBar.labelWidth}
                linePadding={timelineBar.linePadding}
                maxEventPadding={timelineBar.maxEventPadding}
                minEventPadding={timelineBar.minEventPadding}
                slidingMotion={{
                  stiffness: timelineBar.slidingMotionStiffness,
                  damping: timelineBar.slidingMotionDamping,
                }}
                styles={{
                  background: timelineBar.stylesBackground,
                  foreground: timelineBar.stylesForeground,
                  outline: timelineBar.stylesOutline,
                }}
                values={visitDates}
                isOpenEnding={timelineBar.isOpenEnding}
                isOpenBeginning={timelineBar.isOpenBeginning}
              />
            )}
          </div>
        </CCardBody>
      </CCard>
      <div
        className="d-flex  flex-row"
        style={windowDimensions.full}
        // style={{ position: "absolute" }}
      >
        <CListGroup
          style={{
            width: "50%",
            paddingRight: "10px",
            overflow: "auto",
          }}
        >
          {dataForSelectedVisitDate &&
            Object.keys(dataForSelectedVisitDate).map((keyName, i) => {
              return (
                <div
                  style={{
                    position: showMentions[keyName] ? "sticky" : "relative",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      width: "100%",
                      flexWrap: "wrap",
                      position: "relative",
                      flexShrink: "0",
                      alignItems: "center",
                      backgroundColor: "#F9F9FB",
                      zIndex: 1,
                    }}
                    onClick={() => handleShowHideMentions(keyName)}
                  >
                    <FontAwesomeIcon
                      icon={faChevronRight}
                      // color="green"
                      rotation={showMentions[keyName] ? 90 : 45}
                      style={{
                        right: "auto",
                        left: "18px",
                        position: "absolute",
                        transition: "-webkit-transform .2s ease-in-out",
                        transition: "transform .2s ease-in-out",
                        transition:
                          "transform .2s ease-in-out, -webkit-transform .2s ease-in-out",
                        zIndex: 2,
                      }}
                    />
                    <CListGroupItem
                      key={keyName}
                      style={{ paddingLeft: "36px", width: "100%" }}
                    >
                      {keyName}
                    </CListGroupItem>
                  </div>
                  <CCollapse
                    show={showMentions[keyName]}
                    style={{
                      overflow: "auto",
                      height: "75vh",
                    }}
                  >
                    <div
                      style={{
                        flex: 1,
                      }}
                    >
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns:
                            "20px minmax(200px, 3.23fr) minmax(90px, 1fr) minmax(90px, 1fr) minmax(90px, 1fr) minmax(170px, 1.36fr) minmax(70px, 0.36fr) 30px",
                          gridGap: 0,
                          border: "1px solid #dcdfe3",
                        }}
                      >
                        <span
                          style={{ padding: "9.5px", color: "#9aa1aa" }}
                        ></span>

                        <span
                          style={{
                            padding: "9.5px",
                            color: "#9aa1aa",
                            paddingLeft: "7px",
                          }}
                        >
                          Term Mentioned
                        </span>
                        <span
                          style={{
                            padding: "9.5px",
                            color: "#9aa1aa",
                            paddingLeft: "7px",
                          }}
                        >
                          Body Side
                        </span>
                        <span
                          style={{
                            padding: "9.5px",
                            color: "#9aa1aa",
                            paddingLeft: "7px",
                          }}
                        >
                          Body Region
                        </span>
                        <span
                          style={{
                            padding: "9.5px",
                            color: "#9aa1aa",
                            paddingLeft: "7px",
                          }}
                        >
                          Negated?
                        </span>
                        <span
                          style={{
                            padding: "9.5px",
                            color: "#9aa1aa",
                            paddingLeft: "7px",
                          }}
                        >
                          Relations
                        </span>
                        <span
                          style={{
                            padding: "9.5px",
                            color: "#9aa1aa",
                            paddingLeft: "7px",
                          }}
                        >
                          Page Number
                        </span>

                        <span
                          style={{ padding: "9.5px", color: "#9aa1aa" }}
                        ></span>
                      </div>

                      {dataForSelectedVisitDate[keyName] &&
                        dataForSelectedVisitDate[keyName].map((f, i) => (
                          <div>
                            <div
                              style={{
                                display: "grid",
                                gridTemplateColumns:
                                  "20px minmax(200px, 3.23fr) minmax(90px, 1fr) minmax(90px, 1fr) minmax(90px, 1fr) minmax(170px, 1.36fr) minmax(70px, 0.36fr) 30px",
                                gridGap: 0,
                                borderLeft: "1px solid #dcdfe3",
                                borderRight: "1px solid #dcdfe3",
                                borderBottom: "1px solid #dcdfe3",
                              }}
                              key={i}
                            >
                              <span style={{ padding: "9.5px" }}></span>

                              <span
                                style={{
                                  padding: "9.5px",
                                  paddingLeft: "7px",
                                }}
                              >
                                <CLink onClick={() => takeMeToPDF(f)}>
                                  {f["text"]}
                                </CLink>
                              </span>
                              <span
                                style={{
                                  padding: "9.5px",
                                  paddingLeft: "7px",
                                }}
                              >
                                {f["body_side"]}
                              </span>
                              <span
                                style={{
                                  padding: "9.5px",
                                  paddingLeft: "7px",
                                }}
                              >
                                {f["body_region"] &&
                                  f["body_region"].map((b, bi) => (
                                    <span>{b}</span>
                                  ))}
                              </span>
                              <span
                                style={{
                                  padding: "9.5px",
                                  paddingLeft: "7px",
                                }}
                              >
                                {f["polarity"] === 1 ? "No" : "Yes"}
                              </span>
                              <span
                                style={{
                                  padding: "9.5px",
                                  paddingLeft: "7px",
                                }}
                              >
                                {f["related_ids"] &&
                                f["related_ids"].length > 0 ? (
                                  <CLink
                                    onClick={() => showHideRelations(f["id"])}
                                  >
                                    {f["related_ids"].length}
                                  </CLink>
                                ) : (
                                  0
                                )}
                              </span>
                              <span
                                style={{
                                  padding: "9.5px",
                                  color: "#9aa1aa",
                                  paddingLeft: "7px",
                                }}
                              >
                                {f["page_number"]}
                              </span>
                              <span style={{ padding: "9.5px" }}></span>
                            </div>

                            {showRelations[f["id"]] && (
                              <RelatedMentions
                                idList={f["related_ids"]}
                                takeMeToPDF={takeMeToPDF}
                              />
                            )}
                          </div>
                        ))}
                    </div>
                  </CCollapse>
                </div>
              );
            })}
        </CListGroup>
        {pdfDoc && <PDFDisplay pdfDoc={pdfDoc} highlights={highlights} />}
      </div>
    </div>
  );
};

export default VisitDates;
