import { BrowserRouter, Route, Routes } from "react-router-dom";
import { VanguardProvider } from "./lib/store.js";
import Admin from "./pages/Admin.jsx";
import Compliance from "./pages/Compliance.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Forensics from "./pages/Forensics.jsx";
import Login from "./pages/Login.jsx";

function App() {
  return (
    <VanguardProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/forensics" element={<Forensics />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </BrowserRouter>
    </VanguardProvider>
  );
}

export default App;
