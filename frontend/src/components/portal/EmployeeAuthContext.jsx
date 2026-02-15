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

  const fetchProfile = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/employee-portal/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmployee(response.data.employee);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  }, [token]);

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
    setEmployee(response.data.employee);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem("employee_portal_token");
    setToken(null);
    setEmployee(null);
  };

  const getAuthHeaders = () => ({ Authorization: `Bearer ${token}` });

  return (
    <EmployeeAuthContext.Provider value={{ employee, token, login, logout, loading, getAuthHeaders }}>
      {children}
    </EmployeeAuthContext.Provider>
  );
}
