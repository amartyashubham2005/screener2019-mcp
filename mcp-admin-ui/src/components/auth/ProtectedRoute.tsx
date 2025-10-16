import { Navigate, Outlet } from "react-router";
import { useAuth } from "../../context/AuthContext";

export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  // Show a loading indicator while checking for authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div>Loading...</div>
      </div>
    );
  }

  // If authenticated, render the child routes. Otherwise, redirect to sign-in.
  return isAuthenticated ? <Outlet /> : <Navigate to="/signin" replace />;
}