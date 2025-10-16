import PageMeta from "../../components/common/PageMeta";
import AuthLayout from "./AuthPageLayout";
import SignUpForm from "../../components/auth/SignUpForm";

export default function SignUp() {
  return (
    <>
      <PageMeta
        title="MCP Admin UI SignUp Dashboard | MCP Admin UI : LLM-Powered OBM ABC Analysis Tool"
        description="This is MCP Admin UI SignUp Tables Dashboard page for MCP Admin UI - LLM-Powered OBM ABC Analysis Tool"
      />
      <AuthLayout>
        <SignUpForm />
      </AuthLayout>
    </>
  );
}
