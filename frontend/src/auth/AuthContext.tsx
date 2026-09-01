import { createContext, useContext, useState, type ReactNode } from "react";
import { TOKEN_KEY } from "../api/client";
import { login as loginRequest } from "../api/endpoints";

interface AuthContextValue {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem(TOKEN_KEY));

  async function login(email: string, password: string) {
    const token = await loginRequest(email, password);
    localStorage.setItem(TOKEN_KEY, token);
    setIsAuthenticated(true);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setIsAuthenticated(false);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
