import React, { PureComponent } from "react";
import "./SearchBar.css";
import "./tooltip-css.css";
import ForceGraph2D from 'react-force-graph-2d';

export default class SearchBar2 extends PureComponent {
  constructor(props) {
    super(props);
    this.state = { tagname: '' , results: '', nodeData:{
      "nodes": [],
      "links": []
  }};
  }

  myData = {
    "nodes": [ ],
    "links": []
}

myChangeHandler = (event) => {
  this.setState({tagname: event.target.value, nodeData:this.state.nodeData});
}

handleNodeClick = (event) => {
  //event.preventDefault();
  console.log(event);

  //return event.name;

}

  handleClick = (event) => {
    event.preventDefault();
    fetch('https://0bf8a9e6.ngrok.io/webhook', {
		method: 'POST',
		body: JSON.stringify({
                       'queryResult': {'intent': {'displayName':'RetrieveUIData'}, 'parameters': {'tag': this.state.tagname}}
		}),
		headers: {
			"Content-type": "application/json; charset=UTF-8",
                        "Access-Control-Allow-Origin": "*"
		},
		}).then(response => {
      setTimeout(() => null, 0);
      return response.json();
  })
  .then((response) => {
                          var keys = Object.keys(response)
                          var tagname = keys[0]
                          var innerKeys = Object.keys(response[tagname])
                          var person = {}
                          var tagNode = {
                            "id": '0',
                            "name":"tag Name:" + tagname,
                            "val": 3,
                            "group":1,
                            "color":'blue'
                          }
                          var count = 1
                          var nodesArray = [tagNode]
                          var links = []
                          console.log(response)
                          for (var i = 0; i < innerKeys.length; i++) {
                            var parentNodeName = innerKeys[i]
                            nodesArray.push({
                            "id": String(count),
                            "name": "File Name:"+parentNodeName,
                            "val": 3,
                            "group":2,
                            "color": 'red'
                            })
                            links.push({
                                "source": String(0),
                                "target": String(count)
                            })
                            var parentNode = count
                            count =count +1
                            if(response[tagname][parentNodeName]["names"] != null){
                              for (var j=0; j<response[tagname][parentNodeName]["names"].length;j++){
                                var contactName = response[tagname][parentNodeName]["names"][j]
                                if (person[contactName] != null){
                                  links.push({
                                      "source": String(parentNode),
                                      "target": person[contactName]
                                  })
                                }else{
                                  nodesArray.push({
                                  "id": String(count),
                                  "name": "Contact Name:" + contactName,
                                  "val": 3,
                                  "group":3,
                                  "color": 'purple'})
                                  links.push({
                                      "source": String(parentNode),
                                      "target": String(count)
                                  })
                                  person[contactName] = String(count)
                                  count = count + 1

                                }

                              }
                          }
                          }
                          console.log(nodesArray)
                          console.log(links)
                          this.state.nodeData.nodes = nodesArray
                          this.state.nodeData.links = links
                          this.state.style = {display:'block'}
                          this.myData = this.state.nodeData
                          this.setState({tagname: this.state.tagname, nodeData:{"nodes":nodesArray, "links":links},
                          style:{display:'block'} });
    }).catch(function (error) {
                    console.log(error);
                  })

  }

    render(){
      return(
        <div>
          <form onSubmit={this.handleClick} align="center">
          <input type='text' placeholder="Enter the tag name..."
            onChange={this.myChangeHandler} style={{width: '261px', height: '30px',
            fontSize: 'large', boxSizing: 'content-box', border: '1px solid', borderRadius: '12px', paddingLeft: '10px'}}
          />
          <input
            type='submit' style={{width: '100px', height: '30px', backgroundColor:"#4CAF50",
            color:"white",
            textAlign:"center",
            display:"inline-block", border: '1px solid', borderRadius: '12px', fontSize: 'large', boxSizing: 'content-box',}}/>
          
          </form>
          <div id="graph" align="center">
              <ForceGraph2D
                graphData={this.myData}
                nodeAutoColorBy="group"
                width={700} height={500} linkWidth={3} linkColor={'black'}
                nodeCanvasObject={(node, ctx, globalScale) => {
                  const label = node.name;
                  const fontSize = 12/globalScale;
                  ctx.font = `${fontSize}px Sans-Serif`;
                  const textWidth = ctx.measureText(label).width;
                  const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); // some padding

                  ctx.fillStyle = 'rgba(231, 241, 217, 0)';
                  ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);

                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillStyle = node.color;
                  ctx.fillText(label, node.x, node.y);
                }}
              /></div>
      </div>
      );
    }
}
