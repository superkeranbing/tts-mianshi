import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register, login } from "../services/api";
import { useAppStore } from "../stores/appStore";
import { Loader2, LogIn } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isReg, setIsReg] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAppStore();
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fn = isReg ? register : login;
      const { access_token, user } = await fn(username, password);
      setAuth(user, access_token);
      localStorage.setItem("tts-auth", JSON.stringify({ user, token: access_token }));
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="bg-gray-900 rounded-lg p-8 w-full max-w-md border border-gray-800">
        <h2 className="text-2xl font-bold text-center mb-6 text-emerald-400">{isReg ? "注册" : "登录"} 听记面试</h2>
        {error && <div className="bg-red-900/50 text-red-300 px-4 py-2 rounded mb-4 text-sm">{error}</div>}
        <form onSubmit={submit}>
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="用户名" className="w-full px-4 py-2 mb-3 bg-gray-800 rounded border border-gray-700 focus:border-emerald-500 outline-none text-white" />
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="密码" className="w-full px-4 py-2 mb-4 bg-gray-800 rounded border border-gray-700 focus:border-emerald-500 outline-none text-white" />
          <button type="submit" disabled={loading} className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-white font-medium transition-colors flex items-center justify-center gap-2">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> 处理中...</> : <><LogIn className="w-4 h-4" /> {isReg ? "注册" : "登录"}</>}
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-500">
          <button onClick={() => { setIsReg(!isReg); setError(""); }} className="hover:text-emerald-400 transition-colors">
            {isReg ? "已有账号？登录" : "没有账号？注册"}
          </button>
        </p>
      </div>
    </div>
  );
}
