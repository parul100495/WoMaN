import React, { PureComponent } from "react";
import Header from "./Header";
import filterEmoji from "./filterEmoji";
import SearchBar2 from "./searchBar2";
import "./AppCss.css";
export default class App extends PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      filteredEmoji: filterEmoji("", 20)
    };
  }

  handleSearchChange = event => {
    this.setState({
      filteredEmoji: filterEmoji(event.target.value, 20)
    });
  };

  render() {
    return (
      <div style={{borderStyle: 'solid',
        borderColor: 'black',
        margin: '0px',
        padding: '0px'
      }}>
      <div className="topnav" style={{backgroundColor: '#E7F1D9'}}>
        <Header />
      </div>
      <hr
        style={{
            color: 'black',
            backgroundColor: 'black',
            height: 5
        }}
    />
      <div>
         <table width="100%" height="100%" align="center" margin="0">
           <tbody>
          <tr>
         <td valign="top" width="60%"><SearchBar2 /></td>
         <td width="40%" valign="bottom"><iframe title="myFrame"
                  allow="microphone;"
                  width="100%"
                  height="540"
                  float="right"
                  align="right"
                  src="https://console.dialogflow.com/api-client/demo/embedded/b85859d1-c8ff-402a-9e03-3fb9b8cf82c8">
          </iframe></td>
          </tr>
          </tbody>
         </table>
      </div>
      </div>
    );
  }
}
