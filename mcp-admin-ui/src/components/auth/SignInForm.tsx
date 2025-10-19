import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { toast } from "react-hot-toast";

import { EyeCloseIcon, EyeIcon } from "../../icons";
import Label from "../form/Label";
import Input from "../form/input/InputField";
import Checkbox from "../form/input/Checkbox";
import Button from "../ui/button/Button";
import { authService } from "../../services/auth";
import { useAuth } from "../../context/AuthContext";

export default function SignInForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [isChecked, setIsChecked] = useState(false);
  const { login } = useAuth(); // Get the login function from context
  const [isLoading, setIsLoading] = useState(false);
const navigate = useNavigate();

// Add this function to handle the API call
const handleSignIn = async (e: React.FormEvent) => {
  e.preventDefault();
  setIsLoading(true);

  const formData = new FormData(e.target as HTMLFormElement);
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  try {
    const response = await authService.signIn({ email, password });

    if (response.ok) {
      toast.success("Sign in successful!");
      login(response.data.user);
      navigate("/sources");
    } else if (response.status === 401) {
      toast.error("Invalid email or password");
    } else {
      toast.error("Something went wrong. Please try again.");
    }
  } catch (error) {
    console.error("Sign in error:", error);
    toast.error("Network error. Please check your connection.");
  } finally {
    setIsLoading(false);
  }
};

// Handle Azure AD SSO login
const handleAzureLogin = async () => {
  try {
    const response = await authService.initiateAzureLogin();

    if (response.ok && response.data.authorization_url) {
      // Extract state from authorization URL to store it locally
      const url = new URL(response.data.authorization_url);
      const state = url.searchParams.get('state');

      if (state) {
        // Store state in sessionStorage for validation after redirect
        sessionStorage.setItem('azure_oauth_state', state);
        console.log('[Azure SSO] Stored state in sessionStorage:', state);
      } else {
        console.error('[Azure SSO] No state parameter found in authorization URL');
      }

      console.log('[Azure SSO] Redirecting to:', response.data.authorization_url);
      // Redirect to Azure AD authorization URL
      window.location.href = response.data.authorization_url;
    } else {
      toast.error("Failed to initiate Azure login");
    }
  } catch (error) {
    console.error("Azure login error:", error);
    toast.error("Failed to connect to Azure. Please try again.");
  }
};
  return (
    <div className="flex flex-col flex-1">
      <div className="flex flex-col justify-center flex-1 w-full max-w-md mx-auto">
        <div>
          <div className="mb-5 sm:mb-8">
            <h1 className="mb-2 font-semibold text-gray-800 text-title-sm dark:text-white/90 sm:text-title-md">
              Sign In
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Enter your email and password to sign in!
            </p>
          </div>
          <div>
            <form onSubmit={handleSignIn} className="space-y-6">
              <div className="space-y-6">
                <div>
                  <Label>
                    Email <span className="text-error-500">*</span>{" "}
                  </Label>
                  <Input name="email" placeholder="info@gmail.com" />
                </div>
                <div>
                  <Label>
                    Password <span className="text-error-500">*</span>{" "}
                  </Label>
                  <div className="relative">
                    <Input
                      name="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter your password"
                    />
                    <span
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute z-30 -translate-y-1/2 cursor-pointer right-4 top-1/2"
                    >
                      {showPassword ? (
                        <EyeIcon className="fill-gray-500 dark:fill-gray-400 size-5" />
                      ) : (
                        <EyeCloseIcon className="fill-gray-500 dark:fill-gray-400 size-5" />
                      )}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Checkbox checked={isChecked} onChange={setIsChecked} />
                    <span className="block font-normal text-gray-700 text-theme-sm dark:text-gray-400">
                      Keep me logged in
                    </span>
                  </div>
                  <Link
                    to="/reset-password"
                    className="text-sm text-brand-500 hover:text-brand-600 dark:text-brand-400"
                  >
                    Forgot password?
                  </Link>
                </div>
                <div>
                  <Button className="w-full" size="sm" disabled={isLoading} >
                    Sign in
                  </Button>
                </div>

                {/* Divider */}
                <div className="relative flex items-center justify-center">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
                  </div>
                  <div className="relative px-3 text-sm text-gray-500 bg-white dark:bg-gray-800 dark:text-gray-400">
                    Or continue with
                  </div>
                </div>

                {/* Azure AD SSO Button */}
                <div>
                  <button
                    type="button"
                    onClick={handleAzureLogin}
                    className="flex items-center justify-center w-full gap-3 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 23 23" fill="none">
                      <path d="M0 0h10.931v10.931H0z" fill="#f25022"/>
                      <path d="M12.069 0H23v10.931H12.069z" fill="#7fba00"/>
                      <path d="M0 12.069h10.931V23H0z" fill="#00a4ef"/>
                      <path d="M12.069 12.069H23V23H12.069z" fill="#ffb900"/>
                    </svg>
                    Sign in with Microsoft
                  </button>
                </div>
              </div>
            </form>

            <div className="mt-5">
              <p className="text-sm font-normal text-center text-gray-700 dark:text-gray-400 sm:text-start">
                Don&apos;t have an account? {""}
                <Link
                  to="/signup"
                  className="text-brand-500 hover:text-brand-600 dark:text-brand-400"
                >
                  Sign Up
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
