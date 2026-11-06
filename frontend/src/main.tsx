import { Component, type ErrorInfo, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import "maplibre-gl/dist/maplibre-gl.css";
import App from "./App";
import "./app.css";

type BoundaryState = { failed: boolean; errorMessage: string };

class DemoErrorBoundary extends Component<{ children: ReactNode }, BoundaryState> {
  state: BoundaryState = { failed: false, errorMessage: "" };

  static getDerivedStateFromError(error: Error): BoundaryState {
    return {
      failed: true,
      errorMessage: error instanceof Error ? error.message : String(error ?? "Unknown error"),
    };
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
            {this.state.errorMessage && (
              <p style={{ fontFamily: "var(--mono)", fontSize: "11px", color: "#9eb2a8", marginTop: "8px" }}>
                Diagnostic: {this.state.errorMessage}
              </p>
            )}
            <div style={{ display: "flex", gap: "10px", marginTop: "14px" }}>
              <button
                type="button"
                onClick={() => this.setState({ failed: false, errorMessage: "" })}
              >
                Continue BoponX
              </button>
              <button
                type="button"
                onClick={() => window.location.reload()}
                style={{ background: "transparent", color: "#eef5f1", border: "1px solid rgba(255,255,255,0.24)" }}
              >
                Reload Page
              </button>
            </div>
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
  <DemoErrorBoundary>
    <App />
  </DemoErrorBoundary>,
);
