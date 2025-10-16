import PageMeta from "../../components/common/PageMeta";
import AuthLayout from "./AuthPageLayout";
import SignInForm from "../../components/auth/SignInForm";

export default function SignIn() {
  return (
    <>
      <PageMeta
        title="MCP Admin UI SignIn Dashboard | MCP Admin UI : LLM-Powered OBM ABC Analysis Tool"
        description="This is MCP Admin UI SignIn Tables Dashboard page for MCP Admin UI - LLM-Powered OBM ABC Analysis Tool"
      />
      <AuthLayout>
        <SignInForm />
      </AuthLayout>
    </>
  );
}
