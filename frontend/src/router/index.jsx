import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../layouts/AppLayout";
import { AuthLayout } from "../layouts/AuthLayout";
import { AddCompanyPage } from "../pages/AddCompanyPage";
import { ApplicationsPage } from "../pages/ApplicationsPage";
import { CompaniesPage } from "../pages/CompaniesPage";
import { CompanyDetailPage } from "../pages/CompanyDetailPage";
import { ContactsPage } from "../pages/ContactsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { LoginPage } from "../pages/LoginPage";
import { NotesPage } from "../pages/NotesPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { ProfilePage } from "../pages/ProfilePage";
import { RegisterPage } from "../pages/RegisterPage";
import { ScanProgressPage } from "../pages/ScanProgressPage";
import { SettingsPage } from "../pages/SettingsPage";
import { ProtectedRoute } from "./ProtectedRoute";
import { PublicOnlyRoute } from "./PublicOnlyRoute";
import { RouteErrorBoundary } from "./RouteErrorBoundary";

/**
 * The route table.
 *
 * Two guarded groups: `PublicOnlyRoute` wraps the signed-out pages,
 * `ProtectedRoute` wraps everything that needs a session.
 *
 * `/companies/new` is declared before `/companies/:companyId` so "new" is not
 * swallowed as a company id.
 */
export const router = createBrowserRouter([
  {
    path: "/",
    errorElement: <RouteErrorBoundary />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },

      {
        element: <PublicOnlyRoute />,
        children: [
          {
            element: <AuthLayout />,
            children: [
              { path: "login", element: <LoginPage /> },
              { path: "register", element: <RegisterPage /> },
            ],
          },
        ],
      },

      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { path: "dashboard", element: <DashboardPage /> },

              { path: "companies", element: <CompaniesPage /> },
              { path: "companies/new", element: <AddCompanyPage /> },
              { path: "companies/:companyId", element: <CompanyDetailPage /> },

              { path: "scans/:scanId", element: <ScanProgressPage /> },

              { path: "contacts", element: <ContactsPage /> },
              { path: "applications", element: <ApplicationsPage /> },
              { path: "notes", element: <NotesPage /> },

              { path: "profile", element: <ProfilePage /> },
              { path: "settings", element: <SettingsPage /> },
            ],
          },
        ],
      },

      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
