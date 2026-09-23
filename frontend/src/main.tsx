import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
import "./showcase.css";

const root = document.getElementById("root");
if (!root) throw new Error("BoponX root element is missing");
createRoot(root).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
