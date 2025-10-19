import { useEffect, useState, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { toast } from "react-hot-toast";
import { useAuth } from "../../context/AuthContext";
import PageMeta from "../../components/common/PageMeta";

export default function AzureCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const hasRun = useRef(false);

  useEffect(() => {
    // Prevent double execution in React StrictMode (development)
    if (hasRun.current) {
      return;
    }
    hasRun.current = true;

    const handleCallback = async () => {
      try {
        // Get the authorization code and state from URL query params
        const code = searchParams.get("code");
        const state = searchParams.get("state");
        const error = searchParams.get("error");
        const errorDescription = searchParams.get("error_description");

        // Check for OAuth errors
        if (error) {
          console.error("Azure AD error:", error, errorDescription);
          setErrorMessage(errorDescription || error);
          setStatus("error");
          toast.error(`Azure AD error: ${errorDescription || error}`);
          setTimeout(() => navigate("/signin"), 3000);
          return;
        }

        // Validate required parameters
        if (!code || !state) {
          console.error("Missing code or state parameter");
          setErrorMessage("Invalid callback parameters");
          setStatus("error");
          toast.error("Invalid callback from Azure AD");
          setTimeout(() => navigate("/signin"), 3000);
          return;
        }

        // Validate state from sessionStorage (CSRF protection)
        const storedState = sessionStorage.getItem('azure_oauth_state');
        console.log('[Azure SSO] State validation:', {
          storedState,
          receivedState: state,
          match: storedState === state
        });

        if (!storedState || storedState !== state) {
          console.error("State validation failed", {
            storedState,
            receivedState: state
          });
          setErrorMessage("Invalid state parameter - possible CSRF attack");
          setStatus("error");
          toast.error("Security validation failed");
          setTimeout(() => navigate("/signin"), 3000);
          return;
        }

        console.log('[Azure SSO] State validation successful');
        // Clear the stored state after successful validation
        sessionStorage.removeItem('azure_oauth_state');

        // The backend /api/v1/auth/azure/callback endpoint handles:
        // 1. Validating the state (CSRF protection)
        // 2. Exchanging the code for an access token
        // 3. Getting user info from Microsoft Graph
        // 4. Creating/updating the user in the database
        // 5. Setting the JWT cookie

        // We need to call the backend callback endpoint with these params
        const callbackUrl = `${import.meta.env.VITE_API_BASE_URL}/api/v1/auth/azure/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`;

        const response = await fetch(callbackUrl, {
          method: "GET",
          credentials: "include", // Important: include cookies
        });

        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.detail || "Authentication failed");
        }

        const data = await response.json();

        if (data.user) {
          // Login successful
          setStatus("success");
          toast.success("Successfully signed in with Microsoft!");
          login(data.user);

          // Redirect to dashboard
          setTimeout(() => navigate("/sources"), 1000);
        } else {
          throw new Error("No user data received");
        }
      } catch (error: any) {
        console.error("Error handling Azure callback:", error);
        setErrorMessage(error.message || "An unexpected error occurred");
        setStatus("error");
        toast.error(error.message || "Failed to complete sign in");
        setTimeout(() => navigate("/signin"), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, login]);

  return (
    <>
      <PageMeta
        title="Azure AD Sign In | MCP Admin UI"
        description="Completing Azure AD authentication"
      />
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="w-full max-w-md p-8 text-center">
          {status === "loading" && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="w-16 h-16 border-4 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                Completing sign in...
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Please wait while we verify your credentials
              </p>
            </div>
          )}

          {status === "success" && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <svg
                  className="w-16 h-16 text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                Sign in successful!
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Redirecting you to the dashboard...
              </p>
            </div>
          )}

          {status === "error" && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <svg
                  className="w-16 h-16 text-red-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                Authentication failed
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {errorMessage || "An error occurred during sign in"}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                Redirecting you back to sign in page...
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
