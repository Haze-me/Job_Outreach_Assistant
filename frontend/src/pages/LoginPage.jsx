import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { useAuth } from "../hooks/useAuth";
import { getErrorMessage, getFieldErrors } from "../utils/errors";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [form, setForm] = useState({ email: "", password: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [isSubmitting, setSubmitting] = useState(false);

  // Where the user was headed before the guard redirected them here.
  const redirectTo = location.state?.from?.pathname ?? "/dashboard";

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: undefined }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    setFieldErrors({});

    try {
      await login(form);
      navigate(redirectTo, { replace: true });
    } catch (error) {
      // The API returns identical responses for a wrong password and an
      // unknown email, so the message stays deliberately non-specific.
      setFormError(getErrorMessage(error));
      setFieldErrors(getFieldErrors(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <h2 className="mb-1 text-lg font-semibold text-slate-900">Sign in</h2>
      <p className="mb-6 text-sm text-slate-500">Welcome back.</p>

      {formError && (
        <Alert variant="error" className="mb-5">
          {formError}
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input
          label="Email address"
          name="email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={handleChange}
          error={fieldErrors.email}
          required
          autoFocus
        />

        <Input
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={form.password}
          onChange={handleChange}
          error={fieldErrors.password}
          required
        />

        <Button type="submit" isLoading={isSubmitting} className="w-full" size="lg">
          {isSubmitting ? "Signing in..." : "Sign in"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500">
        No account yet?{" "}
        <Link to="/register" className="font-medium text-brand-600 hover:text-brand-700">
          Create one
        </Link>
      </p>
    </>
  );
}
