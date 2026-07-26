import { useNavigate } from "react-router-dom";

import { CompanyForm } from "../components/companies/CompanyForm";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { useCreateCompany } from "../hooks/useCompanies";

export function AddCompanyPage() {
  const navigate = useNavigate();
  const createCompany = useCreateCompany();

  async function handleSubmit(values) {
    // Errors propagate to CompanyForm, which renders them per field.
    const company = await createCompany.mutateAsync(values);
    navigate(`/companies/${company.id}`, { replace: true });
  }

  return (
    <>
      <PageHeader
        title="Add a company"
        description="Add the company's website, then scan it for recruitment contacts."
      />
      <Card className="max-w-2xl">
        <CompanyForm
          onSubmit={handleSubmit}
          submitLabel="Add company"
          onCancel={() => navigate("/companies")}
        />
      </Card>
    </>
  );
}
