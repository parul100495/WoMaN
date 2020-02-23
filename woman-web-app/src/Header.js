import React, { PureComponent } from "react";
import "./Header.css";

export default class Header extends PureComponent {
  render() {
    return (
      <header className="component-header">
        <img
          src= {require('./woman.png')}
          height='100' 
          alt="WoMan"
        />
        
      </header>
    );
  }
}
