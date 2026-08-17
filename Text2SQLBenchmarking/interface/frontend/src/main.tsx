import ReactDOM from "react-dom";
import App from "./App";
import { AppProvider } from "./state/AppContext";
import "./styles/tokens.css";
import "./styles/global.css";

ReactDOM.render(
  <AppProvider><App /></AppProvider>,
  document.getElementById("root")
);
