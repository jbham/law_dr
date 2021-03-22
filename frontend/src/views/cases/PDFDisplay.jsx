import React, { Component } from "react";
/* eslint import/no-webpack-loader-syntax: 0 */
import PDFWorker from "worker-loader!pdfjs-dist/lib/pdf.worker";
import {
  PdfLoader,
  PdfHighlighter,
  Tip,
  Highlight,
  Popup,
  AreaHighlight,
  setPdfWorker,
  // } from "react-pdf-highlighter";
} from "../../components/pdfHighlighter/core";

import Spinner from "../../components/pdfHighlighter/Spinner";

// import {
//   PdfLoader,
//   PdfHighlighter,
//   Tip,
//   Highlight,
//   Popup,
//   AreaHighlight,
//   setPdfWorker,
// } from "react-pdf-highlighter";

import type {
  T_Highlight,
  T_NewHighlight,
} from "../../components/pdfHighlighter/types";

setPdfWorker(PDFWorker);

const resetHash = () => {
  window.location.hash = "jaspal";
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
  return Number(window.location.hash.slice("#highlight-".length));
};

const getNextId = () => String(Math.random()).slice(2);

const updateHash = (highlight) => {
  document.location.hash = `highlight-${highlight.id}`;
};

class PDFDisplay extends Component {
  constructor(props) {
    super(props);
    console.log("Props from PDFDisplay", props);
    this.state = {
      pdfDoc: props.pdfDoc,
      highlights: props.highlights,
    };
  }

  componentDidMount() {
    window.addEventListener(
      "hashchange",
      this.scrollToHighlightFromHash,
      false
    );
  }

  componentDidUpdate(prevProps) {
    if (prevProps.highlights !== this.props.highlights) {
      this.setState({ highlights: this.props.highlights });
    }

    if (prevProps.pdfDoc !== this.props.pdfDoc) {
      this.setState({ pdfDoc: this.props.pdfDoc });
    }
  }

  scrollToHighlightFromHash = () => {
    const highlight = this.getHighlightById(parseIdFromHash());

    if (highlight) {
      this.scrollViewerTo(highlight);
    }
  };

  getHighlightById(id: string) {
    const { highlights } = this.state;

    return highlights.find((highlight) => highlight.id === id);
  }

  addHighlight(highlight: T_NewHighlight) {
    const { highlights } = this.state;

    console.log("Saving highlight", highlight);

    this.setState({
      highlights: [{ ...highlight, id: getNextId() }, ...highlights],
    });
  }

  updateHighlight(highlightId: string, position: Object, content: Object) {
    console.log("Updating highlight", highlightId, position, content);

    this.setState({
      highlights: this.state.highlights.map((h) => {
        return h.id === highlightId
          ? {
              ...h,
              position: { ...h.position, ...position },
              content: { ...h.content, ...content },
            }
          : h;
      }),
    });
  }

  scrollViewerTo = (highlight: any) => {};
  render() {
    const { pdfDoc, highlights } = this.state;
    return (
      <div // style={{
        //   height: "50vw",
        //   width: "60%",
        //   // overflowY: "hidden",
        //   position: "relative",
        //   // overflow: "auto",
        //   border: "1px solid #d8dbe0",
        //   padding: "10px 10px 10px 10px",
        // }}
        style={{
          //   height: "47vw",
          //   overflowY: "hidden",
          position: "sticky",
          //   overflowX: "hidden",
          border: "1px solid #d8dbe0",
          //   padding: "10px 10px 10px 10px",
          width: "50%",
        }}
        // style={{
        //   height: "100vh",
        //   width: "75vw",
        //   position: "relative",
        // }}
      >
        <PdfLoader url={pdfDoc} beforeLoad={<Spinner />}>
          {(pdfDocument) => (
            <PdfHighlighter
              pdfDocument={pdfDocument}
              enableAreaSelection={(event) => event.altKey}
              onScrollChange={resetHash}
              // pdfScaleValue="page-width"
              scrollRef={(scrollTo) => {
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
                  onConfirm={(comment) => {
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
                    onChange={(boundingRect) => {
                      this.updateHighlight(
                        highlight.id,
                        { boundingRect: viewportToScaled(boundingRect) },
                        { image: screenshot(boundingRect) }
                      );
                    }}
                  />
                );

                return (
                  <Popup
                    popupContent={<HighlightPopup {...highlight} />}
                    onMouseOver={(popupContent) =>
                      setTip(highlight, (highlight) => popupContent)
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
      </div>
    );
  }
}

export default PDFDisplay;
