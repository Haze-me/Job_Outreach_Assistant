import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { useAuth } from "../hooks/useAuth";
import { getErrorMessage, getFieldErrors } from "../utils/errors";

const EMPTY_FORM = {
  firstName: "",
  lastName: "",
  email: "",
  password: "",
  passwordConfirm: "",
};

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState(null);
  const [isSubmitting, setSubmitting] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors({});
  }

  async function handleSubmit(event) {
    event.preventDefault();

    // Caught here so the user is told immediately rather than after a round
    // trip; the API checks it again regardless.
    if (form.password !== form.passwordConfirm) {
      setFieldErrors({ password_confirm: "Passwords do not match." });
      return;
    }

    setSubmitting(true);
    setFormError(null);
    setFieldErrors({});

    try {
      // Registration returns a token pair, so the new account lands straight
      // on the dashboard rather than back at the login form.
      await register(form);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setFormError(getErrorMessage(error));
      setFieldErrors(getFieldErrors(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <h2 className="mb-1 text-lg font-semibold text-slate-900">Create your account</h2>
      <p className="mb-6 text-sm text-slate-500">Free, and takes a moment.</p>

      {formError && (
        <Alert variant="error" className="mb-5">
          {formError}
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="First name"
            name="firstName"
            autoComplete="given-name"
            value={form.firstName}
            onChange={handleChange}
            error={fieldErrors.first_name}
          />
          <Input
            label="Last name"
            name="lastName"
            autoComplete="family-name"
            value={form.lastName}
            onChange={handleChange}
            error={fieldErrors.last_name}
          />
        </div>

        <Input
          label="Email address"
          name="email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={handleChange}
          error={fieldErrors.email}
          required
        />

        <Input
          label="Password"
          name="password"
          type="password"
          autoComplete="new-password"
          value={form.password}
          onChange={handleChange}
          error={fieldErrors.password}
          hint="At least 8 characters, and not a common password."
          required
        />

        <Input
          label="Confirm password"
          name="passwordConfirm"
          type="password"
          autoComplete="new-password"
          value={form.passwordConfirm}
          onChange={handleChange}
          error={fieldErrors.password_confirm}
          required
        />

        <Button type="submit" isLoading={isSubmitting} className="w-full" size="lg">
          {isSubmitting ? "Creating account..." : "Create account"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500">
        Already registered?{" "}
        <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
          Sign in
        </Link>
      </p>
    </>
  );
}
