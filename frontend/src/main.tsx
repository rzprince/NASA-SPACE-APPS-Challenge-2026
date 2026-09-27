import React, { Component, type ErrorInfo, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import "maplibre-gl/dist/maplibre-gl.css";
import App from "./App";
import "./app.css";

type BoundaryState = { failed: boolean };

class DemoErrorBoundary extends Component<{ children: ReactNode }, BoundaryState> {
  state: BoundaryState = { failed: false };

  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("BoponX interface error", error, info);
  }

  render() {
    if (this.state.failed) {
      return (
        <main className="app-recovery">
          <div className="app-recovery-card">
            <span className="app-recovery-mark">BoponX</span>
            <h1>The interface needs a quick refresh.</h1>
            <p>Your farm information was not stored. Reload the page and continue from the field location.</p>
            <button type="button" onClick={() => window.location.reload()}>Reload BoponX</button>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}

const root = document.getElementById("root");
if (!root) throw new Error("BoponX root element is missing");

createRoot(root).render(
  <React.StrictMode>
    <DemoErrorBoundary>
      <App />
    </DemoErrorBoundary>
  </React.StrictMode>,
);
