import React, { Component } from "react";
import PropTypes from "prop-types";
import { CCard, CCardBody, CCardFooter } from "@coreui/react";
import classNames from "classnames";
import { mapToCssModules } from "reactstrap/lib/utils";
import { Link } from "react-router-dom";

const propTypes = {
  header: PropTypes.string,
  mainText: PropTypes.string,
  icon: PropTypes.string,
  color: PropTypes.string,
  variant: PropTypes.string,
  footer: PropTypes.bool,
  link: PropTypes.string,
  children: PropTypes.node,
  className: PropTypes.string,
  cssModule: PropTypes.object,
};

const defaultProps = {
  header: "$1,999.50",
  mainText: "Income",
  icon: "fa fa-cogs",
  color: "primary",
  variant: "0",
  link: "#",
};

class CaseComponent extends Component {
  render() {
    const {
      className,
      cssModule,
      header,
      mainText,
      icon,
      color,
      footer,
      link,
      children,
      variant,
      ...attributes
    } = this.props;

    // demo purposes only
    const padding =
      variant === "0"
        ? { card: "p-3", icon: "p-3", lead: "mt-2" }
        : variant === "1"
        ? {
            card: "p-0",
            icon: "p-4",
            lead: "pt-3",
          }
        : { card: "p-0", icon: "p-4 px-5", lead: "pt-3" };

    const card = { style: "clearfix", color: color, icon: icon, classes: "" };
    card.classes = mapToCssModules(
      classNames(className, card.style, padding.card),
      cssModule
    );

    const lead = { style: "h5 mb-0", color: color, classes: "" };
    lead.classes = classNames(lead.style, "text-" + card.color, padding.lead);

    const blockIcon = function (icon) {
      const classes = classNames(
        icon,
        "bg-" + card.color,
        padding.icon,
        "font-2xl mr-3 float-left"
      );
      return <i className={classes} />;
    };

    const cardFooter = function () {
      if (footer) {
        return (
          <CCardFooter className="px-3 py-2">
            <Link
              to={link}
              className="font-weight-bold font-xs btn-block text-muted"
            >
              View more
              <i className="fa fa-angle-right float-right font-lg" />
            </Link>
          </CCardFooter>
        );
      }
    };

    return (
      <CCard>
        <CCardBody className={card.classes} {...attributes}>
          {blockIcon(card.icon)}
          <div className={lead.classes}>{header}</div>
          <div className="text-muted text-uppercase font-weight-bold font-xs">
            {mainText}
          </div>
        </CCardBody>
        {cardFooter()}
      </CCard>
    );
  }
}

CaseComponent.propTypes = propTypes;
CaseComponent.defaultProps = defaultProps;

export default CaseComponent;
