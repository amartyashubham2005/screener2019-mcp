import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router";
import SignIn from "./pages/AuthPages/SignIn";
import SignUp from "./pages/AuthPages/SignUp";
import NotFound from "./pages/OtherPage/NotFound";
import UserProfiles from "./pages/UserProfiles";
import AppLayout from "./layout/AppLayout";
import { ScrollToTop } from "./components/common/ScrollToTop";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import Sources from "./pages/Sources";
import McpServers from "./pages/McpServers";
import Logs from "./pages/Logs";

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <ScrollToTop />
        <Toaster position="top-right" />
        <Routes>
          {/* Redirect root path to /signin */}
          <Route path="/" element={<Navigate to="/signin" />} />


          {/* Auth Layout */}
          <Route path="/signin" element={<SignIn />} />
          <Route path="/signup" element={<SignUp />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            {/* Dashboard Layout */}
            <Route element={<AppLayout />}>
              <Route path="/sources" element={<Sources />} />
              <Route path="/mcp-servers" element={<McpServers />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/profile" element={<UserProfiles />} />
            </Route>
          </Route>


          {/* Fallback Route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
