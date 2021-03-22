import React, { useState } from "react";
import { useSelector, useDispatch } from "react-redux";

import {
  CCreateElement,
  CSidebar,
  CSidebarBrand,
  CSidebarNav,
  CSidebarNavDivider,
  CSidebarNavTitle,
  CSidebarMinimizer,
  CSidebarNavDropdown,
  CSidebarNavItem,
} from "@coreui/react";

import CIcon from "@coreui/icons-react";

// sidebar nav config
import navigation from "./_nav";
import { set } from "../store/sidebar";

const TheSidebar = () => {
  const dispatch = useDispatch();
  const show = useSelector((state) => state.sidebar.sidebarShow);
  console.log("selectorrrr", typeof show, show);

  const [minimize, setMinimize] = useState(
    localStorage.getItem("sidebarMinize")
      ? localStorage.getItem("sidebarMinize") === "true"
        ? true
        : false
      : false
  );

  const storeMinimizedValues = () => {
    if (localStorage.getItem("sidebarMinize") === null) {
      localStorage.setItem("sidebarMinize", !minimize);
    } else {
      let val = localStorage.getItem("sidebarMinize") === "true";
      setMinimize(!val);
      localStorage.setItem("sidebarMinize", !val);
    }
  };

  const somefunc = (val) => {
    // dispatch({ type: "set", sidebarShow: val });
    dispatch(set({ sidebarShow: val }));
  };

  return (
    <CSidebar
      show={show}
      minimize={minimize}
      onMinimizeChange={storeMinimizedValues}
      onShowChange={somefunc}
    >
      <CSidebarBrand className="d-md-down-none" to="/">
        <CIcon
          className="c-sidebar-brand-full"
          name="logo-negative"
          height={35}
        />
        <CIcon
          className="c-sidebar-brand-minimized"
          name="sygnet"
          height={35}
        />
      </CSidebarBrand>
      <CSidebarNav>
        <CCreateElement
          items={navigation}
          components={{
            CSidebarNavDivider,
            CSidebarNavDropdown,
            CSidebarNavItem,
            CSidebarNavTitle,
          }}
        />
      </CSidebarNav>
      <CSidebarMinimizer className="c-d-md-down-none" />
    </CSidebar>
  );
};

export default React.memo(TheSidebar);
