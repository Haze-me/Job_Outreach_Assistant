import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { Card, CardHeader } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { PageHeader } from "../components/ui/PageHeader";
import { useAuth } from "../hooks/useAuth";
import * as authService from "../services/authService";
import { getErrorMessage, getFieldErrors } from "../utils/errors";

/**
 * Who the user is. Account security lives on the Settings page, so the
 * password form is not duplicated here.
 */
export function ProfilePage() {
  const { user, applyUserUpdate } = useAuth();

  const [form, setForm] = useState({ firstName: "", lastName: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [status, setStatus] = useState(null);
  const [isSaving, setSaving] = useState(false);

  // The user arrives asynchronously on a page reload, so the form seeds itself
  // once it is available rather than being initialised empty and left stale.
  useEffect(() => {
    setForm({ firstName: user?.first_name ?? "", lastName: user?.last_name ?? "" });
  }, [user?.first_name, user?.last_name]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setStatus(null);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setStatus(null);
    setFieldErrors({});

    try {
      const updated = await authService.updateProfile(form);
      applyUserUpdate(updated);
      setStatus({ variant: "success", message: "Profile updated." });
    } catch (error) {
      setStatus({ variant: "error", message: getErrorMessage(error) });
      setFieldErrors(getFieldErrors(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader title="Profile" description="How your name appears in the app." />

      <Card className="max-w-xl">
        <CardHeader title="Details" />

        {status && (
          <Alert variant={status.variant} className="mb-5">
            {status.message}
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <Input
            label="Email address"
            value={user?.email ?? ""}
            disabled
            readOnly
            hint="Your email is your sign-in identifier and cannot be changed here."
          />
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

          <Button type="submit" isLoading={isSaving}>
            Save changes
          </Button>
        </form>

        <p className="mt-6 border-t border-slate-100 pt-5 text-sm text-slate-500">
          To change your password, go to{" "}
          <Link to="/settings" className="font-medium text-brand-700 hover:text-brand-800">
            Settings
          </Link>
          .
        </p>
      </Card>
    </>
  );
}
