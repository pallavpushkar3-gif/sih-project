import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import { AppProviders } from "./app/providers";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";
import "@fontsource/inter/latin-600.css";
import "./shared/styles/globals.css";

createRoot(document.getElementById("root")!).render(<StrictMode><AppProviders><App /></AppProviders></StrictMode>);
