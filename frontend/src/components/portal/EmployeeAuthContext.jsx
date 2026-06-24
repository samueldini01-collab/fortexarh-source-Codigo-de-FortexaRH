import { useState, useEffect, createContext, useContext, useCallback } from "react";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

const EmployeeAuthContext = createContext(null);

export function useEmployeeAuth() {
  const context = useContext(EmployeeAuthContext);
  if (!context) throw new Error("useEmployeeAuth must be used within EmployeeAuthProvider");
  return context;
}

export function EmployeeAuthProvider({ children }) {
  const [employee, setEmployee] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("employee_portal_token"));
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem("employee_portal_token");
    setToken(null);
    setEmployee(null);
  }, []);

  const fetchProfile = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/employee-portal/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const emp = response.data.employee || {};
      // Normalize the flag name to a single canonical key on the client
      emp.must_change_password = Boolean(
        emp.must_change_password ?? emp.portal_must_change_password ?? false
      );
      setEmployee(emp);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  }, [token, logout]);

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, [token, fetchProfile]);

  const login = async (documentNumber, password) => {
    const response = await axios.post(`${API}/employee-portal/login`, {
      document_number: documentNumber,
      password: password
    });
    localStorage.setItem("employee_portal_token", response.data.token);
    setToken(response.data.token);
    const emp = response.data.employee || {};
    emp.must_change_password = Boolean(emp.must_change_password ?? false);
    setEmployee(emp);
    return response.data;
  };

  const refreshProfile = useCallback(async () => {
    if (!token) return;
    await fetchProfile();
  }, [token, fetchProfile]);

  const getAuthHeaders = () => ({ Authorization: `Bearer ${token}` });

  return (
    <EmployeeAuthContext.Provider
      value={{ employee, token, login, logout, loading, getAuthHeaders, refreshProfile }}
    >
      {children}
    </EmployeeAuthContext.Provider>
  );
}
