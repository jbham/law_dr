import React, { Component } from "react";
import Joi from "joi-browser";
import { CButton } from "@coreui/react";

class FormClass extends Component {
  state = { data: {}, errors: {} };

  validateProperty = ({ name, value }) => {
    const obj = { [name]: value };
    const schema = { [name]: this.schema[name] };
    const { error } = Joi.validate(obj, schema);
    return error ? error.details[0].message : null;

    // if (name === "username") {
    //   if (value.trim() === "") return "Username is required";
    // }
    // if (name === "password") {
    //   if (value.trim() === "") return "Password is required";
    // }
  };

  validate = () => {
    const options = {
      abortEarly: false,
    };
    console.log(this.state.data);
    console.log(this.schema);
    const result = Joi.validate(this.state.data, this.schema, options);
    console.log(result);
    if (!result.error) return null;

    const errors = {};
    for (let item of result.error.details) errors[item.path[0]] = item.message;
    return errors;

    // const errors = {};

    // const { data } = this.state;

    // if (data.username.trim() === "")
    //   errors.username = "Username is required.";
    // if (data.password.trim() === "")
    //   errors.password = "Password is required.";

    // return Object.keys(errors).length === 0 ? null : errors;
  };

  handleSubmit = (e) => {
    console.log("handling submitt");
    e.preventDefault();

    const errors = this.validate();
    console.log(errors);
    this.setState({ errors: errors || {} });
    if (errors) return;
    console.log(errors);

    this.doSubmit();
  };

  // currentTarget is property of "e"
  // e is an object being passed to this function from render method
  handleChange = ({ currentTarget: input }) => {
    const errors = { ...this.state.errors };
    const errorMessage = this.validateProperty(input);
    if (errorMessage) errors[input.name] = errorMessage;
    else delete errors[input.name];
    const data = { ...this.state.data };
    data[input.name] = input.type === "checkbox" ? input.checked : input.value;

    // added callback to setstate
    // based on https://stackoverflow.com/questions/39655205/reactjs-setstate-not-working-on-first-toggle-of-checkbox
    this.setState({ data, errors }, function afterStateChange() {
      this.useNewState();
    });
    console.log(this.state.data);
  };

  useNewState() {}

  renderButton = (
    label,
    classname,
    color,
    active = true,
    tabIndex,
    disabled
  ) => {
    return (
      <CButton
        disabled={label === "Login" ? (this.validate() ? true : false) : false}
        color={color}
        className={classname}
        active={active}
        tabIndex={tabIndex}
      >
        {label}
      </CButton>
    );
  };
}

export default FormClass;
